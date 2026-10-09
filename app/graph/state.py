from typing import TypedDict


class AgentState(TypedDict, total=False):
    mode: str            # "topic" or "links"
    input: str           # user's topic or pasted links
    length: str
    style: str
    topic: str
    urls: list
    snippets: dict       # url -> (title, search snippet), fallback text
    sub_questions: list
    sources: list        # list[Source]
    failed: dict         # url -> reason
    summaries: list      # [(url, summary)]
    report: str
    critique: str
    revisions: int