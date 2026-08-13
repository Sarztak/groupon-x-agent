import json
import logging
from pathlib import Path

from guardrails import guard_output
from marketing_copy import build_agent_input, generate_and_review

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

CATALOG_PATH   = Path("./deals_catalog.json").resolve()
REFERENCES_DIR = Path("./prompts/references").resolve()

deals = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))

CASES = [
    {"label": f"deal_{i}", "deal": deals[i]}
    for i in range(min(10, len(deals)))
]

if __name__ == "__main__":
    import sys
    filter_label = sys.argv[1].lower() if len(sys.argv) > 1 else None
    cases_to_run = [c for c in CASES if filter_label in c["label"].lower()] if filter_label else CASES

    passed = 0
    failed = 0
    for case in cases_to_run:
        deal = case["deal"]
        print(f"\n{'='*60}")
        print(f"CASE: {case['label'].upper()}")
        print(f"Deal: {deal.get('merchant_name')} — {deal.get('deal_title')}")
        print("-" * 60)

        agent_input = build_agent_input(deal, segment="spontaneous_locals", variations=1)
        result = generate_and_review(agent_input, REFERENCES_DIR, model="claude-sonnet-4-6", max_attempts=2)

        if result["status"] != "pass":
            log.error("FAIL — copy did not pass review after max attempts")
            log.error("Last results: %s", json.dumps(result["results"], indent=2))
            failed += 1
            continue

        copy = result["results"][0]["copy"]
        deal_info = agent_input["deal"]

        output_check = guard_output(json.dumps({"draft": copy, "deal_info": deal_info}))
        if not output_check:
            log.error("FAIL — output guard returned None")
            failed += 1
            continue

        if output_check["action"] != "publish":
            log.error("FAIL — output guard blocked: %s | flags: %s", output_check.get("reason"), {k: v for k, v in output_check.get("flags", {}).items() if v})
            failed += 1
            continue

        log.info("PASS | copy: %s", copy)
        passed += 1

    print(f"\nResults: {passed}/{passed + failed} passed")
