"""
rag_pipeline.py — Groq-powered RAG brief generation for PropPulse

Reads:   backend/data/melbourne_weekly.json   (NLP pipeline output)
Writes:  backend/data/briefs/week_{WEEK}.json  (generated brief)
Prints:  Full brief to console

Run directly:  python rag_pipeline.py
Requires:      pip install groq python-dotenv
               GROQ_API_KEY set in .env
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# ---------------------------------------------------------------------------
# Paths & config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
WEEKLY_PATH = DATA_DIR / "melbourne_weekly.json"
BRIEFS_DIR = DATA_DIR / "briefs"

load_dotenv(BASE_DIR.parent / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# How many content blocks to inject per source — enough for rich context
# without overloading the prompt. 70B on Groq supports 131k tokens.
BLOCKS_PER_SOURCE = 30


# ---------------------------------------------------------------------------
# Context builder — serialise weekly JSON into a readable prompt string
# ---------------------------------------------------------------------------

def build_rag_context(weekly: dict) -> str:
    """
    Convert the melbourne_weekly.json structure into a compact, readable
    context block to inject into the LLM prompt.
    """
    lines = []

    # --- Top-level metrics ---
    lines.append(f"WEEK: {weekly.get('week', 'unknown')}")
    lines.append(f"OVERALL MARKET SENTIMENT: {weekly.get('sentiment', 'neutral').upper()}")
    lines.append("")

    # --- Key statistics ---
    stats = weekly.get("key_statistics", {})

    prices = stats.get("prices", [])
    if prices:
        formatted = [f"${p:,}" for p in prices[:8]]
        lines.append(f"PRICE FIGURES MENTIONED: {', '.join(formatted)}")

    percentages = stats.get("percentages", [])
    if percentages:
        lines.append(f"PERCENTAGES MENTIONED: {', '.join(percentages[:12])}")

    rates = stats.get("rates", [])
    if rates:
        lines.append(f"INTEREST/CASH RATE MENTIONS: {', '.join(rates[:5])}")

    lines.append("")

    # --- NER entities ---
    entities = weekly.get("entities", {})
    suburbs = entities.get("suburbs_mentioned", [])
    if suburbs:
        lines.append(f"SUBURBS MENTIONED: {', '.join(suburbs)}")

    orgs = entities.get("organisations", [])
    if orgs:
        lines.append(f"ORGANISATIONS MENTIONED: {', '.join(orgs[:6])}")

    lines.append("")

    # --- Top themes ---
    themes = weekly.get("top_themes", [])
    if themes:
        lines.append("TOP MARKET THEMES THIS WEEK:")
        for i, theme in enumerate(themes, 1):
            lines.append(f"  {i}. {theme}")
    lines.append("")

    # --- Raw content samples from each source ---
    raw_content = weekly.get("raw_content", {})
    lines.append("SOURCE CONTENT (sampled):")
    lines.append("-" * 40)

    for source_name, blocks in raw_content.items():
        if not blocks:
            continue
        lines.append(f"\n[Source: {source_name}]")
        for block in blocks[:BLOCKS_PER_SOURCE]:
            lines.append(block)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a senior property market analyst writing for Melbourne
real estate agents. Your job is to produce a professional weekly market brief
that agents can share directly with their clients.

Tone: confident, data-driven, and clear. Write in plain English — no jargon,
no hedging phrases like "it seems" or "possibly". Agents trust you.

You will be given real scraped market data and NLP analysis from this week.
Ground every claim in the provided data. Do not invent statistics not present
in the context."""


def build_user_prompt(context: str, week: str) -> str:
    return f"""Below is this week's Melbourne property market data ({week}):

--- MARKET DATA START ---
{context}
--- MARKET DATA END ---

Using only the data above, write a weekly market brief with exactly these
four sections. Use the exact section headers shown.

---

## Market Snapshot

Provide 4–6 bullet points. Each bullet must contain a specific number or
statistic from the data (prices, rates, percentages, clearance rates etc.).
Format: "• [Metric]: [value] — [one-sentence context]"

## Weekly Narrative

Write 2–3 confident paragraphs summarising what happened in the Melbourne
property market this week. This is the section agents will copy-paste to
send to clients. Make it engaging and authoritative. Reference specific
suburbs, price movements, or trends from the data where possible.

## Top Themes This Week

List the top themes driving the Melbourne market this week. For each theme,
write 1–2 sentences explaining why it matters to buyers and sellers right now.

## Agent Outlook

Write one focused paragraph of actionable advice. What should agents be
telling their vendor clients? Their buyer clients? What does the data say
about timing the market this week? Be direct and specific.

---

End the brief with a single line: "Data sources: [list the source names]"
"""


