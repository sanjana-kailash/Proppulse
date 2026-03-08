"""
nlp_pipeline.py — NLP processing pipeline for PropPulse

Reads:   backend/data/raw_articles.json   (list of 4 source dicts from scraper.py)
Writes:
  backend/data/melbourne_weekly.json      (combined NLP analysis for RAG)
  backend/data/suburbs/{slug}.json        (per-suburb context using mock metrics)

Run directly:  python nlp_pipeline.py
Requires:      pip install spacy && python -m spacy download en_core_web_sm
"""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

import spacy


# ---------------------------------------------------------------------------
# Paths & config
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_ARTICLES_PATH = os.path.join(DATA_DIR, "raw_articles.json")
SUBURBS_DIR = os.path.join(DATA_DIR, "suburbs")
WEEKLY_OUTPUT_PATH = os.path.join(DATA_DIR, "melbourne_weekly.json")

CURRENT_WEEK = datetime.now(timezone.utc).strftime("%Y-W%W")
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Mock suburb metrics (realistic Melbourne 2025 values)
# ---------------------------------------------------------------------------

SUBURB_MOCK_DATA: dict[str, dict] = {
    "richmond": {
        "suburb": "Richmond",
        "suburb_slug": "richmond",
        "postcode": "3121",
        "median_house_price": 1_385_000,
        "median_unit_price": 615_000,
        "clearance_rate": 74.2,
        "median_days_on_market": 28,
        "quarterly_growth": 1.8,
    },
    "fitzroy": {
        "suburb": "Fitzroy",
        "suburb_slug": "fitzroy",
        "postcode": "3065",
        "median_house_price": 1_520_000,
        "median_unit_price": 580_000,
        "clearance_rate": 71.5,
        "median_days_on_market": 24,
        "quarterly_growth": 2.3,
    },
    "collingwood": {
        "suburb": "Collingwood",
        "suburb_slug": "collingwood",
        "postcode": "3066",
        "median_house_price": 1_290_000,
        "median_unit_price": 545_000,
        "clearance_rate": 68.9,
        "median_days_on_market": 32,
        "quarterly_growth": -0.5,
    },
    "brunswick": {
        "suburb": "Brunswick",
        "suburb_slug": "brunswick",
        "postcode": "3056",
        "median_house_price": 1_175_000,
        "median_unit_price": 490_000,
        "clearance_rate": 66.3,
        "median_days_on_market": 35,
        "quarterly_growth": 0.9,
    },
    "south-yarra": {
        "suburb": "South Yarra",
        "suburb_slug": "south-yarra",
        "postcode": "3141",
        "median_house_price": 2_150_000,
        "median_unit_price": 720_000,
        "clearance_rate": 76.8,
        "median_days_on_market": 21,
        "quarterly_growth": 3.1,
    },
}

KNOWN_SUBURBS: set[str] = {
    "Richmond", "Fitzroy", "Collingwood", "Brunswick", "South Yarra",
    "Melbourne", "Hawthorn", "Carlton", "Prahran", "St Kilda",
    "Northcote", "Abbotsford", "Cremorne", "Toorak", "Windsor",
    "Docklands", "Southbank", "Port Melbourne", "Albert Park",
    "Moonee Ponds", "Essendon", "Kew", "Camberwell", "Box Hill",
    "Doncaster", "Williamstown", "Newport", "Footscray", "Sunshine",
}

SUBURB_SLUG_MAP: dict[str, str] = {
    "Richmond": "richmond",
    "Fitzroy": "fitzroy",
    "Collingwood": "collingwood",
    "Brunswick": "brunswick",
    "South Yarra": "south-yarra",
}


# ---------------------------------------------------------------------------
# Sentiment — keyword scoring
# ---------------------------------------------------------------------------

_POSITIVE_WORDS = {
    "growth", "grew", "rise", "rising", "rose", "surge", "surged", "strong",
    "confidence", "demand", "rally", "resilient", "boom", "increase", "increased",
    "improve", "improved", "uptick", "record", "outperform", "gain", "gains",
    "robust", "positive", "recover", "recovery", "momentum", "buoyant", "elevated",
    "climb", "climbed", "acceleration", "opportunity",
}

