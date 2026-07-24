import json
import logging
import datetime
from marketing_copy import call_model

log = logging.getLogger(__name__)

COMPETITOR_LIST = [
    "LivingSocial", "Gilt City", "Honey", "RetailMeNot",
    "Rakuten", "Slickdeals", "DealNews", "Woot", "Ibotta"
]

SENSITIVE_TOPICS = [
    "shooting", "terrorist", "attack", "tragedy", "disaster", "death",
    "war", "genocide", "rape", "suicide", "mass shooting", "bombing",
    "election", "abortion", "immigration", "gun control", "racism",
    "protest", "riot", "police brutality"
]

with open("prompts/input_guard.txt", "r") as f:
    INPUT_GUARD_PROMPT = f.read().format(
        COMPETITOR_LIST=COMPETITOR_LIST,
        SENSITIVE_TOPICS=SENSITIVE_TOPICS
    )

with open("prompts/output_guard.txt", "r") as f:
    OUTPUT_GUARD_PROMPT = f.read().format(
        COMPETITOR_LIST=COMPETITOR_LIST,
        SENSITIVE_TOPICS=SENSITIVE_TOPICS
    )

MODEL = "claude-sonnet-4-6"


def guard_input(user_message: str, backend: str = "cli") -> dict | None:
    raw = call_model(
        system=INPUT_GUARD_PROMPT,
        user=f"<message>{user_message}</message>",
        model=MODEL,
        backend=backend,
    )
    if not raw:
        log.error("Input guard returned None for message: %s", user_message)
        return None
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        log.error("Input guard JSON parse failed. Raw:\n%s", raw)
        return None
    log.info("Input guard: hard_block=%s flags=%s", result.get("hard_block"), result.get("flags"))
    log_action("input_guard", user_message, result)
    return result


def guard_output(draft_post: str, backend: str = "cli") -> dict | None:
    raw = call_model(
        system=OUTPUT_GUARD_PROMPT,
        user=draft_post,
        model=MODEL,
        backend=backend,
    )
    if not raw:
        log.error("Output guard returned None for draft: %s", draft_post)
        return None
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        log.error("Output guard JSON parse failed. Raw:\n%s", raw)
        return None
    log.info("Output guard: action=%s", result.get("action"))
    log_action("output_guard", draft_post, result)
    return result


def log_action(guard_type: str, content: str, result: dict):
    with open("agent_log.jsonl", "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "guard": guard_type,
            "content": content,
            "result": result
        }) + "\n")


def is_killed() -> bool:
    import os
    return os.path.exists("KILL_SWITCH")


def process_mention(tweet_text: str, agent_draft: str, backend: str = "cli") -> dict:
    if is_killed():
        log.warning("Kill switch active")
        return {"action": "block", "reason": "Kill switch active"}

    input_result = guard_input(tweet_text, backend=backend)
    if not input_result:
        log.error("Input guard failed in process_mention")
        return {"action": "block", "reason": "Input guard failed"}
    if input_result["action"] != "proceed":
        return input_result

    output_result = guard_output(agent_draft, backend=backend)
    if not output_result:
        log.error("Output guard failed in process_mention")
        return {"action": "block", "reason": "Output guard failed"}
    return output_result