# ---------------------------------------------------------------------------
# Groq API call
# ---------------------------------------------------------------------------

def call_groq(system_prompt: str, user_prompt: str) -> str:
    """
    Send a chat completion request to Groq and return the response text.
    Raises RuntimeError if the API key is missing or the call fails.
    """
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not found. Add it to your .env file:\n"
            "  GROQ_API_KEY=your_key_here"
        )

    client = Groq(api_key=GROQ_API_KEY)

    print(f"[RAG] Calling Groq ({MODEL})...")
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,    # low enough for factual grounding, enough for fluency
        max_tokens=2048,
    )

    return completion.choices[0].message.content


# ---------------------------------------------------------------------------
# Brief parser — split LLM response into structured sections
# ---------------------------------------------------------------------------

def parse_brief_sections(raw_text: str) -> dict:
    """
    Split the LLM's markdown response into a dict keyed by section name.
    Falls back to storing the full text under 'full_text' if parsing fails.
    """
    sections = {
        "market_snapshot": "",
        "weekly_narrative": "",
        "top_themes": "",
        "agent_outlook": "",
        "data_sources": "",
        "full_text": raw_text,
    }

    # Split on ## headers
    import re
    parts = re.split(r"\n##\s+", raw_text)

    section_map = {
        "market snapshot":    "market_snapshot",
        "weekly narrative":   "weekly_narrative",
        "top themes":         "top_themes",
        "agent outlook":      "agent_outlook",
    }

    for part in parts:
        lines = part.strip().splitlines()
        if not lines:
            continue
        header = lines[0].lower().strip()
        body = "\n".join(lines[1:]).strip()

        for key, field in section_map.items():
            if key in header:
                sections[field] = body
                break

    # Extract data sources line at the end
    sources_match = re.search(r"Data sources?:\s*(.+)", raw_text, re.I)
    if sources_match:
        sections["data_sources"] = sources_match.group(1).strip()

    return sections


# ---------------------------------------------------------------------------
# Save brief to disk
# ---------------------------------------------------------------------------

def save_brief(week: str, brief: dict) -> Path:
    """
    Save the generated brief to data/briefs/week_{week}.json.
    Returns the path written to.
    """
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BRIEFS_DIR / f"week_{week}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate_brief() -> dict:
    """
    Full RAG pipeline:
      1. Load melbourne_weekly.json
      2. Build context string
      3. Call Groq LLM
      4. Parse + save brief
      5. Print to console
    """
    print("=" * 60)
    print("PropPulse RAG Pipeline")
    print(f"Model : {MODEL}")
    print(f"Time  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # --- Load weekly NLP data ---
    if not WEEKLY_PATH.exists():
        raise FileNotFoundError(
            f"melbourne_weekly.json not found at {WEEKLY_PATH}. "
            "Run nlp_pipeline.py first."
        )

    with open(WEEKLY_PATH, "r", encoding="utf-8") as f:
        weekly = json.load(f)

    week = weekly.get("week", datetime.now(timezone.utc).strftime("%Y-W%W"))
    sources_used = list(weekly.get("raw_content", {}).keys())
    print(f"[RAG] Loaded weekly data for {week}")
    print(f"[RAG] Sources: {', '.join(sources_used)}")
    print(f"[RAG] Sentiment: {weekly.get('sentiment', '—')}")
    print(f"[RAG] Themes: {weekly.get('top_themes', [])}")

    # --- Build RAG context ---
    print("[RAG] Building context...")
    context = build_rag_context(weekly)
    print(f"[RAG] Context: {len(context):,} characters")

    # --- Call Groq ---
    user_prompt = build_user_prompt(context, week)
    raw_response = call_groq(SYSTEM_PROMPT, user_prompt)
    print("[RAG] Response received.")

    # --- Parse sections ---
    sections = parse_brief_sections(raw_response)

    # --- Assemble final brief object ---
    brief = {
        "week": week,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "sentiment": weekly.get("sentiment"),
        "top_themes": weekly.get("top_themes", []),
        "sections": {
            "market_snapshot": sections["market_snapshot"],
            "weekly_narrative": sections["weekly_narrative"],
            "top_themes": sections["top_themes"],
            "agent_outlook": sections["agent_outlook"],
        },
        "data_sources": sections["data_sources"] or ", ".join(sources_used),
        "full_text": sections["full_text"],
    }

    # --- Save ---
    out_path = save_brief(week, brief)
    print(f"[RAG] Brief saved → {out_path}")

    # --- Print to console ---
    print("\n" + "=" * 60)
    print(f"  PROPPULSE WEEKLY BRIEF — {week}")
    print("=" * 60)
    print(raw_response)
    print("=" * 60)

    return brief


if __name__ == "__main__":
    generate_brief()
