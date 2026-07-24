import json
import logging
from pathlib import Path

from marketing_copy import call_model

log = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.6


def load_catalog_index(catalog_path: Path) -> list[dict]:
    deals = json.loads(catalog_path.read_text())
    return [
        {
            "deal_title":    d.get("deal_title"),
            "merchant_name": d.get("merchant_name"),
            "category":      d.get("category"),
            "city":          d.get("city"),
        }
        for d in deals
    ]


def fetch_full_deal(deal_title: str, merchant_name: str, catalog_path: Path) -> dict | None:
    deals = json.loads(catalog_path.read_text())
    for d in deals:
        if d.get("deal_title") == deal_title and d.get("merchant_name") == merchant_name:
            return d
    return None


def retrieve_deal(
    trigger_type: str,
    trigger_text: str,
    catalog_path: Path,
    prompts_dir: Path,
    backend: str = "api",
    model: str = "claude-haiku-4-5",
) -> dict | None:
    system = (prompts_dir / "retrival.txt").read_text()
    catalog_index = load_catalog_index(catalog_path)

    user = json.dumps({
        "trigger_type": trigger_type,
        "trigger_text": trigger_text,
        "catalog": catalog_index,
    })

    raw = call_model(system=system, user=user, model=model, backend=backend)
    if not raw:
        log.warning("Model returned nothing for trigger: %s", trigger_text)
        return None

    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        match = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("JSON parse failed. Raw:\n%s", raw)
        return None

    confidence = match.get("confidence", 0)
    log.info("Match: %s | %s | confidence=%.2f | reason: %s",
             match.get("deal_title"), match.get("merchant_name"), confidence, match.get("reason"))

    if confidence < CONFIDENCE_THRESHOLD:
        log.info("Confidence %.2f below threshold %.2f — no deal retrieved", confidence, CONFIDENCE_THRESHOLD)
        return None

    full_deal = fetch_full_deal(match["deal_title"], match["merchant_name"], catalog_path)
    if not full_deal:
        log.warning("Match not found in catalog: %s / %s", match["deal_title"], match["merchant_name"])
        return None

    log.info("Retrieved full deal: %s", full_deal.get("deal_title"))
    return full_deal


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")

    catalog_path = Path("./deals_catalog.json").resolve()
    prompts_dir  = Path("./prompts").resolve()

    mentions = json.loads(Path("./simulated_mentions.json").read_text())
    trends   = json.loads(Path("./simulated_trends.json").read_text())

    mention = mentions[0]
    log.info("=== MENTION TEST ===")
    log.info("Trigger: %s", mention["text"])
    deal = retrieve_deal(
        trigger_type="mention",
        trigger_text=mention["text"],
        catalog_path=catalog_path,
        prompts_dir=prompts_dir,
        backend="api",
    )
    if deal:
        log.info("Full deal: %s — %s", deal["merchant_name"], deal["deal_title"])
    else:
        log.info("No deal matched")

    print()

    trend = trends[0]
    log.info("=== TREND TEST ===")
    log.info("Trigger: %s", trend["name"])
    deal = retrieve_deal(
        trigger_type="trend",
        trigger_text=trend["name"],
        catalog_path=catalog_path,
        prompts_dir=prompts_dir,
        backend="api",
    )
    if deal:
        log.info("Full deal: %s — %s", deal["merchant_name"], deal["deal_title"])
    else:
        log.info("No deal matched")
