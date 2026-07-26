import datetime
import json
import logging
from marketing_copy import generate_and_review, build_agent_input
from guardrails import guard_input, guard_output, is_killed
from retrieval import retrieve_deal
from orchestrator import orchestrate
from conversational import generate_conversational_reply
from metrics import log_post
from url_utils import enrich_url

log = logging.getLogger(__name__)

GROUPON_HELP_LINK = "https://www.groupon.com/articles/about"
GROUPON_HOME_LINK = "https://www.groupon.com/"

FIXED_REPLIES = {
    "blocked_reply": f"Not something I can help with, but if you're looking for something to do — check out today's local deals on Groupon. {GROUPON_HOME_LINK}",
    "off_topic": f"For how Groupon works, check out {GROUPON_HELP_LINK} — or if you're just looking for something to do, see what's near you at {GROUPON_HOME_LINK}",
    "sensitive_block": "That's not something we're able to weigh in on.",
}


def handle_mention(message: str, username: str, catalog_path, prompts_dir, references_dir) -> dict:
    log.info("Handling mention from @%s: %s", username, message)

    if is_killed():
        log.warning("Kill switch active — pausing")
        return {"status": "paused", "reason": "Kill switch active"}

    guard_report = guard_input(message)
    if not guard_report:
        log.error("Input guard failed for @%s — escalating", username)
        queue_for_human_review(message, username, {}, {})
        return {"status": "escalated", "reason": "Input guard failed", "guard_report": {}}
    log.info("Guard report: hard_block=%s flags=%s", guard_report.get("hard_block"), guard_report.get("flags"))

    if guard_report.get("hard_block"):
        if guard_report.get("flags", {}).get("sensitive_news"):
            log.info("Hard block + sensitive_news — sending sensitive_block")
            return {"status": "posted", "reply": FIXED_REPLIES["sensitive_block"], "route": "sensitive_block", "guard_report": guard_report}
        log.info("Hard block — skipping orchestrator, sending blocked_reply")
        return {"status": "posted", "reply": FIXED_REPLIES["blocked_reply"], "route": "blocked_reply", "guard_report": guard_report}

    decision = orchestrate(message, username, guard_report)
    if not decision:
        log.error("Orchestrator returned None — escalating")
        queue_for_human_review(message, username, guard_report, {})
        return {"status": "escalated", "reason": "Orchestrator failed", "guard_report": guard_report}

    route = decision["route"]
    log.info("Route: %s | engage_with: %s", route, decision.get("engage_with"))
    deal_info = None    # set for deal_request, passed to output guard as verified source
    deal_raw_url = None # set for deal_request, appended after output guard passes

    if route in ("blocked_reply", "off_topic"):
        reply_text = FIXED_REPLIES[route]
        log.info("Fixed reply for route %s — skipping output guard", route)
        log_post(post_type="mention_reply", route=route, copy=reply_text)
        return {"status": "posted", "reply": reply_text, "route": route, "guard_report": guard_report}

    elif route == "deal_request":
        deal = retrieve_deal(
            trigger_type="mention",
            trigger_text=decision["engage_with"],
            catalog_path=catalog_path,
            prompts_dir=prompts_dir
        )
        if not deal:
            queue_for_human_review(message, username, guard_report, decision)
            return {"status": "escalated", "reason": "No confident deal match found", "guard_report": guard_report}

        deal_raw_url = deal.get("url")
        agent_input = build_agent_input(deal, segment="spontaneous_locals", variations=1)
        deal_info = agent_input["deal"]
        result = generate_and_review(agent_input, references_dir, model="claude-sonnet-4-6")

        if result["status"] != "pass":
            queue_for_human_review(message, username, guard_report, decision)
            return {"status": "escalated", "reason": "Deal copy failed review", "guard_report": guard_report}

        deal_copy = result["results"][0]["copy"]
        conv_params = dict(mode="deal_reply", mention_text=decision["engage_with"], username=username, deal_copy=deal_copy)

    elif route == "acknowledge":
        conv_params = dict(mode="acknowledge", mention_text=message, username=username)
        queue_for_human_review(message, username, guard_report, decision)

    elif route == "positive_response":
        conv_params = dict(mode="positive_response", mention_text=message, username=username)

    else:
        queue_for_human_review(message, username, guard_report, decision)
        return {"status": "escalated", "reason": f"Unrecognized route: {route}", "guard_report": guard_report}

    reply = generate_conversational_reply(**conv_params)
    if not reply:
        log.error("Conversational agent returned None — escalating")
        queue_for_human_review(message, username, guard_report, decision)
        return {"status": "escalated", "reason": "Conversational agent failed", "guard_report": guard_report}
    reply_text = reply["reply"]

    guard_payload = json.dumps({"draft": reply_text, "deal_info": deal_info})
    output_check = guard_output(guard_payload)
    if not output_check:
        log.error("Output guard failed — escalating")
        queue_for_human_review(message, username, guard_report, decision)
        return {"status": "escalated", "reason": "Output guard failed", "guard_report": guard_report}
    log.info("Output guard action: %s", output_check.get("action"))
    if output_check["action"] != "publish":
        log.warning("Output guard blocked reply — escalating")
        queue_for_human_review(message, username, guard_report, decision)
        return {"status": "escalated", "reason": "Output guard blocked reply", "guard_report": guard_report}

    deal_url = None
    if route == "deal_request" and deal_raw_url:
        deal_url = enrich_url(deal_raw_url, "mention_reply")
        reply_text = f"{reply_text} {deal_url}"

    log.info("Reply posted for @%s: %s", username, reply_text)
    log_post(post_type="mention_reply", route=route, copy=reply_text)
    result = {"status": "posted", "reply": reply_text, "route": route, "guard_report": guard_report}
    if deal_url:
        result["deal_url"] = deal_url
    return result


def queue_for_human_review(message, username, guard_report, decision):
    with open("human_review_queue.jsonl", "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "message": message,
            "username": username,
            "guard_report": guard_report,
            "decision": decision
        }) + "\n")
