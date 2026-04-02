# Embedding Comparison

This report compares the existing hashing embedder with the new semantic embedder on a small synthetic codebase that was designed to surface semantic synonym gaps.

- semantic model: `all-MiniLM-L6-v2`
- query count: 5
- hashing top-1 hits: 2/5
- semantic top-1 hits: 5/5

## Results

| Query | Expected Top-1 | Hashing Top-1 | Semantic Top-1 | Hashing Match | Semantic Match | Note |
| --- | --- | --- | --- | :---: | :---: | --- |
| How do we authenticate a user? | src/auth/login.py | src/auth/login.py | src/auth/login.py | yes | yes | semantic synonym: authenticate -> login |
| Where are runtime settings loaded? | src/config/runtime.py | src/auth/login.py | src/config/runtime.py | no | yes | semantic synonym: settings -> config |
| Which file performs similarity lookup over vectors? | src/search/vector_search.py | src/auth/login.py | src/search/vector_search.py | no | yes | semantic synonym: lookup -> search |
| Where is the application entrypoint? | src/cli/entry.py | src/cli/entry.py | src/cli/entry.py | yes | yes | semantic synonym: entrypoint -> command entry |
| How are access rights checked? | src/security/permission.py | src/auth/login.py | src/security/permission.py | no | yes | semantic synonym: access rights -> permission |

## Takeaways

- hashing is lightweight and deterministic, but it relies heavily on exact token overlap
- semantic embeddings handle synonym-style queries much better when the wording differs from the code tokens
- the native C++ retriever remains reusable because it only depends on vectors, not on how they were produced