_NEGATIVE_WORDS = {
    "fall", "falling", "fell", "decline", "declined", "drop", "dropped", "weak",
    "slowdown", "concern", "crisis", "risk", "downturn", "struggle", "soften",
    "softened", "slump", "decrease", "decreased", "contraction", "pressure",
    "affordability", "unaffordable", "correction", "retreat", "retreated",
    "cautious", "uncertainty", "headwinds", "stagnant", "flat",
}


def score_sentiment(text: str) -> str:
    """
    Return 'positive', 'negative', or 'neutral' based on keyword frequency.
    """
    words = re.findall(r"\b[a-z]+\b", text.lower())
    pos = sum(1 for w in words if w in _POSITIVE_WORDS)
    neg = sum(1 for w in words if w in _NEGATIVE_WORDS)

    if pos > neg * 1.2:
        return "positive"
    if neg > pos * 1.2:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Topic classification — keyword rules
# ---------------------------------------------------------------------------

TOPIC_RULES: list[tuple[str, list[str]]] = [
    ("Interest rate & policy", [
        "cash rate", "interest rate", "rba", "reserve bank", "rate cut", "rate hike",
        "monetary policy", "inflation", "cpi", "treasury", "budget", "apra",
        "rate decision", "basis points",
    ]),
    ("Rental market & affordability", [
        "rent", "rental", "tenant", "landlord", "vacancy", "renters", "lease",
        "rental yield", "rental crisis", "housing affordability", "renter",
        "rental growth", "vacancy rate",
    ]),
    ("Auction & price movement", [
        "median price", "house price", "property value", "clearance rate",
        "auction", "sold", "price growth", "price fall", "price drop",
        "values rose", "values fell", "price record", "dwelling value",
        "median house", "median unit", "reserve price",
    ]),
    ("Supply & new development", [
        "development", "rezoning", "planning", "council", "construction",
        "new development", "apartment", "high-rise", "precinct", "supply",
        "listings", "new listings", "stock", "pipeline", "build",
    ]),
    ("Buyer & investor activity", [
        "buyer", "investor", "first home buyer", "fhb", "downsizer", "upsizer",
        "demand", "purchaser", "owner-occupier", "investment property",
        "yield", "capital growth", "portfolio",
    ]),
    ("Market outlook & confidence", [
        "confidence", "sentiment", "outlook", "forecast", "predict", "expect",
        "spring selling", "market conditions", "next quarter", "next year",
        "economists", "analysts", "data shows",
    ]),
]


def classify_block(text: str) -> str | None:
    """Return the best-matching topic label for a text block, or None."""
    text_lower = text.lower()
    scores = {label: 0 for label, _ in TOPIC_RULES}
    for label, keywords in TOPIC_RULES:
        for kw in keywords:
            if kw in text_lower:
                scores[label] += 1
    best_label = max(scores, key=lambda l: scores[l])
    return best_label if scores[best_label] > 0 else None


def derive_top_themes(all_blocks: list[str], n: int = 5) -> list[str]:
    """
    Score every content block against topic rules and return the top n themes,
    sorted by how many blocks matched each.
    """
    topic_counts: Counter = Counter()
    for block in all_blocks:
        label = classify_block(block)
        if label:
            topic_counts[label] += 1

    return [label for label, _ in topic_counts.most_common(n)]


# ---------------------------------------------------------------------------
# Statistics extraction — regex
# ---------------------------------------------------------------------------

def extract_statistics(text: str) -> dict:
    """
    Extract price figures, percentage changes, and interest rates from text.

    Returns:
      {
        prices:      [int, ...]     — dollar amounts > $100k
        percentages: [str, ...]     — e.g. "3.2%", "-1.5%"
        rates:       [str, ...]     — interest/cash rate mentions e.g. "4.35%"
      }
    """
    # Dollar amounts: $1.2m, $850k, $1,200,000
    raw_prices = re.findall(r"\$[\d,]+(?:\.\d+)?[mk]?", text, re.I)
    prices = []
    for p in raw_prices:
        parsed = _parse_price(p)
        if parsed and parsed > 100_000:
            prices.append(parsed)

    # All percentages (including negatives)
    percentages = re.findall(r"-?[\d]+\.?\d*\s*(?:per\s*cent|%)", text, re.I)
    percentages = [p.strip() for p in percentages]

    # Interest / cash rate context — percentages near rate keywords
    rate_pattern = re.compile(
        r"(?:cash rate|interest rate|rate)[^.]{0,40}?([\d]+\.[\d]+\s*%?)", re.I
    )
    rates = [m.group(1).strip() for m in rate_pattern.finditer(text)]

    return {
        "prices": sorted(set(prices), reverse=True)[:15],
        "percentages": list(dict.fromkeys(percentages))[:20],
        "rates": list(dict.fromkeys(rates))[:10],
    }


