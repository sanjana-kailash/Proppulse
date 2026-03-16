# PropPulse 🏡
### AI Property Market Intelligence for Melbourne Real Estate Agents

[![Live Demo](https://img.shields.io/badge/Live%20Demo-proppulse--chi.vercel.app-blue?style=for-the-badge)](https://proppulse-chi.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM-Llama%203.1%2070B-F54E42?style=flat-square)](https://groq.com)

---

## What is PropPulse?

Real estate agents spend hours every Monday reading property blogs, news sites, and market reports just to prepare for client conversations. PropPulse automates that entirely.

It scrapes live property market data from across Melbourne, runs NLP analysis to extract the signals that matter, and generates a ready-to-use **AI-written weekly market briefing** — written in the tone of a senior agent, delivered before the week begins.

**[→ View the live app](https://proppulse-chi.vercel.app/)**

---

## Features

- **Weekly AI Briefs** — LLM-generated market summaries covering price trends, suburb activity, and macroeconomic signals, auto-delivered every week
- **Suburb Intelligence** — Deep-dive pages for individual Melbourne suburbs with trend charts and historical data
- **AI Chat Assistant** — Ask the platform questions about the market and get grounded, data-backed answers via RAG
- **Real-time Dashboard** — Live visualisations of market movements powered by Recharts
- **Fully Automated Pipeline** — From web scraping to NLP to LLM generation, no manual input required

---

## Tech Stack

| Layer         | Technology                                           |
|---------------|------------------------------------------------------|
| Frontend      | React, Vite, Tailwind CSS, Recharts                  |
| Backend       | Python, FastAPI                                      |
| NLP           | spaCy (Named Entity Recognition), BERTopic           |
| AI Generation | Groq API — Llama 3.1 70B via LangChain               |
| Data Sources  | Domain, ABC News, RBA, ABS                           |
| Deployment    | Vercel (frontend), Render (backend)                  |

---

## Project Structure

```
├── backend/
│   ├── data/                  # Generated data files
│   ├── main.py                # FastAPI endpoints (7 REST routes)
│   ├── scraper.py             # Domain, ABC News, RBA, ABS scrapers
│   ├── nlp_pipeline.py        # spaCy NER + BERTopic topic modelling
│   ├── rag_pipeline.py        # LangChain + Groq brief generation and chat
│   ├── requirements.txt       # Python dependencies
│   ├── render.yaml            # Render deployment config
│   └── nixpacks.toml          # Build configuration
│
├── frontend/
│   ├── src/                   # React source files
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── vercel.json            # Vercel deployment config
│
└── .gitignore
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Groq API key](https://console.groq.com)

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp ../.env .env        # add your GROQ_API_KEY
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` — API requests are proxied to `http://localhost:8000`.

---

## How It Works

```
Web Sources          NLP Pipeline           AI Generation
(Domain, ABC,   →   spaCy NER +        →   LangChain +        →   Weekly Brief
 RBA, ABS)          BERTopic                Groq Llama 3.1 70B     + Chat
```

1. **Scrape** — Pulls live property news and data from multiple Melbourne sources
2. **Extract** — spaCy NER identifies suburbs, prices, and entities; BERTopic clusters themes
3. **Generate** — LangChain orchestrates a RAG pipeline using Groq to produce structured, agent-ready briefs
4. **Deliver** — React dashboard surfaces briefs, suburb analytics, and an AI chat interface

---

## Author

**Sanjana Kailasanathan**
[LinkedIn](https://linkedin.com/in/sanjana-kailasanathan) · [Portfolio](https://sanjanakailashds.lovable.app) · [GitHub](https://github.com/sanjana-kailash)
