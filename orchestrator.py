import json
import logging
from pathlib import Path

from marketing_copy import call_model

log = logging.getLogger(__name__)

PROMPTS_DIR = Path("./prompts").resolve()


def orchestrate(
    message: str,
    username: str,
    guard_report: dict,
    backend: str = "api",
    model: str = "claude-sonnet-4-6",
    prompts_dir: Path = PROMPTS_DIR,
) -> dict | None:
    system = (prompts_dir / "orchestrator.txt").read_text()

    user = json.dumps({
        "message": message,
        "username": username,
        "guard_report": guard_report,
    })

    raw = call_model(system=system, user=user, model=model, backend=backend)
    if not raw:
        log.warning("Orchestrator returned nothing for message: %s", message)
        return None

    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Orchestrator JSON parse failed. Raw:\n%s", raw)
        return None

    log.info("Route: %s | reasoning: %s", decision.get("route"), decision.get("reasoning"))
    return decision
