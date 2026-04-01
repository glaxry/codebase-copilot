# Codebase Copilot 架构图讲解

对应架构图文件：

- `docs/codebase_copilot_architecture.html`

---

## 1. 项目一句话概述

`Codebase Copilot` 是一个基于 `Python + C++` 的本地代码仓库 Agent。

- `Python` 负责命令行入口、仓库扫描、切块、Prompt 组装、问答/修改建议工作流
- `C++` 负责底层向量检索
- 两者通过 `pybind11` 打通

这个项目的核心目标不是做一个通用文档问答，而是做一个**面向代码仓库理解、问答、修改建议和性能对比**的本地 Agent。

---

## 2. 这张架构图怎么读

这张图从左到右、从上到下可以分成 7 个部分：

1. `Entry Layer`
2. `Offline Index Pipeline`
3. `Online QA and Patch`
4. `Native Retrieval`
5. `Benchmark Subsystem`
6. `Core Modules`
7. `Project Outputs`

其中：

- 左上部分表示用户怎么进入系统
- 中上部分表示索引和在线问答/修改建议的主流程
- 右上部分表示底层 C++ 检索能力
- 下半部分表示 benchmark、公共模块和最终产物

---

## 3. Entry Layer：系统入口层

这一层主要回答一个问题：**用户是怎么使用这个项目的？**

入口统一在：

- `python/main.py`

支持的命令包括：

- `scan`
- `chunk`
- `index`
- `ask`
- `patch`
- `benchmark`

这里的设计意图很明确：

- 所有功能都从一个统一 CLI 进入，便于演示
- 项目展示时可以直接按 `index -> ask -> patch -> benchmark` 这条链路讲清楚

你可以把这一层理解成整个系统的“控制台”。

---

## 4. Offline Index Pipeline：离线索引构建流程

这一部分是项目的“离线准备阶段”，主要目标是把仓库内容变成后续可检索的数据。

对应流程如下：

### 4.1 RepositoryLoader

文件：

- `python/codebase_copilot/repo_loader.py`

职责：

- 扫描仓库文件
- 过滤无关目录和不支持的文件
- 处理文本编码
- 输出规范化的 `RepoFile`

也就是说，这一步解决的是“哪些文件值得进入索引”的问题。

### 4.2 CodeChunker

文件：

- `python/codebase_copilot/chunker.py`

职责：

- 把大文件切成按行滑动的 chunk
- 支持 `chunk_size` 和 `chunk_overlap`
- 为每个 chunk 记录路径、语言、起止行号、文本内容

这一步解决的是“代码太长，不能整文件直接喂给检索和模型”的问题。

### 4.3 HashingEmbedder

文件：

- `python/codebase_copilot/embedder.py`

职责：

- 使用本地确定性的 hashing embedding
- 不依赖外部 embedding 服务
- 把 chunk 文本变成固定维度的向量

这样做的好处是：

- 项目闭环完整
- 离线可运行
- 便于 benchmark 和复现

### 4.4 build_index()

文件：

- `python/codebase_copilot/pipeline.py`

职责：

- 串联 `RepositoryLoader -> CodeChunker -> HashingEmbedder`
- 调用 `VectorRetriever` 验证索引可写入
- 生成 `metadata.json`

最终输出：

- `data/metadata.json`

这里有一个很重要的设计点：

- `metadata.json` 存的是 **chunk 元信息**
- 并不直接持久化底层 native retriever
- 在线阶段再根据这些 chunk 重新构建内存检索器

这个设计让项目更简单，也更容易调试和解释。

---

## 5. Online QA and Patch：在线问答与修改建议流程

这一部分是最核心的 Agent 主流程。

### 5.1 元数据加载

文件：

- `python/codebase_copilot/agent.py`

流程：

- 从 `metadata.json` 读取 chunk 记录
- 恢复 `LoadedIndex`
- 重新用 `HashingEmbedder` 生成 chunk 向量
- 把这些向量重新塞进 `VectorRetriever`

也就是说，在线阶段不是直接读取一个现成数据库，而是：

- 先读元数据
- 再在内存中恢复检索结构

### 5.2 CodebaseQAAgent

文件：

- `python/codebase_copilot/agent.py`

这是在线阶段的核心类，负责：

