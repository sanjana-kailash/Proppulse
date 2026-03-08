"""
main.py — FastAPI application entry point for PropPulse

Endpoints:
  GET  /api/health          — health check
  GET  /api/suburbs         — list available suburb slugs
  GET  /api/suburb/{name}   — suburb context JSON
  GET  /api/dashboard       — aggregated weekly metrics
  POST /api/generate-brief  — run full pipeline and return brief
  GET  /api/brief/latest    — most recently generated brief

Run with:  uvicorn main:app --reload
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import nlp_pipeline
import rag_pipeline
import scraper


# ---------------------------------------------------------------------------
# Paths & env
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SUBURBS_DIR = DATA_DIR / "suburbs"
BRIEFS_DIR = DATA_DIR / "briefs"
WEEKLY_PATH = DATA_DIR / "melbourne_weekly.json"

load_dotenv(BASE_DIR.parent / ".env")


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PropPulse API",
    description="Melbourne property market intelligence for real estate agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup message
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_message():
    print("\n" + "=" * 55)
    print("  PropPulse API — started")
    print("=" * 55)
    print("  GET  /api/health")
    print("  GET  /api/suburbs")
    print("  GET  /api/suburb/{name}")
    print("  GET  /api/dashboard")
    print("  POST /api/generate-brief")
    print("  GET  /api/brief/latest")
    print("=" * 55)
    print(f"  Docs: http://localhost:8000/docs")
    print("=" * 55 + "\n")


# ---------------------------------------------------------------------------
# Helper — load JSON file safely
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_suburb_summaries() -> list[dict]:
    if not SUBURBS_DIR.exists():
        return []

    summaries = []
    for path in sorted(SUBURBS_DIR.glob("*.json")):
        suburb = load_json(path)
        metrics = suburb.get("metrics", {})
        summaries.append(
            {
                "name": suburb.get("suburb"),
                "slug": suburb.get("suburb_slug", path.stem),
                "postcode": suburb.get("postcode"),
                "week": suburb.get("week"),
                "sentiment": suburb.get("market_context", {}).get("sentiment"),
                "median_house_price": metrics.get("median_house_price"),
                "median_unit_price": metrics.get("median_unit_price"),
                "clearance_rate": metrics.get("clearance_rate"),
                "median_days_on_market": metrics.get("median_days_on_market"),
                "quarterly_growth": metrics.get("quarterly_growth"),
            }
        )

    return summaries


def build_chat_response(question: str, suburb_data: dict) -> str:
    suburb = suburb_data.get("suburb", "This suburb")
    metrics = suburb_data.get("metrics", {})
    context = suburb_data.get("market_context", {})
    themes = context.get("top_themes", [])[:3]
    snippets = suburb_data.get("relevant_content", [])[:2]

    lower_question = question.lower()
    if "sell" in lower_question or "vendor" in lower_question:
        lead = (
            f"{suburb} currently reads as a "
            f"{context.get('sentiment', 'balanced')} market for vendors."
        )
        action = (
            f" With a clearance rate of {metrics.get('clearance_rate', 'n/a')}% and "
            f"median days on market around {metrics.get('median_days_on_market', 'n/a')}, "
            "well-priced listings should still attract attention."
        )
    elif "buy" in lower_question or "buyer" in lower_question:
        lead = (
            f"Buyers in {suburb} are dealing with a market that is "
            f"{context.get('sentiment', 'mixed')} overall."
        )
        action = (
            f" Median unit pricing near ${metrics.get('median_unit_price', 0):,} and "
            f"quarterly growth of {metrics.get('quarterly_growth', 'n/a')}% suggest "
            "there is still room for selective negotiation."
        )
    elif "price" in lower_question or "worth" in lower_question or "value" in lower_question:
        lead = (
            f"In {suburb}, the current benchmark pricing is about "
            f"${metrics.get('median_house_price', 0):,} for houses and "
            f"${metrics.get('median_unit_price', 0):,} for units."
        )
        action = (
            f" Quarterly growth is {metrics.get('quarterly_growth', 'n/a')}%, so "
            "pricing conversations should stay grounded in recent comparables rather than peak-market expectations."
        )
    else:
        lead = (
            f"{suburb} is tracking as a {context.get('sentiment', 'balanced')} market this week."
        )
        action = (
            f" Key local signals are a {metrics.get('clearance_rate', 'n/a')}% clearance rate, "
            f"{metrics.get('median_days_on_market', 'n/a')} median days on market, and "
            f"{metrics.get('quarterly_growth', 'n/a')}% quarterly growth."
        )

    theme_text = f" The main themes showing up are {', '.join(themes)}." if themes else ""
    snippet_text = f" Recent coverage notes: {snippets[0]}" if snippets else ""
    return f"{lead}{action}{theme_text}{snippet_text}"


class ChatRequest(BaseModel):
    suburb: str
    question: str


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    """Confirms the server is running."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /api/suburbs
# ---------------------------------------------------------------------------

