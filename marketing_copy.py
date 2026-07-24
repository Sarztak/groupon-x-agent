import os
import subprocess
import re
import json
from pathlib import Path

def load_file(path: Path) -> str:
    with open(path, "r") as f:
        return f.read()


SHARED_TOV = [
    "messaging-house.md",
    "tov/voice-pillars.md",
    "tov/voice-dna.md",
    "tov/audience-modulation.md",
    "tov/pillar-translator.md",
    "tov/funnel-application.md",
    "tov/channels/organic-social.md",
    "tov/channels/display-ads.md",
    "tov/channels/crm.md",
    "tov/channels/sem.md",
    "tov/channels/seo.md",
    "tov/channels/imp.md",
]

WRITE_ONLY = [
    "tov/key-messages.md",
    "agent-notes/named-patterns.md",
    "_SOURCES.md",
]

REVIEW_ONLY = [
    "agent-notes/review-rubric.md",
    "agent-notes/anti-patterns.md",
]


def load_context(references_dir: Path, extra_files: list) -> str:
    files = SHARED_TOV + extra_files
    sections = []
    for f in files:
        path = references_dir / f
        if os.path.exists(path):
            sections.append(f"## {f}\n\n{load_file(path)}")
        else:
            print(f"Warning: {path} not found, skipping")
    return "\n\n---\n\n".join(sections)



def call_model(system: str, user: str, model: str, backend: str = "api") -> str | None:
    if backend == "cli":
        result = subprocess.run(
            ["claude", "-p", user, "--system", system, "--model", model],
            capture_output=True, text=True
        )
        return result.stdout.strip() if result.returncode == 0 else None

    from anthropic import Anthropic
    from dotenv import load_dotenv
    load_dotenv()
    client = Anthropic()

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    for block in response.content:
        if block.type == "text":
            return block.text
    return None


def generate_copy(
    agent_input: dict, references_dir: Path, model="claude-haiku-4-5", backend="api"
) -> list[dict] | None:
    context = load_context(references_dir, WRITE_ONLY)
    write_prompt = (references_dir / ".." / "copywriter.txt").read_text()

    text = call_model(
        system=f"{write_prompt}\n\n{context}",
        user=json.dumps(agent_input),
        model=model,
        backend=backend,
    )
    if not text:
        return None
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import logging
        logging.getLogger(__name__).warning("generate_copy JSON parse failed. Raw:\n%s", text)
        return None


def review_copy(
    results: list[dict], references_dir: Path, model="claude-haiku-4-5", backend="api"
) -> list[dict] | None:
    context = load_context(references_dir, REVIEW_ONLY)
    reviewer_prompt = (references_dir / ".." / "copy_reviewer.txt").read_text()

    text = call_model(
        system=f"{reviewer_prompt}\n\n{context}",
        user=json.dumps(results),
        model=model,
        backend=backend,
    )
    if not text:
        return None
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

def build_merchant_info(deal) -> str | None:
    parts = filter(None, [
        deal.get('merchant_description'),
        deal.get('merchant_info'),
        deal.get('highlights')
    ])
    return '\n\n'.join(parts) or None

def clean_reviews(reviews) -> list:
    cleaned = []
    for r in reviews:
        match = re.search(r'\d+\s+(?:hours?|days?|weeks?|months?|minutes?)\s+ago\n(.+)', r)
        if match:
            cleaned.append(match.group(1).strip())
    return cleaned

def build_agent_input(deal, segment, variations=1):
    return {
        "deal": {
            "deal_title":    deal.get("deal_title"),
            "merchant_name": deal.get("merchant_name"),
            "location":      deal.get("location"),
            "city":          deal.get("city"),
            "merchant_info": build_merchant_info(deal),
            "reviews":       clean_reviews(deal.get("reviews", []))
        },
        "segment":    segment,
        "variations": variations
    }

def generate_and_review(agent_input: dict, references_dir: Path, max_attempts=3, backend="api", model="claude-haiku-4-5"):
    import logging
    log = logging.getLogger(__name__)
    reviewed = []
    for attempt in range(1, max_attempts + 1):
        log.info("Attempt %d/%d", attempt, max_attempts)
        results = generate_copy(agent_input, references_dir, model=model, backend=backend)
        if not results:
            log.warning("generate_copy returned nothing — skipping")
            continue
        log.info("Generated %d copy variation(s)", len(results) if isinstance(results, list) else 1)

        reviewed = review_copy(results, references_dir, model=model, backend=backend)
        if not reviewed:
            log.warning("review_copy returned nothing — skipping")
            continue
        log.info("Review results: %s", json.dumps(reviewed, indent=2))

        verdicts = [r.get("verdict") for r in reviewed]
        log.info("Verdicts: %s", verdicts)
        if all(v == "pass" for v in verdicts):
            return {"status": "pass", "results": reviewed}
        log.info("Not all passed — retrying")

    return {"status": "escalate", "results": reviewed}

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
    log = logging.getLogger(__name__)

    references_dir = Path("./prompts/references").resolve()
    catalog = Path("./deals_catalog.json").resolve()

    deals = json.loads(catalog.read_text())
    deal = deals[0]
    log.info("Loaded deal: %s — %s", deal.get("merchant_name"), deal.get("deal_title"))

    agent_input = build_agent_input(deal, segment="spontaneous_locals", variations=2)
    log.info("Agent input built: %s", json.dumps(agent_input, indent=2))

    log.info("Running generate_and_review (backend=api)...")
    result = generate_and_review(agent_input, references_dir, backend="api", model="claude-sonnet-4-6")

    log.info("Status: %s", result["status"])
    for i, item in enumerate(result.get("results") or [], 1):
        log.info("Result %d: verdict=%s", i, item.get("verdict"))
        log.info("  copy: %s", item.get("copy") or item.get("text") or item)
