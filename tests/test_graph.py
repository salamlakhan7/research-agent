from app.graph.builder import build_graph

graph = build_graph()

print("=== LINKS MODE ===")
r = graph.invoke({
    "mode": "links",
    "input": "https://en.wikipedia.org/wiki/Large_language_model https://arxiv.org/pdf/1706.03762",
    "length": "short",
    "style": "bullets",
})
print(r["report"])
print("critique:", r["critique"], "| revisions:", r["revisions"])

print("\n=== TOPIC MODE ===")
r = graph.invoke({
    "mode": "topic",
    "input": "Risks of using AI in healthcare",
    "length": "short",
    "style": "bullets",
})
print(r["report"])
print("sub-questions:", r["sub_questions"])