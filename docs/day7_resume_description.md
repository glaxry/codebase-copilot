# Day 7 Resume Description

## One-Line Project Summary

**Codebase Copilot: a local code-repository Agent built with Python and C++, supporting indexing, grounded Q&A, patch suggestions, and Python-vs-C++ retrieval benchmarking.**

## Resume Bullets

### Version A: Engineering-Focused

- Designed and implemented a local codebase Agent that supports repository indexing, chunk-level retrieval, grounded code Q&A, and patch-style suggestion generation.
- Built the Agent workflow in Python for repository scanning, chunking, prompt assembly, CLI orchestration, and optional OpenAI-compatible LLM integration.
- Implemented a native C++ vector retrieval core with cosine-similarity top-k search and exposed it to Python through `pybind11`.
- Added a benchmark suite comparing Python brute-force retrieval against the C++ retriever across `1k`, `10k`, `50k`, and `100k` synthetic vectors, producing reproducible performance tables for README and interviews.

### Version B: AI / Agent-Focused

- Built a lightweight Code Agent for local repositories, covering chunk-based indexing, retrieval-augmented prompting, grounded question answering, and patch suggestion generation.
- Reconstructed the retrieval index from persisted `metadata.json`, enabling a clean offline indexing flow and an online query flow without an external vector database.
- Integrated local deterministic synthesizers and an OpenAI-compatible LLM backend, supporting `local`, `llm`, and `auto` runtime modes.
- Improved retrieval quality by prioritizing source files over markdown notes, reranking query-relevant code chunks, and reducing near-duplicate contexts.

## Chinese Resume Notes

如果你想写成中文简历，可以直接压缩成下面这版：

- 设计并实现基于 `Python + C++` 的本地代码仓库 Agent，支持仓库索引、代码问答、修改建议和性能 benchmark。
- 使用 `Python` 完成仓库扫描、代码切块、Prompt 组装、CLI 编排与 LLM 接入，使用 `C++` 手写向量检索并通过 `pybind11` 与 Python 打通。
- 基于余弦相似度实现 top-k 暴力检索，并完成 Python 与 C++ 检索性能对比实验，在 `100k` 级向量数据上实现显著加速。
- 支持返回相关文件路径、代码片段和 patch 风格建议，提升代码定位与仓库理解效率。

## Resume Usage Advice

- If your target is backend / infrastructure: use Version A.
- If your target is AI engineering / Agent platform: use Version B.
- If the resume space is tight: keep the one-line summary plus the first three bullets.
