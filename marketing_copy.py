import os
import subprocess
import re
import json
from pathlib import Path

def load_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
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



def call_model(system: str, user: str, model: str, backend: str = "cli") -> str | None:
    if backend == "cli":
        import sys, os, tempfile
        if sys.platform == "win32":
            # cmd.exe has an 8191-char arg limit; PS 5.1 word-splits variables in native calls.
            # Fix: write prompts to temp files, invoke via a .ps1 script using array splatting
            # (@a) so each element is passed as a discrete arg with no word-splitting.
            sys_f = tempfile.NamedTemporaryFile(mode='w', suffix='_sys.txt', delete=False, encoding='utf-8')
            usr_f = tempfile.NamedTemporaryFile(mode='w', suffix='_usr.txt', delete=False, encoding='utf-8')
            ps1_f = tempfile.NamedTemporaryFile(mode='w', suffix='.ps1',    delete=False, encoding='utf-8')
            sys_f.write(system); sys_f.close()
            usr_f.write(user);   usr_f.close()
            ps1_f.write(
                f"$s = Get-Content -Raw -LiteralPath '{sys_f.name}'\n"
                f"$u = Get-Content -Raw -LiteralPath '{usr_f.name}'\n"
                f"$s = $s -replace '\"', '\\\"'\n"
                f"$u = $u -replace '\"', '\\\"'\n"
                f"$a = @('-p', $u, '--system-prompt', $s, '--model', '{model}')\n"
                f"& claude @a\n"
            )
            ps1_f.close()
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1_f.name],
                    capture_output=True, text=True, encoding='utf-8',
                )
            finally:
                os.unlink(sys_f.name)
                os.unlink(usr_f.name)
                os.unlink(ps1_f.name)
        else:
            result = subprocess.run(
                ["claude", "-p", user, "--system-prompt", system, "--model", model],
                capture_output=True, text=True,
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
    agent_input: dict, references_dir: Path, model="claude-haiku-4-5", backend="cli",
    revision_feedback: list[dict] | None = None,
) -> list[dict] | None:
    context = load_context(references_dir, WRITE_ONLY)
    write_prompt = (references_dir / ".." / "copywriter.txt").read_text(encoding="utf-8")

    if revision_feedback:
        feedback_block = "\n\n".join(
            f'Prior draft: "{f["copy"]}"\n'
            f'Failures:\n' + "\n".join(f"  - {fail}" for fail in f.get("failures", [])) + "\n"
            f'Instruction: {f["feedback"]}'
            for f in revision_feedback
        )
        user = (
            "Previous attempt failed review. Rewrite addressing this feedback "
            "before generating new copy:\n\n"
            f"{feedback_block}\n\n---\n\n{json.dumps(agent_input)}"
        )
    else:
        user = json.dumps(agent_input)

    text = call_model(
        system=f"{write_prompt}\n\n{context}",
        user=user,
        model=model,
        backend=backend,
    )
    if not text:
        return None
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        import logging
        logging.getLogger(__name__).warning("generate_copy JSON parse failed. Raw:\n%s", text)
        return None


def review_copy(
    results: list[dict], references_dir: Path, model="claude-haiku-4-5", backend="cli"
) -> list[dict] | None:
    context = load_context(references_dir, REVIEW_ONLY)
    reviewer_prompt = (references_dir / ".." / "copy_reviewer.txt").read_text(encoding="utf-8")

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

def generate_and_review(agent_input: dict, references_dir: Path, max_attempts=3, backend="cli", model="claude-haiku-4-5"):
    import logging
    log = logging.getLogger(__name__)
    reviewed = []
    feedback: list[dict] | None = None
    for attempt in range(1, max_attempts + 1):
        log.info("Attempt %d/%d", attempt, max_attempts)
        results = generate_copy(agent_input, references_dir, model=model, backend=backend,
                                revision_feedback=feedback)
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

        feedback = [
            {"copy": r.get("copy"), "failures": r.get("failures", []), "feedback": r.get("feedback_for_rewrite")}
            for r in reviewed
            if r.get("verdict") != "pass" and r.get("feedback_for_rewrite")
        ]
        if feedback:
            log.info("Feeding reviewer feedback into next attempt")
        log.info("Not all passed — retrying")

    return {"status": "escalate", "results": reviewed}

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
    log = logging.getLogger(__name__)

    references_dir = Path("./prompts/references").resolve()
    catalog = Path("./deals_catalog.json").resolve()

    deals = json.loads(catalog.read_text(encoding='utf-8'))
    deal = deals[0]
    log.info("Loaded deal: %s — %s", deal.get("merchant_name"), deal.get("deal_title"))

    agent_input = build_agent_input(deal, segment="spontaneous_locals", variations=2)
    log.info("Agent input built: %s", json.dumps(agent_input, indent=2))

    log.info("Running generate_and_review (backend=api)...")
    result = generate_and_review(agent_input, references_dir, backend="cli", model="claude-sonnet-4-6")

    log.info("Status: %s", result["status"])
    for i, item in enumerate(result.get("results") or [], 1):
        log.info("Result %d: verdict=%s", i, item.get("verdict"))
        log.info("  copy: %s", item.get("copy") or item.get("text") or item)
