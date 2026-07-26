"""
Offline generation script for the 2-week demo content plan.
Reads two_week_plan/plan_skeleton.json, runs the pipeline for each item,
saves results incrementally to two_week_plan/posts.json and two_week_plan/replies.json.
Re-runnable: already-completed items are skipped.
"""
import json
import logging
import sys
import time
from pathlib import Path

from marketing_copy import build_agent_input, generate_and_review
from guardrails import guard_output
from retrieval import retrieve_deal
from router import handle_mention

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

CATALOG_PATH    = Path("./deals_catalog.json").resolve()
PROMPTS_DIR     = Path("./prompts").resolve()
REFERENCES_DIR  = Path("./prompts/references").resolve()
PLAN_DIR        = Path("./two_week_plan")
SKELETON_PATH   = PLAN_DIR / "plan_skeleton.json"
POSTS_PATH      = PLAN_DIR / "posts.json"
REPLIES_PATH    = PLAN_DIR / "replies.json"

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries


def load_existing(path: Path) -> dict:
    if path.exists():
        return {item["id"]: item for item in json.loads(path.read_text())}
    return {}


def save_all(path: Path, items: dict):
    path.write_text(json.dumps(list(items.values()), indent=2))


def generate_deal_drop_copy(deal: dict) -> str | None:
    agent_input = build_agent_input(deal, segment="spontaneous_locals", variations=1)
    result = generate_and_review(
        agent_input, REFERENCES_DIR, model="claude-sonnet-4-6", max_attempts=2
    )
    if not result["results"]:
        return None
    copy = result["results"][0]["copy"]
    check = guard_output(json.dumps({"draft": copy, "deal_info": agent_input["deal"]}))
    if not check or check.get("action") == "block":
        log.warning("Output guard hard-blocked copy for %s", deal.get("merchant_name"))
        return None
    if check.get("action") == "route_to_human":
        log.warning("Output guard escalating %s — reason: %s", deal.get("merchant_name"), check.get("reason"))
        return None
    return copy


def generate_trend_copy(trend: str) -> tuple[dict | None, str | None]:
    deal = retrieve_deal(
        trigger_type="trend",
        trigger_text=trend,
        catalog_path=CATALOG_PATH,
        prompts_dir=PROMPTS_DIR,
        model="claude-sonnet-4-6",
    )
    if not deal:
        return None, None
    copy = generate_deal_drop_copy(deal)
    return deal, copy


def run_with_retry(fn, label: str):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = fn()
            if result is not None:
                return result
            log.warning("%s attempt %d returned None", label, attempt)
        except Exception as e:
            log.warning("%s attempt %d failed: %s", label, attempt, e)
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    log.error("%s failed after %d attempts", label, MAX_RETRIES)
    return None


def process_posts(skeleton_posts: list):
    existing = load_existing(POSTS_PATH)
    for post in skeleton_posts:
        pid = post["id"]
        if pid in existing and existing[pid].get("status") == "ok":
            log.info("Skip %s — already generated", pid)
            continue

        log.info("Generating %s  %s  %s", pid, post["date"], post["type"])

        if post["type"] == "deal_drop":
            copy = run_with_retry(
                lambda d=post["deal"]: generate_deal_drop_copy(d),
                pid,
            )
            if copy:
                existing[pid] = {**post, "copy": copy, "status": "ok"}
            else:
                existing[pid] = {**post, "copy": None, "status": "failed"}

        elif post["type"] == "trend_hook":
            def gen_trend(t=post["trend"]):
                d, c = generate_trend_copy(t)
                return (d, c) if d and c else None

            result = run_with_retry(gen_trend, pid)
            if result:
                deal, copy = result
                existing[pid] = {**post, "matched_deal": deal, "copy": copy, "status": "ok"}
            else:
                existing[pid] = {**post, "matched_deal": None, "copy": None, "status": "failed"}

        save_all(POSTS_PATH, existing)
        log.info("Saved %s  status=%s", pid, existing[pid]["status"])


def process_replies(skeleton_replies: list):
    existing = load_existing(REPLIES_PATH)
    for reply in skeleton_replies:
        rid = reply["id"]
        if rid in existing and existing[rid].get("status") == "ok":
            log.info("Skip %s — already generated", rid)
            continue

        log.info("Generating reply %s  @%s", rid, reply["username"])

        def gen_reply(text=reply["text"], user=reply["username"]):
            return handle_mention(text, user, CATALOG_PATH, PROMPTS_DIR, REFERENCES_DIR)

        result = run_with_retry(gen_reply, rid)
        if result and result.get("status") in ("posted", "escalated"):
            entry = {
                **reply,
                "route": result.get("route", reply["route_hint"]),
                "reply": result.get("reply", ""),
                "guard_report": result.get("guard_report", {}),
                "status": "ok",
            }
            if result.get("deal_url"):
                entry["deal_url"] = result["deal_url"]
            existing[rid] = entry
        else:
            existing[rid] = {**reply, "route": reply["route_hint"], "reply": None, "status": "failed"}

        save_all(REPLIES_PATH, existing)
        log.info("Saved %s  status=%s", rid, existing[rid]["status"])


def main():
    skeleton = json.loads(SKELETON_PATH.read_text())
    log.info("Loaded skeleton: %d posts, %d replies", len(skeleton["posts"]), len(skeleton["replies"]))

    process_posts(skeleton["posts"])
    process_replies(skeleton["replies"])

    posts = load_existing(POSTS_PATH)
    replies = load_existing(REPLIES_PATH)
    ok_posts = sum(1 for p in posts.values() if p["status"] == "ok")
    ok_replies = sum(1 for r in replies.values() if r["status"] == "ok")
    log.info("Done. Posts: %d/%d ok. Replies: %d/%d ok.", ok_posts, len(posts), ok_replies, len(replies))
    if ok_posts < len(posts) or ok_replies < len(replies):
        sys.exit(1)


if __name__ == "__main__":
    main()
