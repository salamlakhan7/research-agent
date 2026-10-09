import re

from langchain_groq import ChatGroq
from tavily import TavilyClient

#from app.config import GROQ_API_KEY, GROQ_MODEL, TAVILY_API_KEY
from concurrent.futures import ThreadPoolExecutor
from app.graph.state import AgentState
from app.services.embeddings import Source, deduplicate, rank_by_relevance, cluster_sources
from app.services.loaders import load_many
# from app.services.summarizer import summarize_local, synthesize_groq
from app.config import GROQ_API_KEY, GROQ_MODEL, TAVILY_API_KEY, DEMO_MODE
from app.services.summarizer import summarize_local, summarize_groq, synthesize_groq

_llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.2)
URL_RE = re.compile(r"https?://[^\s,;]+")


def intake(state: AgentState) -> dict:
    text = state["input"].strip()
    if state.get("mode") == "links":
        return {"urls": URL_RE.findall(text), "topic": "the provided sources", "revisions": 0}
    return {"topic": text, "revisions": 0}


def planner(state: AgentState) -> dict:
    msg = _llm.invoke(
        "Break this research topic into 3 specific web-search questions. "
        "Return only the questions, one per line, no numbering.\n\n"
        f"Topic: {state['topic']}"
    ).content
    qs = [re.sub(r"^[\s\-\d.)]+", "", l).strip() for l in msg.splitlines() if l.strip()]
    return {"sub_questions": qs[:3] or [state["topic"]]}


def searcher(state: AgentState) -> dict:
    client = TavilyClient(api_key=TAVILY_API_KEY)
    urls, snippets = [], {}
    for q in state["sub_questions"]:
        for r in client.search(query=q, max_results=3).get("results", []):
            if r["url"] not in snippets:
                urls.append(r["url"])
                snippets[r["url"]] = (r.get("title", ""), r.get("content", ""))
    return {"urls": urls, "snippets": snippets}


def reader(state: AgentState) -> dict:
    sources, failed = load_many(state["urls"])
    snippets = state.get("snippets", {})
    for url in list(failed):                      # fall back to the search snippet
        title, content = snippets.get(url, ("", ""))
        if len(content) >= 100:
            sources.append(Source(url, title or url, content))
            del failed[url]
    return {"sources": sources, "failed": failed}


def organizer(state: AgentState) -> dict:
    sources = deduplicate(state["sources"])
    if state.get("mode") == "topic" and sources:
        ranked = rank_by_relevance(state["topic"], sources, top_k=6)
        sources = [s for s, _ in ranked]
        groups = cluster_sources(sources, n_clusters=3)
        sources = [s for g in groups.values() for s in g]   # related sources sit together
    return {"sources": sources}


# def summarizer(state: AgentState) -> dict:
def summarizer(state: AgentState) -> dict:
    srcs = state["sources"]
    if DEMO_MODE:   # Groq, parallel: seconds instead of minutes
        with ThreadPoolExecutor(max_workers=4) as ex:
         texts = list(ex.map(lambda s: summarize_groq(s.text[:6000]), srcs))
    else:          # local DistilBART transformer
         texts = [summarize_local(s.text[:6000]) for s in srcs]
    return {"summaries": [(s.url, t) for s, t in zip(srcs, texts)]}


def writer(state: AgentState) -> dict:
    summaries = state.get("summaries", [])
    if not summaries:
        return {"report": "No readable sources were found.", "revisions": state.get("revisions", 0) + 1}

    style = state["style"]
    if state.get("critique") and state["critique"] != "OK":
        style += f". Fix this problem from the previous draft: {state['critique']}"

    text = synthesize_groq(state["topic"], summaries, state["length"], style)
    text = re.sub(r"【(\d+)】", r"[\1]", text)                 # normalize citation brackets

    # refs = "\n".join(f"[{i+1}] {url}" for i, (url, _) in enumerate(summaries))
    # text += f"\n\n**Sources**\n{refs}"
    refs = "\n".join(f"- [{i+1}] {url}" for i, (url, _) in enumerate(summaries))
    text += f"\n\n**Sources**\n\n{refs}"
    if state.get("failed"):
        text += "\n\n**Could not read:**\n" + "\n".join(f"- {u} ({r})" for u, r in state["failed"].items())
    return {"report": text, "revisions": state.get("revisions", 0) + 1}


def critic(state: AgentState) -> dict:
    if not state.get("summaries"):
        return {"critique": "OK"}
    src = "\n".join(f"[{i+1}] {t}" for i, (_, t) in enumerate(state["summaries"]))
    verdict = _llm.invoke(
        "Check this brief against the sources. Reply exactly 'OK' if every claim is "
        "supported by the sources and carries a citation. Otherwise reply with ONE short "
        f"sentence naming the main problem.\n\nSOURCES:\n{src}\n\nBRIEF:\n{state['report']}"
    ).content.strip()
    return {"critique": "OK" if verdict.upper().startswith("OK") else verdict}