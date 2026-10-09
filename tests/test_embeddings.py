from app.services.embeddings import Source, deduplicate, rank_by_relevance, cluster_sources

sources = [
    Source("a.com", "LLMs in hospitals", "Large language models help doctors summarize patient notes and reduce paperwork."),
    Source("b.com", "LLMs in hospitals (copy)", "Large language models help doctors summarize patient notes and reduce paperwork."),
    Source("c.com", "AI risks", "Hallucinations and privacy leaks are serious risks when using AI in healthcare."),
    Source("d.com", "Regulation", "The FDA and EU are drafting rules for AI medical devices and clinical software."),
    Source("e.com", "Cooking tips", "Simmer the tomato sauce for an hour for a richer flavor."),
]

unique = deduplicate(sources)
print("After dedup:", [s.url for s in unique])

for s, score in rank_by_relevance("risks of AI in healthcare", unique, top_k=3):
    print(f"{score:.2f}  {s.url}")

print({k: [s.url for s in v] for k, v in cluster_sources(unique, 2).items()})