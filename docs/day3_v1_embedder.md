# Day 3 - Version 1: Local Embedder

## Goal

Add a deterministic embedding layer so Day 3 can build an index without relying on remote APIs.

## What This Version Contains

- `HashingEmbedder` for local text-to-vector conversion
- single-text and batch embedding interfaces
- deterministic token hashing with L2 normalization
- a runnable similarity test for the embedder

## Design Notes

- this embedder is intentionally lightweight and dependency-free beyond `numpy`
- the implementation uses feature hashing so the same input always maps to the same vector
- vectors are normalized so cosine similarity works naturally with the C++ retriever

## Thought Process

- the project plan allows a local lightweight embedding strategy
- a deterministic local embedder keeps Day 3 unblocked and makes tests stable
- the embedder is designed as a replaceable module, so a future API or sentence-transformers backend can swap in later without changing the index pipeline

## Test

Run:

```powershell
python test_embedder.py
```

The test verifies output shape, batch embedding, normalization, and that two similar login-related texts score higher than an unrelated retrieval text.

## Next Step

Connect chunk embeddings to the C++ retriever, save `metadata.json`, and expose a real `index` command.
