import math

from lib.similarity import (
    cluster_by_threshold,
    cosine,
    tfidf_vectors,
    tokenize,
)


# ---------------------------------------------------------------------------
# tokenize
# ---------------------------------------------------------------------------

def test_tokenize_lowercases_and_filters_short():
    assert tokenize("Toyota Prius is a HYBRID") == ["toyota", "prius", "hybrid"]


def test_tokenize_drops_stopwords():
    # "this", "is", "the", "a" are stopwords; "engine" should remain
    assert tokenize("this is the a engine") == ["engine"]


def test_tokenize_keeps_topical_terms():
    # Make sure we don't accidentally stopword domain terms
    out = tokenize("hybrid battery prius synergy drive")
    assert "hybrid" in out and "battery" in out and "prius" in out


def test_tokenize_strips_punctuation():
    assert tokenize("end. start! mid?") == ["end", "start", "mid"]


def test_tokenize_handles_empty():
    assert tokenize("") == []


# ---------------------------------------------------------------------------
# tfidf_vectors
# ---------------------------------------------------------------------------

def test_tfidf_empty_docs():
    assert tfidf_vectors([]) == []


def test_tfidf_term_in_all_docs_has_zero_idf():
    docs = [["hybrid"], ["hybrid"], ["hybrid"]]
    vecs = tfidf_vectors(docs)
    # IDF for term in all docs = log(3/3) = 0; term filtered out
    assert all("hybrid" not in v for v in vecs)


def test_tfidf_unique_term_has_high_weight():
    docs = [
        ["hybrid", "battery", "prius"],
        ["hybrid", "tesla", "model"],
    ]
    vecs = tfidf_vectors(docs)
    # "prius" only in doc 0 → IDF = log(2/1) = 0.693, present in vec[0]
    assert "prius" in vecs[0]
    assert vecs[0]["prius"] > 0


def test_tfidf_empty_doc_yields_empty_vector():
    docs = [["hybrid", "battery"], []]
    vecs = tfidf_vectors(docs)
    assert vecs[1] == {}


# ---------------------------------------------------------------------------
# cosine
# ---------------------------------------------------------------------------

def test_cosine_identical_vectors_is_one():
    a = {"x": 1.0, "y": 2.0}
    assert math.isclose(cosine(a, a), 1.0)


def test_cosine_disjoint_vectors_is_zero():
    a = {"x": 1.0}
    b = {"y": 1.0}
    assert cosine(a, b) == 0.0


def test_cosine_empty_returns_zero():
    assert cosine({}, {"a": 1.0}) == 0.0
    assert cosine({"a": 1.0}, {}) == 0.0


def test_cosine_partial_overlap_between_zero_and_one():
    a = {"x": 1.0, "y": 1.0}
    b = {"x": 1.0, "z": 1.0}
    sim = cosine(a, b)
    assert 0.0 < sim < 1.0


# ---------------------------------------------------------------------------
# cluster_by_threshold
# ---------------------------------------------------------------------------

def test_cluster_no_dupes_returns_empty():
    docs = [
        ["hybrid", "battery", "prius"],
        ["tesla", "model", "electric"],
        ["bicycle", "wheel", "frame"],
    ]
    vecs = tfidf_vectors(docs)
    assert cluster_by_threshold(vecs, 0.75) == []


def test_cluster_groups_near_duplicates():
    # Two docs with identical content should cluster at any reasonable threshold.
    # (When all docs share all terms, IDF=0 so we mix in unique terms.)
    docs = [
        ["hybrid", "battery", "prius", "shared", "shared", "shared"],
        ["hybrid", "battery", "prius", "shared", "shared", "shared"],
        ["tesla", "model", "electric", "different", "different", "different"],
    ]
    vecs = tfidf_vectors(docs)
    clusters = cluster_by_threshold(vecs, 0.5)
    assert len(clusters) == 1
    assert clusters[0]["members"] == [0, 1]
    assert clusters[0]["max_similarity"] > 0.5


def test_cluster_chains_via_connected_components():
    # A ~ B and B ~ C → all three cluster, even if A vs C alone is below threshold.
    docs = [
        ["alpha", "beta", "gamma", "delta"],
        ["alpha", "beta", "epsilon", "zeta"],
        ["epsilon", "zeta", "eta", "theta"],
        ["unrelated", "outsider", "different", "topic"],
    ]
    vecs = tfidf_vectors(docs)
    clusters = cluster_by_threshold(vecs, 0.1)
    members = [m for c in clusters for m in c["members"]]
    # 0,1,2 should chain together; 3 should not be in any cluster
    assert 3 not in members


def test_cluster_excludes_singletons():
    docs = [["a", "b", "c"], ["d", "e", "f"]]
    vecs = tfidf_vectors(docs)
    out = cluster_by_threshold(vecs, 0.99)
    # No pair meets 0.99 → no clusters returned (singletons filtered)
    assert out == []