@app.get("/api/suburbs")
def get_suburbs():
    """
    Returns a list of suburb slugs available in data/suburbs/.
    Each slug corresponds to a {slug}.json file.
    """
    if not SUBURBS_DIR.exists():
        return {"suburbs": []}

    slugs = [
        p.stem for p in sorted(SUBURBS_DIR.glob("*.json"))
        if not p.stem.startswith(".")
    ]
    return {"suburbs": slugs}


# ---------------------------------------------------------------------------
# GET /api/suburb/{name}
# ---------------------------------------------------------------------------

@app.get("/api/suburb/{name}")
def get_suburb(name: str):
    """
    Returns the full context JSON for a suburb.
    {name} should be a slug e.g. 'south-yarra', 'richmond'.
    """
    path = SUBURBS_DIR / f"{name}.json"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Suburb '{name}' not found. "
                   f"Run the pipeline first or check the slug spelling.",
        )
    return load_json(path)


# ---------------------------------------------------------------------------
# GET /api/dashboard
# ---------------------------------------------------------------------------

@app.get("/api/dashboard")
def get_dashboard():
    """
    Returns the aggregated weekly metrics from melbourne_weekly.json.
    Includes: week, sentiment, top_themes, key_statistics, sources_scraped.
    """
    if not WEEKLY_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Weekly data not found. Run the pipeline first: POST /api/generate-brief",
        )

    weekly = load_json(WEEKLY_PATH)

    return {
        "week": weekly.get("week"),
        "generated_at": weekly.get("generated_at"),
        "sentiment": weekly.get("sentiment"),
        "top_themes": weekly.get("top_themes", []),
        "key_statistics": weekly.get("key_statistics", {}),
        "sources_scraped": weekly.get("sources_scraped", 0),
        "total_content_blocks": weekly.get("total_content_blocks", 0),
        "suburbs": list_suburb_summaries(),
    }


# ---------------------------------------------------------------------------
# POST /api/generate-brief
# ---------------------------------------------------------------------------

def _run_full_pipeline() -> dict:
    """
    Synchronous wrapper that runs all three pipeline stages in sequence.
    Called from the async endpoint via asyncio.to_thread().
    """
    # Stage 1 — scrape
    print("[API] Stage 1/3: Running scraper...")
    scraper.main()

    # Stage 2 — NLP
    print("[API] Stage 2/3: Running NLP pipeline...")
    nlp_pipeline.run_pipeline()

    # Stage 3 — RAG / brief generation
    print("[API] Stage 3/3: Generating brief with Groq...")
    brief = rag_pipeline.generate_brief()

    return brief


@app.post("/api/generate-brief")
async def generate_brief():
    """
    Runs the full pipeline (scrape → NLP → RAG) and returns the generated brief.
    Expect ~30–60 seconds. The pipeline stages print progress to the server console.
    """
    try:
        # Run the blocking pipeline in a thread so the event loop stays free
        brief = await asyncio.to_thread(_run_full_pipeline)
        return {
            "status": "success",
            "week": brief.get("week"),
            "generated_at": brief.get("generated_at"),
            "brief": brief,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        # Catches missing GROQ_API_KEY and similar config errors
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed: {type(e).__name__}: {e}",
        )


# ---------------------------------------------------------------------------
# GET /api/brief/latest
# ---------------------------------------------------------------------------

@app.get("/api/brief/latest")
def get_latest_brief():
    """
    Returns the most recently generated brief from data/briefs/.
    Files are named week_{YYYY-WNN}.json — sorted alphabetically gives latest last.
    """
    if not BRIEFS_DIR.exists():
        raise HTTPException(
            status_code=404,
            detail="No briefs found. Run POST /api/generate-brief first.",
        )

    brief_files = sorted(BRIEFS_DIR.glob("week_*.json"))

    if not brief_files:
        raise HTTPException(
            status_code=404,
            detail="No briefs found. Run POST /api/generate-brief first.",
        )

    latest = brief_files[-1]   # lexicographic sort on week_YYYY-WNN puts latest last
    return load_json(latest)


@app.post("/api/chat")
def chat(req: ChatRequest):
    path = SUBURBS_DIR / f"{req.suburb}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Suburb '{req.suburb}' not found.")

    suburb_data = load_json(path)
    answer = build_chat_response(req.question, suburb_data)
    return {
        "suburb": suburb_data.get("suburb"),
        "answer": answer,
    }