def _parse_price(text: str) -> int | None:
    """Convert '$1.2m' / '$850k' / '$1,200,000' to int."""
    text = text.replace(",", "").strip().lower()
    m = re.search(r"\$?([\d.]+)\s*([mk]?)", text)
    if not m:
        return None
    value = float(m.group(1))
    suffix = m.group(2)
    if suffix == "m":
        return int(value * 1_000_000)
    if suffix == "k":
        return int(value * 1_000)
    return int(value) if value > 100 else None


# ---------------------------------------------------------------------------
# spaCy NER
# ---------------------------------------------------------------------------

def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        raise RuntimeError(
            "spaCy model not found. Run:  python -m spacy download en_core_web_sm"
        )


def extract_entities(text: str, nlp) -> dict:
    """
    Run spaCy NER on text. Returns suburb mentions, price entities, orgs, percents.
    Truncates to 100k chars to stay within spaCy's default limit.
    """
    doc = nlp(text[:100_000])

    suburbs, prices, percentages, organisations = [], [], [], []

    for ent in doc.ents:
        if ent.label_ == "GPE" and ent.text in KNOWN_SUBURBS:
            suburbs.append(ent.text)
        elif ent.label_ == "MONEY":
            parsed = _parse_price(ent.text)
            if parsed and parsed > 100_000:
                prices.append(parsed)
        elif ent.label_ == "PERCENT":
            percentages.append(ent.text)
        elif ent.label_ == "ORG":
            organisations.append(ent.text)

    property_type_re = re.compile(
        r"\b(house|unit|apartment|townhouse|villa|duplex|terrace|cottage)\b", re.I
    )
    property_types = list({m.group().lower() for m in property_type_re.finditer(text)})

    return {
        "suburbs_mentioned": list(dict.fromkeys(suburbs)),
        "prices": sorted(set(prices), reverse=True)[:10],
        "percentages": list(dict.fromkeys(percentages))[:15],
        "organisations": list(dict.fromkeys(organisations))[:10],
        "property_types": property_types,
    }


# ---------------------------------------------------------------------------
# Build melbourne_weekly.json
# ---------------------------------------------------------------------------

def build_weekly_summary(
    sources: list[dict],
    all_blocks: list[str],
    combined_text: str,
    entities: dict,
    themes: list[str],
    stats: dict,
) -> dict:
    """
    Assemble the master weekly output consumed by rag_pipeline.py.
    """
    sentiment = score_sentiment(combined_text)

    # Raw content keyed by source name — preserved for RAG context injection
    raw_content_by_source = {
        s["source"]: s["content"]
        for s in sources
        if s.get("success") and s.get("content")
    }

    return {
        "week": CURRENT_WEEK,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_scraped": len([s for s in sources if s.get("success")]),
        "total_content_blocks": len(all_blocks),
        "sentiment": sentiment,
        "top_themes": themes,
        "key_statistics": stats,
        "entities": entities,
        "raw_content": raw_content_by_source,
    }


# ---------------------------------------------------------------------------
# Build per-suburb context (for rag_pipeline.py suburb briefs)
# ---------------------------------------------------------------------------

