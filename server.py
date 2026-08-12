import asyncio
import json
import logging
import random
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from guardrails import guard_output
from marketing_copy import build_agent_input, generate_and_review
from metrics import log_post, summarize
from retrieval import retrieve_deal
from router import handle_mention
from url_utils import enrich_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

CATALOG_PATH      = Path("./deals_catalog.json").resolve()
TRENDS_PATH       = Path("./simulated_trends.json").resolve()
MENTIONS_PATH     = Path("./simulated_mentions.json").resolve()
DEAL_DROP_CACHE   = Path("./deal_drop_cache.json").resolve()
PROMPTS_DIR       = Path("./prompts").resolve()
REFERENCES_DIR    = Path("./prompts/references").resolve()


class MentionRequest(BaseModel):
    message: str
    username: str

class TrendRequest(BaseModel):
    trend: str

class CustomDealRequest(BaseModel):
    url: str

class KillSwitchRequest(BaseModel):
    active: bool


TWO_WEEK_DIR    = Path("./two_week_plan").resolve()


KILL_SWITCH_PATH = Path("./KILL_SWITCH").resolve()


@app.get("/api/kill_switch")
async def get_kill_switch():
    return {"active": KILL_SWITCH_PATH.exists()}


@app.post("/api/kill_switch")
async def set_kill_switch(req: KillSwitchRequest):
    if req.active:
        KILL_SWITCH_PATH.touch()
    else:
        KILL_SWITCH_PATH.unlink(missing_ok=True)
    return {"active": KILL_SWITCH_PATH.exists()}


@app.get("/api/metrics")
async def metrics():
    return summarize()


@app.get("/api/random_mention")
async def random_mention():
    mentions = json.loads(MENTIONS_PATH.read_text(encoding="utf-8"))
    mention = random.choice(mentions)
    return {"username": mention["username"], "text": mention["text"]}


@app.get("/api/two_week_plan")
async def two_week_plan():
    posts_path   = TWO_WEEK_DIR / "posts.json"
    replies_path = TWO_WEEK_DIR / "replies.json"
    if not posts_path.exists() or not replies_path.exists():
        return {"generated": False, "posts": [], "replies": []}
    posts   = json.loads(posts_path.read_text(encoding="utf-8"))
    replies = json.loads(replies_path.read_text(encoding="utf-8"))
    for post in posts:
        if post.get("status") != "ok" or not post.get("copy"):
            continue
        deal = post.get("deal") if post.get("type") == "deal_drop" else post.get("matched_deal")
        raw_url = (deal or {}).get("url")
        if raw_url:
            utm = "deal_drop" if post.get("type") == "deal_drop" else "trend_hook"
            post["deal_url"] = enrich_url(raw_url, utm)
            post["copy"] = f"{post['copy']} {post['deal_url']}"
    return {"generated": True, "posts": posts, "replies": replies}


SCRAPER_SCRIPT = Path("./scrape_single_deal.js").resolve()