- `retrieve()`
- `ask()`
- `patch()`

其中 `retrieve()` 不只是简单向量搜索，还包含了额外的工程策略：

- query-aware rerank
- 源码优先、文档降权
- 测试文件按需命中
- 相似 chunk 去重
- top-k 上下文多样化选择

这说明这个项目不是“只做 embedding + top-k”那么简单，而是在 retrieval 之后做了面向代码场景的二次优化。

### 5.3 Prompt Builder

文件：

- `python/codebase_copilot/prompt.py`

职责：

- 组装问答 prompt
- 组装 patch suggestion prompt
- 把检索到的 chunk 按统一格式拼成上下文

这一层的意义在于：把“搜索到的代码片段”转换成“模型或本地 answerer 能消费的结构化输入”。

### 5.4 Answer / Patch Synthesizer

项目里有两条输出路径：

#### 本地 deterministic 路径

文件：

- `python/codebase_copilot/agent.py`

包括：

- `LocalAnswerSynthesizer`
- `LocalPatchSynthesizer`

优点：

- 没有 API key 也能运行
- 方便测试
- 结果可控，便于做工程验收

#### LLM 路径

文件：

- `python/codebase_copilot/llm.py`

职责：

- 调 OpenAI-compatible 接口
- 支持 `ask` 和 `patch`
- 在 `auto` 模式下失败时回退到本地 synthesizer

所以整个系统的在线执行逻辑是：

- 先检索
- 再组 prompt
- 最后走 `local` 或 `llm`

---

## 6. Native Retrieval：底层 C++ 检索层

这一层是项目最能体现“跨语言工程能力”的部分。

### 6.1 Python Wrapper

文件：

- `python/codebase_copilot/retriever.py`

职责：

- 暴露 `VectorRetriever`
- 做 NumPy 向量格式转换
- 调用 native module `_vector_index`

### 6.2 pybind11 Bridge

文件：

- `cpp/src/binding.cpp`

职责：

- 把 C++ 的 `VectorIndex` 暴露给 Python
- 支持：
  - `add_item`
  - `add_items`
  - `search`
  - `size`
  - `dimension`

### 6.3 C++ VectorIndex

文件：

- `cpp/include/vector_index.h`
- `cpp/src/vector_index.cpp`

职责：

- 保存向量条目
- 计算 cosine similarity
- 用最小堆维护 top-k
- 返回最相关结果

这个部分的意义在于：

- Python 负责“业务编排”
- C++ 负责“性能敏感”的检索循环

这也是 Day 6 benchmark 能成立的基础。

---

## 7. Benchmark Subsystem：性能对比子系统

文件：

- `python/codebase_copilot/benchmark.py`

这一层主要回答一个问题：

**自己写的 C++ 检索到底比 Python baseline 快多少？**

### 7.1 数据生成

- 生成随机单位向量
- 构造 synthetic dataset 和 query

### 7.2 Python baseline

- `PythonBruteForceRetriever`
- 纯 Python 循环逐条算 cosine
- 作为对照组

### 7.3 C++ benchmark

- 调用 `VectorRetriever`
- 实际走 native 检索路径

### 7.4 对比输出

- 比较 Python 平均查询耗时
- 比较 C++ 平均查询耗时
- 计算 speedup
- 检查 top-k 结果是否一致
- 生成 markdown 表格和 benchmark 报告

这部分非常重要，因为它把“我写了 C++ 检索”变成了“我有量化结果证明它更快”。

---

## 8. Core Modules：公共核心模块

图里右下角的 `Core Modules` 表示一些被多个子系统共用的基础模块。

主要包括：

- `models.py`
- `config.py`
- `prompt.py`
- `llm.py`
- `agent.py`
- `retriever.py`

它们分别承担：

- 数据结构定义
- 默认配置管理
- Prompt 组装
- LLM 调用
- Agent 工作流
- 检索接口封装

这部分体现的是项目的模块化组织，而不是把所有逻辑都堆在一个脚本里。

---

## 9. Project Outputs：最终输出层

这一层表示项目最终能给用户或者评审看到什么。

主要输出包括：

- `metadata.json`
- grounded answer
- patch suggestion
- benchmark report
- README
- docs 版本说明

也就是说，这个项目不是只停留在代码层，而是已经具备：