def build_suburb_context(
    slug: str,
    mock_metrics: dict,
    weekly_summary: dict,
    relevant_blocks: list[str],
) -> dict:
    """
    Combine mock suburb metrics with the weekly NLP summary into the
    structured context object consumed by rag_pipeline.py.
    """
    return {
        "suburb": mock_metrics["suburb"],
        "suburb_slug": slug,
        "postcode": mock_metrics["postcode"],
        "week": CURRENT_WEEK,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "median_house_price": mock_metrics["median_house_price"],
            "median_unit_price": mock_metrics["median_unit_price"],
            "clearance_rate": mock_metrics["clearance_rate"],
            "median_days_on_market": mock_metrics["median_days_on_market"],
            "quarterly_growth": mock_metrics["quarterly_growth"],
        },
        "market_context": {
            "sentiment": weekly_summary["sentiment"],
            "top_themes": weekly_summary["top_themes"],
            "key_statistics": weekly_summary["key_statistics"],
        },
        # Blocks that explicitly mention this suburb — richer RAG context
        "relevant_content": relevant_blocks[:20],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_pipeline() -> dict:
    """
    Full NLP pipeline:
      1. Load raw_articles.json (list of 4 source dicts)
      2. Combine all content into one corpus
      3. Run NER, theme extraction, stat extraction, sentiment
      4. Save melbourne_weekly.json
      5. Save per-suburb JSON files using mock metrics + weekly context
    """
    print("=" * 60)
    print("PropPulse NLP Pipeline")
    print(f"Week: {CURRENT_WEEK}")
    print("=" * 60)

    # --- Load scraped data ---
    if not os.path.exists(RAW_ARTICLES_PATH):
        raise FileNotFoundError(
            f"raw_articles.json not found at {RAW_ARTICLES_PATH}. "
            "Run scraper.py first."
        )

    with open(RAW_ARTICLES_PATH, "r", encoding="utf-8") as f:
        sources: list[dict] = json.load(f)

    successful = [s for s in sources if s.get("success") and s.get("content")]
    print(f"\n[NLP] Loaded {len(successful)}/{len(sources)} successful sources.")

    if not successful:
        print("[NLP] No content to process — check scraper output.")
        return {}

    # --- Combine all content blocks into one corpus ---
    all_blocks: list[str] = []
    for source in successful:
        all_blocks.extend(source["content"])

    combined_text = " ".join(all_blocks)
    print(f"[NLP] Total content blocks: {len(all_blocks)}")

    # --- Load spaCy ---
    print("[NLP] Loading spaCy model...")
    nlp = load_spacy_model()
    print("[NLP] Model ready.")

    # --- NER across combined corpus ---
    print("[NLP] Running NER...")
    entities = extract_entities(combined_text, nlp)
    print(f"  Suburbs mentioned : {entities['suburbs_mentioned']}")
    print(f"  Prices found      : {len(entities['prices'])}")
    print(f"  Orgs found        : {entities['organisations'][:5]}")

    # --- Theme extraction ---
    print("[NLP] Deriving top themes...")
    themes = derive_top_themes(all_blocks, n=5)
    for i, t in enumerate(themes, 1):
        print(f"  {i}. {t}")

    # --- Stat extraction ---
    print("[NLP] Extracting statistics...")
    stats = extract_statistics(combined_text)
    print(f"  Price figures     : {len(stats['prices'])} found")
    print(f"  Percentages       : {len(stats['percentages'])} found")
    print(f"  Rate mentions     : {stats['rates'][:3]}")

    # --- Sentiment ---
    sentiment = score_sentiment(combined_text)
    print(f"[NLP] Overall sentiment: {sentiment}")

    # --- Build and save melbourne_weekly.json ---
    weekly = build_weekly_summary(sources, all_blocks, combined_text, entities, themes, stats)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(WEEKLY_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(weekly, f, indent=2, ensure_ascii=False)
    print(f"\n[NLP] Saved → {WEEKLY_OUTPUT_PATH}")

    # --- Build per-suburb context files ---
    os.makedirs(SUBURBS_DIR, exist_ok=True)
    print("[NLP] Building suburb context files...")

    for slug, mock_metrics in SUBURB_MOCK_DATA.items():
        display_name = mock_metrics["suburb"]

        # Blocks that mention this suburb by name
        relevant = [
            b for b in all_blocks
            if display_name.lower() in b.lower()
        ]
        # Fallback: include blocks mentioning Melbourne broadly
        if len(relevant) < 3:
            relevant += [b for b in all_blocks if "melbourne" in b.lower()]

        context = build_suburb_context(slug, mock_metrics, weekly, relevant)

        out_path = os.path.join(SUBURBS_DIR, f"{slug}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(context, f, indent=2, ensure_ascii=False)

        print(f"  [saved] {display_name} → {out_path} ({len(relevant)} relevant blocks)")

    print("\n" + "=" * 60)
    print("NLP pipeline complete.")
    print(f"  Weekly summary : {WEEKLY_OUTPUT_PATH}")
    print(f"  Suburb files   : {SUBURBS_DIR}/")
    print("=" * 60)

    return weekly


if __name__ == "__main__":
    run_pipeline()
