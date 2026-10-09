# import torch
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import GROQ_API_KEY, GROQ_MODEL, LOCAL_SUMMARIZER_MODEL

_tok = None
_model = None  # loaded on first use, so the app starts fast


def _get_local():
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    global _tok, _model
    if _model is None:
        _tok = AutoTokenizer.from_pretrained(LOCAL_SUMMARIZER_MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(LOCAL_SUMMARIZER_MODEL)
        _model.eval()
    return _tok, _model


def _chunk(text: str, max_words: int = 600) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def summarize_local(text: str) -> str:
    import torch
    """Summarize one source with the local model (map-reduce for long text)."""
    tok, model = _get_local()
    parts = []
    for chunk in _chunk(text):
        if len(chunk.split()) < 40:      # too short to summarize
            parts.append(chunk)
            continue
        inputs = tok(chunk, return_tensors="pt", truncation=True, max_length=1024)
        with torch.no_grad():
            ids = model.generate(
                **inputs, max_length=120, min_length=30,
                num_beams=4, do_sample=False, early_stopping=True,
            )
        parts.append(tok.decode(ids[0], skip_special_tokens=True))
    return " ".join(parts)


_llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.2)

_synth_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You write concise, accurate briefs using ONLY the numbered sources given. "
     "Cite sources inline like [1], [2]. Do not add facts not in the sources. "
     "Length: {length}. Style: {style}."),
    ("human", "Topic: {topic}\n\nSources:\n{sources}\n\nWrite the brief."),
])


def synthesize_groq(topic: str, summaries: list[tuple[str, str]], length: str, style: str) -> str:
    """summaries = [(url, summary_text), ...] -> final cited brief."""
    numbered = "\n".join(f"[{i+1}] ({url}) {text}" for i, (url, text) in enumerate(summaries))
    chain = _synth_prompt | _llm
    return chain.invoke(
        {"topic": topic, "sources": numbered, "length": length, "style": style}
    ).content

_sum_prompt = ChatPromptTemplate.from_messages([
    ("system", "Summarize the text in 3-5 factual sentences. Use only the text. No preamble."),
    ("human", "{text}"),
])


def summarize_groq(text: str) -> str:
    return (_sum_prompt | _llm).invoke({"text": text}).content.strip()