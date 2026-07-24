import json
import logging
from guardrails import guard_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

DEAL_INFO = {
    "deal_title": "Base Rock Room: Up to 32% Off at King Spa Chicago",
    "merchant_name": "King Spa Chicago",
    "location": "Chicago, IL",
    "city": "chicago",
    "merchant_info": "Full-service Korean spa with heated pools, saunas, and body scrubs.",
    "reviews": ["Best spa experience in the city.", "Loved the sauna rooms."]
}

CASES = [
    {
        "name": "acknowledge_complaint",
        "draft": "@angry_user Heard you — someone on our team is looking into this right now.",
        "deal_info": None,
        "expected_action": "publish",
    },
    {
        "name": "deal_reply_verified_price",
        "draft": "@sarah_chicago Only three Base Rock Rooms exist on earth — Chicago has one. Worth a visit this weekend, and it's up to 32% off on Groupon right now.",
        "deal_info": DEAL_INFO,
        "expected_action": "publish",
    },
    {
        "name": "competitor_mention",
        "draft": "Better deals than LivingSocial — check Groupon today.",
        "deal_info": None,
        "expected_action": "block",
    },
    {
        "name": "profanity",
        "draft": "Holy sh*t these deals are insane — grab one now!",
        "deal_info": None,
        "expected_action": "block",
    },
    {
        "name": "unverified_price_no_deal_info",
        "draft": "Get 50% off your next spa visit on Groupon.",
        "deal_info": None,
        "expected_action": "block",
    },
    {
        "name": "positive_reply_no_deal",
        "draft": "that post-spa feeling is its own category. Glad that one landed well.",
        "deal_info": None,
        "expected_action": "publish",
    },
]

if __name__ == "__main__":
    passed = 0
    failed = 0
    for case in CASES:
        payload = json.dumps({"draft": case["draft"], "deal_info": case["deal_info"]})
        result = guard_output(payload)
        action = result.get("action") if result else "ERROR"
        flags = result.get("flags", {}) if result else {}
        reason = result.get("reason", "") if result else "null returned"
        ok = action == case["expected_action"]
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        log.info(
            "[%s] %s | action=%s (expected=%s) | reason: %s",
            status, case["name"], action, case["expected_action"], reason
        )
        if not ok or any(flags.values()):
            log.info("  flags: %s", {k: v for k, v in flags.items() if v})

    log.info("Results: %d/%d passed", passed, passed + failed)