- 功能闭环
- 文档闭环
- 测试闭环
- benchmark 闭环

---

## 10. 这张图最值得讲的 4 个设计点

如果你要讲给老师、面试官或者答辩听，最值得强调这四点：

### 10.1 Python + C++ 分层明确

- Python 负责 workflow
- C++ 负责高性能检索

这体现了“用合适语言做合适事情”的工程思路。

### 10.2 离线索引 / 在线检索分离

- 离线阶段扫描仓库、切 chunk、生成元数据
- 在线阶段根据元数据恢复检索器并回答问题

这让整个系统结构清晰，也便于后续扩展。

### 10.3 不只做问答，还支持 patch suggestion

相比只做 `ask`，`patch` 说明项目已经从“代码理解”进一步走向“修改建议”，更接近真实 Agent 场景。

### 10.4 有 benchmark，不只是功能演示

很多项目只能说“我写了 C++ 检索”，但这个项目还能用 Day 6 的数据证明：

- Python baseline 慢多少
- C++ 提升多少
- top-k 是否一致

这会让项目更有说服力。

---

## 11. 你可以怎么口头讲这张图

下面是一段比较适合展示时直接说的讲法。

### 1 分钟版本

> 这张图展示的是我这个 Codebase Copilot 的整体架构。最左边是统一的 CLI 入口，所有功能都从 `python/main.py` 进入，包括 scan、index、ask、patch 和 benchmark。  
> 上半部分左侧是离线索引流程：先用 `RepositoryLoader` 扫描仓库，再用 `CodeChunker` 切代码片段，用 `HashingEmbedder` 做本地向量化，最后由 `pipeline.py` 生成 `metadata.json`。  
> 中间部分是在线问答和修改建议流程：系统从 `metadata.json` 恢复 chunk 信息，在 `CodebaseQAAgent` 里重建内存检索器，做 query-aware rerank，然后组装 prompt，最后走本地 deterministic answerer 或 OpenAI-compatible LLM。  
> 右上部分是底层 C++ 检索模块，我用 `pybind11` 把 `VectorIndex` 暴露给 Python，底层实现是 cosine similarity 加 top-k heap。  
> 下半部分是 benchmark 系统，我用同一份随机向量数据分别跑 Python brute-force baseline 和 C++ retriever，最终生成 benchmark 表，证明 native 检索在查询延迟上有明显提升。

### 2 分钟版本

> 这个项目我故意拆成了 Python workflow 和 C++ retrieval 两层。Python 更适合快速做 Agent 编排、CLI、Prompt 和问答流程，C++ 更适合做性能敏感的向量检索。  
> 在离线阶段，系统先扫描本地仓库文件，过滤无关路径，然后把代码按行切成有 overlap 的 chunk，再用本地 hashing embedding 把 chunk 变成向量，并输出 `metadata.json`。这里我没有直接持久化底层索引，而是只保存 chunk 元数据，这样结构更简单，也更方便调试。  
> 在在线阶段，`ask` 和 `patch` 都由 `CodebaseQAAgent` 驱动。它会加载元数据、在内存里重建 native retriever、执行 top-k 搜索，并额外做 source-first rerank、文档降权和相似 chunk 去重。然后通过 `prompt.py` 组装上下文，最后要么用本地 deterministic synthesizer，要么走兼容 OpenAI API 的 LLM。  
> 除了问答，我还实现了 patch suggestion，这样系统不仅能解释代码，还能给出 grounded 的修改建议。  
> 最后我做了 benchmark 子系统，用 Python brute-force 作为 baseline，对比 C++ 检索的平均查询延迟，并验证 top-k 结果一致。这一部分是为了让这个项目不仅“能跑”，而且“有量化证明”。  

---

## 12. 总结

这张架构图想表达的不是“模块很多”，而是三件事：

1. 这个项目已经形成完整闭环：`index -> ask -> patch -> benchmark`
2. 它是一个明确分层的 `Python + C++` 工程，而不是单脚本 demo
3. 它既有功能输出，也有性能量化结果

如果你后面还要继续扩展，这张图也很方便往下接：

- 更强的 embedding
- 更复杂的索引结构，比如 HNSW
- 自动 patch 应用
- Web UI
- 多轮 Agent 规划

