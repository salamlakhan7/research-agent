# Research Agent

An agentic research tool. Give it a topic or a list of links, and it returns a short brief where every claim is cited.

**Live demo:** [add link after deploy]

## How it works
Intake -> Planner -> Searcher -> Reader -> Organizer -> Summarizer -> Writer -> Critic

- **Planner/Searcher:** breaks a topic into questions and searches the web (Tavily)
- **Reader:** loads web pages, PDFs, and YouTube transcripts; unreadable links are reported, never silently skipped
- **Organizer:** Sentence Transformer embeddings remove duplicates, rank relevance, and cluster sources into themes
- **Summarizer:** Groq LLM in demo mode, or a local DistilBART transformer in local mode
- **Writer/Critic:** writes a brief using only the numbered sources, then checks each claim and requests a revision if needed

## Tech stack
LangChain, LangGraph, FastAPI, Sentence Transformers, Hugging Face Transformers, Groq, Tavily, SQLite, HTML + Tailwind + Three.js

## Features
- Topic mode and Links mode
- Guest try (one free brief), then signup; JWT auth in HttpOnly cookies, bcrypt password hashing
- Per-user history, daily usage limit
- Streaming pipeline progress, Markdown export

## Run locally
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env      (then add your keys)
    uvicorn app.main:app --reload

## Environment variables
GROQ_API_KEY, TAVILY_API_KEY, JWT_SECRET, DEMO_MODE (true = Groq summarizer, false = local DistilBART)

## Demo mode vs local mode
Demo mode keeps the public site fast. Local mode runs the DistilBART transformer on CPU and is slower, kept for experiments and benchmarking.

## Screenshots
[add landing page, dashboard, and a sample brief]

## Author
Abdul Salam | github.com/salamlakhan7 | linkedin.com/in/abdul-salam-501b2025b