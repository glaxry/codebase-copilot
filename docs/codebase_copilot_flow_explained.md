# Codebase Copilot 流程图讲解

对应流程图文件：

- `docs/codebase_copilot_flow.html`

---

## 1. 这张图和架构图有什么区别

前面那张 `architecture` 图更强调的是：

- 模块分层
- 组件职责
- 系统由哪些部分组成

这张 `flow` 图更强调的是：

- 命令是怎么进入系统的
- 数据是怎么流动的
- 每条主流程是怎么串起来的

所以你可以这样理解：

- `architecture` 看“系统长什么样”
- `flow` 看“系统怎么跑起来”

---

## 2. 整体阅读方式

这张流程图主要分成 5 个大块：

1. `入口层`
2. `离线索引流程`
3. `在线问答流程`
4. `修改建议流程`
5. `Benchmark 流程`

建议阅读顺序是：

1. 先看最左边统一入口
2. 再看 `index`
3. 再看 `ask`
4. 再看 `patch`
5. 最后看 `benchmark`

这其实也是项目最适合演示的顺序。

---

## 3. 入口层：所有能力都从 main.py 进入

入口统一在：

- `python/main.py`

它负责解析 CLI 参数，并把请求分发到不同命令：

- `scan`
- `chunk`
- `index`
- `ask`
- `patch`
- `benchmark`

这层的意义是：

- 项目对外只有一个统一入口
- 所有能力都可以从终端复现
- 演示和测试都很方便

也就是说，`main.py` 是整个项目的调度中心。

---

## 4. 离线索引流程：index 是如何生成 metadata.json 的

这条流程对应的是：

```powershell
python python/main.py index --repo . --output data/metadata.json
```

它的主要步骤如下。

### 4.1 RepositoryLoader

文件：

- `python/codebase_copilot/repo_loader.py`

作用：

- 扫描仓库
- 跳过无关目录和不支持的文件
- 读取文本内容
- 输出标准化的 `RepoFile`

这一步是为了保证只有“值得分析的代码文件”进入后续流程。

### 4.2 CodeChunker

文件：

- `python/codebase_copilot/chunker.py`

作用：

- 按行切 chunk
- 支持 overlap
- 给每个 chunk 保留路径、语言、起止行号和文本

这是为了把仓库内容变成适合检索的粒度。

### 4.3 HashingEmbedder

文件：

- `python/codebase_copilot/embedder.py`

作用：

- 为每个 chunk 生成本地 embedding
- 不依赖外部 embedding 服务
- 保持可复现、可离线运行

### 4.4 VectorRetriever

文件：

- `python/codebase_copilot/retriever.py`

作用：

- 把 embedding 写入到底层 native retriever
- 验证向量索引链路是通的

### 4.5 build_index()

文件：

- `python/codebase_copilot/pipeline.py`

作用：

- 串联前面所有步骤
- 最终输出 `metadata.json`

这里有个关键点：

- `metadata.json` 存的是 **chunk 元数据**
- 不是直接把整个 native index 序列化下来

这样设计更简单，也更适合项目讲解。

---

## 5. 在线问答流程：ask 是怎么工作的

这条流程对应的是：

```powershell
python python/main.py ask "Where is the application entry point?" --index data/metadata.json
```

它的主链路如下。

### 5.1 读取 metadata

文件：

- `python/codebase_copilot/agent.py`

首先系统会加载 `metadata.json`，恢复 chunk 信息和索引配置。

### 5.2 CodebaseQAAgent 重建检索器

文件：

- `python/codebase_copilot/agent.py`

这一步会：

- 根据 chunk 文本重新生成 embedding
- 在内存中重建 `VectorRetriever`

也就是说，问答阶段并不是直接读取一个持久化好的数据库，而是：

- 读 metadata
- 再重建检索结构

### 5.3 query 向量化

用户问题会先通过 `HashingEmbedder` 转成向量。

### 5.4 native top-k 检索

然后调用底层 `VectorRetriever.search()` 做 top-k 搜索。

### 5.5 检索后优化

在 `agent.py` 里，检索结果还会继续做二次处理：

- rerank
- 源码优先
- 文档降权
- 相似 chunk 去重

这一层很重要，因为代码问答不适合完全照搬通用文本检索。

### 5.6 Prompt 组装

文件：

- `python/codebase_copilot/prompt.py`

使用：

- `build_qa_prompt()`

把 query 和检索结果拼成模型或本地 synthesizer 可以消费的上下文。

### 5.7 结果生成

最后有两条输出路径：

#### 本地路径

- `LocalAnswerSynthesizer`

#### LLM 路径

- `llm.py`

最终输出包括：

- `answer`
- `sources`
- `prompt`
- `backend`

---

## 6. 修改建议流程：patch 是怎么工作的

这条流程对应的是：

```powershell
python python/main.py patch "How should I add input validation to the login flow?" --index data/metadata.json
```

`patch` 和 `ask` 有一大段流程是共用的：

- 读取 metadata
- 重建检索器
- 做 query embedding
- native top-k
- rerank 和去重

但它和 `ask` 的差别主要在后半段。

### 6.1 patch intent 检索

`patch` 的检索会更偏向“适合修改的代码位置”，而不是只找解释问题最相关的段落。

### 6.2 build_patch_prompt

文件：

- `python/codebase_copilot/prompt.py`

使用：

- `build_patch_prompt()`

这个 prompt 会更强调：

- 修改哪个文件
- 为什么改
- 给出 patch 风格建议

