import re

from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL

CURATED = [
    {"category": "AI & Technology", "topic": "How retrieval-augmented generation reduces LLM hallucinations"},
    {"category": "AI & Technology", "topic": "Impact of generative AI on software engineering jobs"},
    {"category": "AI & Technology", "topic": "Risks and safeguards for autonomous AI agents"},
    {"category": "Health & Science", "topic": "Risks of using AI in healthcare"},
    {"category": "Health & Science", "topic": "How mRNA technology is expanding beyond vaccines"},
    {"category": "Health & Science", "topic": "Effects of sleep deprivation on cognitive performance"},
    {"category": "Business & Careers", "topic": "Remote work productivity: what the research shows"},
    {"category": "Business & Careers", "topic": "Skills in demand for AI and data roles"},
    {"category": "Business & Careers", "topic": "How startups validate product ideas quickly"},
    {"category": "World & Society", "topic": "Renewable energy storage technologies compared"},
    {"category": "World & Society", "topic": "Cybersecurity threats facing small businesses"},
    {"category": "World & Society", "topic": "The future of online education and AI tutoring"},
]

_llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.7)


def suggest_topics(recent: list[str]) -> list[str]:
    prompt = (
        "A user recently researched these subjects:\n- " + "\n- ".join(recent) +
        "\n\nSuggest 5 specific, different follow-up research topics they might want next. "
        "Return only the topics, one per line, no numbering, each under 12 words."
    )
    out = _llm.invoke(prompt).content
    topics = [re.sub(r"^[\s\-\d.)*]+", "", l).strip() for l in out.splitlines() if l.strip()]
    return topics[:5]

def related_questions(report: str) -> list[str]:
    out = _llm.invoke(
        "Based on this research brief, suggest 3 specific follow-up questions a curious reader would ask next. "
        "Return only the questions, one per line, no numbering.\n\n" + report
    ).content
    qs = [re.sub(r"^[\s\-\d.)*]+", "", l).strip() for l in out.splitlines() if l.strip()]
    return qs[:3]