from langgraph.graph import StateGraph, START, END

from app.graph.state import AgentState
from app.graph.nodes import (
    intake, planner, searcher, reader, organizer, summarizer, writer, critic,
)


def _route(state: AgentState) -> str:
    return "reader" if state.get("mode") == "links" else "planner"


def _after_critic(state: AgentState) -> str:
    # allow one revision at most
    if state.get("critique") != "OK" and state.get("revisions", 0) < 2:
        return "writer"
    return END


def build_graph():
    g = StateGraph(AgentState)
    for name, fn in [
        ("intake", intake), ("planner", planner), ("searcher", searcher),
        ("reader", reader), ("organizer", organizer), ("summarizer", summarizer),
        ("writer", writer), ("critic", critic),
    ]:
        g.add_node(name, fn)

    g.add_edge(START, "intake")
    g.add_conditional_edges("intake", _route, {"planner": "planner", "reader": "reader"})
    g.add_edge("planner", "searcher")
    g.add_edge("searcher", "reader")
    g.add_edge("reader", "organizer")
    g.add_edge("organizer", "summarizer")
    g.add_edge("summarizer", "writer")
    g.add_edge("writer", "critic")
    g.add_conditional_edges("critic", _after_critic, {"writer": "writer", END: END})
    return g.compile()