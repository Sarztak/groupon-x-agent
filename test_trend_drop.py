import json
import logging
from pathlib import Path
from retrieval import retrieve_deal
from marketing_copy import build_agent_input, generate_and_review
from guardrails import guard_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

CATALOG_PATH   = Path("./deals_catalog.json").resolve()
TRENDS_PATH    = Path("./simulated_trends.json").resolve()
REFERENCES_DIR = Path("./prompts/references").resolve()
PROMPTS_DIR    = Path("./prompts").resolve()

trends = json.loads(TRENDS_PATH.read_text())

CASES = [{"label": t["name"].lower().replace("#", ""), "trend": t} for t in trends]

if __name__ == "__main__":
    import sys
    filter_label = sys.argv[1].lower() if len(sys.argv) > 1 else None
    cases_to_run = [c for c in CASES if filter_label in c["label"]] if filter_label else CASES[:3]

    for case in cases_to_run:
        trend = case["trend"]
        print(f"\n{'='*60}")
        print(f"TREND: {trend['name']} ({trend.get('tweet_volume', '?')} tweets)")
        print("-" * 60)

        deal = retrieve_deal(
            trigger_type="trend",
            trigger_text=trend["name"],
            catalog_path=CATALOG_PATH,
            prompts_dir=PROMPTS_DIR,
            model="claude-sonnet-4-6",
        )
        if not deal:
            log.info("No matching deal — no_match")
            continue

        log.info("Matched: %s — %s", deal.get("merchant_name"), deal.get("deal_title"))

        agent_input = build_agent_input(deal, segment="spontaneous_locals", variations=1)
        result = generate_and_review(agent_input, REFERENCES_DIR, model="claude-sonnet-4-6", max_attempts=2)

        if not result["results"]:
            log.error("FAIL — generation returned nothing")
            continue

        copy = result["results"][0]["copy"]
        deal_info = agent_input["deal"]

        output_check = guard_output(json.dumps({"draft": copy, "deal_info": deal_info}))
        if not output_check or output_check["action"] != "publish":
            log.error("FAIL — output guard blocked: %s", output_check.get("reason") if output_check else "None")
            continue

        log.info("PASS | status=%s | copy: %s", result["status"], copy)
