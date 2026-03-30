from __future__ import annotations

import numpy as np

from codebase_copilot.embedder import HashingEmbedder


def run_embedder_test() -> tuple[float, float]:
    embedder = HashingEmbedder(dimension=128)

    text_a = "def login(user_name, password): return user_name"
    text_b = "def login(account_name, password): return account_name"
    text_c = "vector search uses cosine similarity for retrieval"

    vector_a = embedder.embed_text(text_a)
    vector_b = embedder.embed_text(text_b)
    vector_c = embedder.embed_text(text_c)
    matrix = embedder.embed_texts([text_a, text_b, text_c])

    score_ab = float(np.dot(vector_a, vector_b))
    score_ac = float(np.dot(vector_a, vector_c))

    assert vector_a.shape == (128,)
    assert matrix.shape == (3, 128)
    assert score_ab > score_ac
    assert np.isclose(np.linalg.norm(vector_a), 1.0)

    return score_ab, score_ac


def main() -> int:
    score_ab, score_ac = run_embedder_test()
    print("Embedder test passed.")
    print(f"similar_login_score={score_ab:.6f}")
    print(f"different_topic_score={score_ac:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