@app.post("/api/custom_deal_drop")
async def custom_deal_drop(req: CustomDealRequest):
    from urllib.parse import urlparse
    parsed = urlparse(req.url)
    if parsed.hostname not in ("www.groupon.com", "groupon.com") or not parsed.path.startswith("/deals/"):
        raise HTTPException(status_code=400, detail="URL must be a groupon.com/deals/ link")

    log.info("Custom deal drop: scraping %s", req.url)
    try:
        proc = await asyncio.create_subprocess_exec(
            "node", str(SCRAPER_SCRIPT), req.url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Scraping timed out")

    if proc.returncode != 0:
        stderr_text = stderr.decode(errors="replace")
        log.error("Scraper failed (exit %d): %s", proc.returncode, stderr_text[-500:])
        raise HTTPException(status_code=502, detail=f"Scraping failed: {stderr_text[-200:]}")

    stdout_text = stdout.decode(errors="replace")
    try:
        deal = json.loads(stdout_text)
    except json.JSONDecodeError:
        log.error("Scraper output not valid JSON: %s", stdout_text[:200])
        raise HTTPException(status_code=502, detail="Scraper returned invalid JSON")

    log.info("Scraped: %s", deal.get("deal_title"))
    result = _copy_from_cache_or_generate(deal, utm_content="deal_drop")
    log_post(post_type="deal_drop", route="custom_deal_drop", copy=result["copy"])
    return {"status": "posted", "copy": result["copy"], "deal": result["deal"]}


@app.post("/api/mention")
async def mention(req: MentionRequest):
    result = handle_mention(
        req.message,
        req.username,
        CATALOG_PATH,
        PROMPTS_DIR,
        REFERENCES_DIR,
    )
    return result


@app.post("/api/deal_drop")
async def deal_drop():
    deals = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    deal = random.choice(deals[:10])
    log.info("Deal drop: selected %s", deal.get("deal_title"))
    result = _copy_from_cache_or_generate(deal)
    log_post(post_type="deal_drop", route="deal_drop", copy=result["copy"])
    return {"status": "posted", "copy": result["copy"], "deal": result["deal"]}


def _copy_from_cache_or_generate(deal: dict, utm_content: str = "deal_drop") -> dict:
    deal_title = deal.get("deal_title")
    cache = json.loads(DEAL_DROP_CACHE.read_text(encoding="utf-8")) if DEAL_DROP_CACHE.exists() else []
    cached = next((e for e in cache if e["deal"].get("deal_title") == deal_title), None)

    if cached:
        log.info("Cache hit — serving existing copy for %s", deal_title)
        copy = cached["copy"]
        deal_info = cached["deal"]
    else:
        log.info("Cache miss — generating copy for %s", deal_title)
        agent_input = build_agent_input(deal, segment="spontaneous_locals", variations=1)
        result = generate_and_review(agent_input, REFERENCES_DIR, model="claude-sonnet-4-6", max_attempts=2)
        if not result["results"]:
            raise HTTPException(status_code=500, detail="Copy generation returned nothing")

        copy = result["results"][0]["copy"]
        deal_info = agent_input["deal"]

        output_check = guard_output(json.dumps({"draft": copy, "deal_info": deal_info}))
        if not output_check or output_check["action"] == "block":
            raise HTTPException(status_code=500, detail="Output guard blocked copy")

        cache.append({"deal": deal_info, "copy": copy})
        DEAL_DROP_CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        log.info("Cached copy for %s", deal_title)

    raw_url = deal.get("url")
    if raw_url:
        deal_url = enrich_url(raw_url, utm_content)
        copy = f"{copy} {deal_url}"

    return {"copy": copy, "deal": deal_info}


@app.post("/api/trend")
async def trend_hook(req: TrendRequest):
    log.info("Trend hook: %s", req.trend)
    deal = retrieve_deal(
        trigger_type="trend",
        trigger_text=req.trend,
        catalog_path=CATALOG_PATH,
        prompts_dir=PROMPTS_DIR,
    )
    if not deal:
        log.info("No matching deal for trend: %s", req.trend)
        return {"status": "no_match"}

    result = _copy_from_cache_or_generate(deal, utm_content="trend_hook")
    return {"status": "posted", "copy": result["copy"], "deal": result["deal"]}


@app.post("/api/trend_drop")
async def trend_drop():
    trends = json.loads(TRENDS_PATH.read_text(encoding='utf-8'))
    trend = random.choice(trends)
    trend_name = trend.get("name")
    log.info("Trend drop: selected %s (%s tweets)", trend_name, trend.get("tweet_volume"))

    deal = retrieve_deal(
        trigger_type="trend",
        trigger_text=trend_name,
        catalog_path=CATALOG_PATH,
        prompts_dir=PROMPTS_DIR,
        model="claude-sonnet-4-6",
    )
    if not deal:
        log.info("No matching deal for trend: %s", trend_name)
        return {"status": "no_match", "trend": trend_name}

    result = _copy_from_cache_or_generate(deal, utm_content="trend_hook")
    log_post(post_type="trend_hook", route="trend_hook", copy=result["copy"])
    return {"status": "posted", "copy": result["copy"], "deal": result["deal"], "trend": trend_name}
