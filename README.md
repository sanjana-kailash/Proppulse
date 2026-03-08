# PropPulse — Melbourne Property Market Intelligence

AI-driven weekly market brief generator for Melbourne real estate agents.

## Stack
- **Frontend**: React + Vite + Tailwind CSS + Recharts
- **Backend**: Python + FastAPI
- **NLP**: spaCy (NER) + BERTopic (topic modelling)
- **AI**: Groq API (Llama 3.1 70B) via LangChain

## Quick Start

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

Frontend runs on http://localhost:5173 — API requests are proxied to http://localhost:8000.

## Project Structure
```
backend/
  main.py          — FastAPI endpoints
  scraper.py       — Domain, ABC News, RBA, ABS scrapers
  nlp_pipeline.py  — spaCy NER + BERTopic
  rag_pipeline.py  — LangChain + Groq brief generation & chat
  data/suburbs/    — JSON data files per suburb
  data/briefs/     — Generated briefs by week

frontend/src/
  pages/           — DashboardPage, BriefPage, SuburbPage, SettingsPage
  components/      — Dashboard, SuburbCard, WeeklyBrief, ChatAssistant, TrendChart, Settings
```
