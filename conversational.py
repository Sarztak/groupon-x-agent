import json
import logging
from pathlib import Path

from marketing_copy import call_model

log = logging.getLogger(__name__)

PROMPTS_DIR = Path("./prompts").resolve()


def generate_conversational_reply(
    mode: str,
    mention_text: str,
    username: str,
    deal_copy: str | None = None,
    backend: str = "cli",
    model: str = "claude-sonnet-4-6",
    prompts_dir: Path = PROMPTS_DIR,
    revision_feedback: str | None = None,
) -> dict | None:
    system = (prompts_dir / "conversational_voice.txt").read_text(encoding="utf-8")

    payload = json.dumps({
        "mode": mode,
        "mention_text": mention_text,
        "username": username,
        "deal_copy": deal_copy,
    })

    if revision_feedback:
        user = (
            f"Previous attempt was rejected. Rewrite addressing this feedback:\n\n"
            f"{revision_feedback}\n\n---\n\n{payload}"
        )
    else:
        user = payload

    raw = call_model(system=system, user=user, model=model, backend=backend)
    if not raw:
        log.warning("Conversational agent returned nothing for mode: %s", mode)
        return None

    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        reply = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Conversational JSON parse failed. Raw:\n%s", raw)
        return None

    log.info("Mode: %s | reply: %s", reply.get("mode"), reply.get("reply"))
    return reply
