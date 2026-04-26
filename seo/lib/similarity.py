"""Stdlib TF-IDF + cosine + connected-components clustering for near-duplicate detection.

Designed for ~100 docs of ~1500 words each. O(n²) cosine is fine at that scale.
"""

import math
import re
from collections import Counter

# Common English stopwords. Topical/technical terms (e.g. "hybrid", "battery",
# "prius") deliberately not listed — they should drive similarity.
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "this", "that", "these", "those", "you", "she", "they",
    "what", "which", "who", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "nor", "not", "only",
    "own", "same", "than", "too", "very", "as", "if", "then", "else", "while",
    "their", "your", "our", "its", "his", "her", "them", "also", "just", "even",
    "still", "now", "well", "much", "many", "any", "one", "two", "three",
    "first", "second", "third", "would", "should", "could", "about",
})


def tokenize(text: str) -> list[str]:
    """Lowercase alnum tokens of length >= 3, stopwords removed."""
    return [
        t for t in re.findall(r"[a-z0-9]+", text.lower())
        if len(t) >= 3 and t not in _STOPWORDS
    ]


def tfidf_vectors(docs_tokens: list[list[str]]) -> list[dict[str, float]]:
    """Compute TF-IDF vectors. Empty docs map to empty dicts."""
    n = len(docs_tokens)
    if n == 0:
        return []

    df: Counter = Counter()
    for tokens in docs_tokens:
        for term in set(tokens):
            df[term] += 1
    idf = {term: math.log(n / count) for term, count in df.items()}

    vectors: list[dict[str, float]] = []
    for tokens in docs_tokens:
        if not tokens:
            vectors.append({})
            continue
        tf = Counter(tokens)
        total = sum(tf.values())
        vec = {term: (count / total) * idf[term] for term, count in tf.items() if idf[term] > 0}
        vectors.append(vec)
    return vectors


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity of two sparse TF-IDF vectors. Returns 0.0 for empty inputs."""
    if not a or not b:
        return 0.0
    common = a.keys() & b.keys()
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def cluster_by_threshold(
    vectors: list[dict[str, float]], threshold: float,
) -> list[dict]:
    """Group docs by connected component over edges with cosine >= threshold.

    Returns dicts with `members` (sorted indices) and `max_similarity` per cluster.
    Singletons (clusters of 1) are excluded.
    """
    n = len(vectors)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    pairs: list[tuple[int, int, float]] = []
    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine(vectors[i], vectors[j])
            if sim >= threshold:
                pairs.append((i, j, sim))
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    max_sim_per_root: dict[int, float] = {}
    for i, _, sim in pairs:
        root = find(i)
        if sim > max_sim_per_root.get(root, 0.0):
            max_sim_per_root[root] = sim

    out: list[dict] = []
    for root, members in groups.items():
        if len(members) > 1:
            out.append({
                "members": sorted(members),
                "max_similarity": max_sim_per_root.get(root, 0.0),
            })
    out.sort(key=lambda g: -g["max_similarity"])
    return out