### 6.3 LocalPatchSynthesizer

文件：

- `python/codebase_copilot/agent.py`

作用：

- 在没有 LLM 的情况下给出 deterministic patch 建议
- 输出文件位置、修改原因和 patch sketch

### 6.4 LLM Path

如果配置了模型，也可以走 LLM 路径生成更自然的 patch suggestion。

最终输出包括：

- `suggestion`
- `sources`
- `prompt`
- `backend`
- `notice`

所以 `patch` 可以看作：

- 共享检索底座
- 但换了一个更偏“修改建议”的后处理和输出形式

---

## 7. Benchmark 流程：为什么要单独画一条

这条流程对应的是：

```powershell
python python/main.py benchmark
```

它的作用不是辅助功能，而是回答这个项目一个非常关键的问题：

**既然已经有 Python 工作流，为什么还要写 C++ 检索？**

### 7.1 生成随机向量

文件：

- `python/codebase_copilot/benchmark.py`

作用：

- 生成随机单位向量
- 构造 synthetic 数据集和 query

### 7.2 Python baseline

- `PythonBruteForceRetriever`

这是纯 Python 的 brute-force 检索路径，作为对照组。

### 7.3 C++ path

- `VectorRetriever`

这条路径会调用 native C++ 检索实现。

### 7.4 结果对比

benchmark 会比较：

- Python 平均查询耗时
- C++ 平均查询耗时
- speedup
- top-k 是否一致

### 7.5 输出 Markdown 报告

最终会生成：

- `data/day6_benchmark.md`

同时 README 里的 benchmark 表也来自这个流程。

所以这一条流程是“性能证明链路”，不是简单附带脚本。

---

## 8. 流程图里最值得强调的 5 个点

### 8.1 统一入口

所有能力都从 `python/main.py` 进入，这让项目非常适合展示和测试。

### 8.2 metadata.json 是中间桥梁

离线索引输出 `metadata.json`，在线问答和 patch 都依赖它。

所以它相当于：

- 离线阶段和在线阶段之间的桥梁

### 8.3 ask 和 patch 共用一套检索底座

这个设计很合理，因为两者都需要：

- 找相关代码
- 做 rerank
- 处理上下文

差别主要只在最后的 prompt 和输出形式。

### 8.4 本地 fallback 很关键

项目不是“只有接入模型才可用”，而是：

- 没有 API key 也能跑
- LLM 失败也能回退

这让整个系统工程上更稳定。

### 8.5 benchmark 形成量化闭环

这条流程让项目不仅是一个功能 demo，还是一个有量化证据的工程作品。

---

## 9. 展示时怎么讲这张流程图

下面给你一段可以直接拿去说的版本。

### 1 分钟讲法

> 这张图展示的是 Codebase Copilot 的运行流程。最左边是统一 CLI 入口，所有能力都从 `python/main.py` 进入，包括 `index`、`ask`、`patch` 和 `benchmark`。  
> 第一条主流程是离线索引：系统先扫描仓库文件，再按行切 chunk，用本地 hashing embedding 做向量化，最后通过 `build_index()` 输出 `metadata.json`。  
> 第二条是在线问答：系统读取 `metadata.json`，在 `CodebaseQAAgent` 里重建内存检索器，做 query embedding、native top-k、rerank 和 prompt 组装，最后输出 answer。  
> 第三条是 patch suggestion：前面和 ask 共用一套检索流程，但后面会走 patch prompt 和 patch synthesizer，最终输出 grounded 的修改建议。  
> 最后一条是 benchmark：它会生成随机向量，用 Python baseline 和 C++ retriever 分别跑检索，再输出 benchmark 表，证明 native 检索带来的性能提升。  

### 2 分钟讲法

> 我这个项目的流程设计是先离线索引，再在线推理。离线阶段把仓库扫描、切块、向量化，并生成 `metadata.json`，这样在线阶段就不需要重新从头处理整个仓库。  
> 在 ask 和 patch 阶段，系统都会从 `metadata.json` 恢复 chunk 信息，并在内存里重建 `VectorRetriever`。然后 query 会被向量化，送到底层 C++ 检索器做 top-k 搜索。  
> 和普通文本检索不同的是，我在 `agent.py` 里做了代码场景优化，比如源码优先、文档降权、相似 chunk 去重，所以检索结果更适合代码理解。  
> ask 流程最终输出 answer，patch 流程最终输出修改建议。两者共用同一套 retrieval 底座，只是在 prompt 和结果生成阶段分叉。  
> 最后 benchmark 流程用同样的数据同时跑 Python brute-force 和 C++ retriever，这样就能量化证明底层 native path 的收益，而不是只停留在“我写了 C++”这个描述上。  

---

## 10. 和架构图配合时怎么用

最好的讲法是：

1. 先展示 `architecture` 图
   说明“系统由哪些模块组成”
2. 再展示 `flow` 图
   说明“这些模块是怎么串起来运行的”

这样会比只讲一张图更完整。

你可以简单分工：

- `architecture` 图：讲系统设计
- `flow` 图：讲运行过程

---

## 11. 总结

这张流程图的核心价值在于把项目讲成一个完整闭环：

1. `index` 生成可检索元数据
2. `ask` 做 grounded QA
3. `patch` 做 grounded 修改建议
4. `benchmark` 给出量化性能结果

如果要一句话概括这张图，可以说：

> 这是一个把离线索引、在线问答、修改建议和性能验证全部串起来的本地代码仓库 Agent 流程图。

