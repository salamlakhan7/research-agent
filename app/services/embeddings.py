from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

from app.config import EMBEDDING_MODEL, DEDUP_THRESHOLD

_model = SentenceTransformer(EMBEDDING_MODEL)


@dataclass
class Source:
    url: str
    title: str
    text: str


def embed(texts: list[str]) -> np.ndarray:
    # normalized vectors, so cosine similarity = dot product
    return _model.encode(texts, normalize_embeddings=True)


def deduplicate(sources: list[Source], threshold: float = DEDUP_THRESHOLD) -> list[Source]:
    """Drop sources that are near-identical to one already kept."""
    if not sources:
        return []
    vecs = embed([s.text[:2000] for s in sources])
    kept: list[int] = []
    for i in range(len(sources)):
        if all(float(vecs[i] @ vecs[j]) < threshold for j in kept):
            kept.append(i)
    return [sources[i] for i in kept]


def rank_by_relevance(query: str, sources: list[Source], top_k: int = 5) -> list[tuple[Source, float]]:
    """Return the top_k sources most relevant to the query, with scores."""
    if not sources:
        return []
    q = embed([query])[0]
    docs = embed([s.text[:2000] for s in sources])
    scores = docs @ q
    order = np.argsort(scores)[::-1][:top_k]
    return [(sources[i], float(scores[i])) for i in order]


def cluster_sources(sources: list[Source], n_clusters: int = 3) -> dict[int, list[Source]]:
    """Group sources into themes."""
    if len(sources) <= n_clusters:
        return {i: [s] for i, s in enumerate(sources)}
    vecs = embed([s.text[:2000] for s in sources])
    labels = KMeans(n_clusters=n_clusters, n_init=10, random_state=42).fit_predict(vecs)
    groups: dict[int, list[Source]] = {}
    for s, label in zip(sources, labels):
        groups.setdefault(int(label), []).append(s)
    return groups