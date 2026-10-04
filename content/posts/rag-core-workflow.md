---
title: "RAG 核心工作流程，给大模型装上你的\"私房知识库\""
date: 2026-06-13
draft: false
categories: ["AI"]
tags: ["RAG", "向量数据库", "大模型", "检索增强"]
summary: "朋友们，咱今天来聊一个贼有意思的东西 —— RAG。"
ShowToc: true
---


朋友们，咱今天来聊一个贼有意思的东西 —— **RAG**。

你有没有遇到过这种尴尬场面：你兴致勃勃地问 ChatGPT 一个关于公司内部文档的问题，结果它一本正经地开始胡说八道（aka 幻觉）？或者你问它"咱公司上季度营收多少"，它给你编了一个看起来很像那么回事但完全不对的数字？

这不能怪大模型，人家训练数据里压根就没有你公司的内部资料嘛 (╯‵□′)╯︵┻━┻。

这时候 RAG 就派上用场了。**RAG（Retrieval-Augmented Generation，检索增强生成）**，说白了就是：**让大模型在回答问题之前，先去你的知识库里翻一翻，找到相关资料，然后拿着资料再回答。**

打个比方：大模型就像一个记忆力超群但没见过你私藏菜谱的大厨，RAG 就是在做菜之前，先把你的独家秘方塞到他手里，让他照着做。这样既不用重新训练大厨（微调模型），又能让他做出你想要的菜。

好嘞，废话不多说，咱直接来看看 RAG 的完整工作流程是怎么跑起来的。

{{< svg "rag-pipeline" >}}

---

## 第一步：文档切块 —— 把大书撕成小纸条

### 为啥要切？

我们手头可能有各种文档：PDF、Word、Markdown、网页抓取的内容…… 这些文档动辄几十页、上万字。如果你直接把一整本书塞给大模型，它会很头疼，因为：

1. **大模型的上下文窗口有限**——虽然现在动辄 128K、1M token，但你也不能每次都把整本《战争与和平》丢进去吧，钱包受不了啊（API 按 token 计费呐）。
2. **检索精度会下降**——你问"Redis 怎么配置集群"，结果把整本运维手册都召回了，里面夹杂着 MySQL、Nginx 等等一堆无关内容，模型容易被带偏。

所以咱得先把文档**切成小块（chunk）**，就像把一本厚厚的百科全书撕成一张张小纸条，每张纸条上只写一个知识点。这样检索的时候才能精准命中。

### 怎么切？

这里面的门道还挺多的，咱一个个来看：

**按字符/词数切（最粗暴）**

```python
# 最简单的按字符数切分
def naive_split(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # overlap 让相邻 chunk 有重叠
    return chunks
```

这种方案简单粗暴，适合纯文本，但**容易在句子中间切断**，把一个完整的意思劈成两半，就很难绷。

**按句子/段落切（稍微聪明点）**

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # 每块最多 500 个字符
    chunk_overlap=50,      # 相邻块重叠 50 个字符
    separators=["\n\n", "\n", "。", ".", " ", ""]  # 优先按段落切，再按句子，再按空格
)
chunks = splitter.split_text(document)
```

这个 splitter 比较聪明，它会按优先级尝试分隔符：先看能不能按段落切，不行就按句子，再不行按空格，最后才按字符硬切。**这样能尽量保证每个 chunk 都是一个完整的语义单元。**

**按语义切（最智能但最贵）**

还有一些方案会用一个小模型来判断"这里是不是一个语义边界"，比如读到某个句子发现话题突然变了，就在这切一刀。效果最好但速度慢、成本高。一般咱用 LangChain 的 `RecursiveCharacterTextSplitter` 就够使了。

### 切多大合适？

这是个经验活，大概给大家几个参考：

- **太小**（比如 100 字符）：上下文不够，模型拿到一堆碎片看都看不懂
- **太大**（比如 5000 字符）：检索精度下降，召回一堆无关内容
- **常见范围**：256 ~ 1024 token 之间，具体得看你的文档类型和应用场景

另外别忘了设置 **overlap（重叠）**，一般设 chunk_size 的 10% 左右。为啥要重叠？想象一下，如果有一句话刚好被切成两半，前半句在 chunk A，后半句在 chunk B，检索的时候就容易漏掉。有了 overlap，相邻 chunk 会有一小段重复内容，就能缓解这个问题。


> **小贴士**：如果你的文档是 Markdown 格式，可以用 `MarkdownHeaderTextSplitter`，它能识别 `#`、`##` 标题层级，按章节结构来切，效果比纯文本切分好得多。

---

## 第二步：向量化 —— 把文字变成数学

### 这又是在整啥？

切好块之后，我们不能直接拿文字去做相似度比较（总不能每次都全文比对一遍吧，太慢了）。咱得把这些文字**变成一堆数字（向量）**，让计算机能高效地计算"哪段文字跟用户的问题最相关"。

**通俗理解**：向量化就是把一句话映射到高维空间里的一个点。语义相近的两句话，它们在空间里的距离就很近；语义不相关的，距离就远。

比如：
- "今天天气真好" → `[0.12, -0.34, 0.56, ...]`（一个 768 或 1536 维的数组）
- "阳光明媚的一天" → `[0.13, -0.31, 0.54, ...]`（跟上面很接近）
- "数据库连接超时了" → `[-0.45, 0.78, -0.23, ...]`（跟上面差老远了）

### 用啥模型做向量化？

这就得掏出 **Embedding 模型** 了。常见的选择：

| 模型 | 维度 | 特点 |
|------|------|------|
| OpenAI `text-embedding-ada-002` | 1536 | 效果好，但要钱，且数据要传出去 |
| OpenAI `text-embedding-3-small` | 512/1536 | 新一代，性价比高，可调维度 |
| `bge-large-zh` (BAAI) | 1024 | 中文效果拔群，开源可本地部署 |
| `m3e-base` | 768 | 国产开源，中文友好，轻量 |
| `all-MiniLM-L6-v2` | 384 | 英文为主，胜在轻量快速 |

选模型主要考虑三点：**语言（中文还是英文）、部署方式（本地还是 API）、成本预算**。

```python
# 用 OpenAI 做 embedding 的示例
from openai import OpenAI

client = OpenAI()
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="RAG 的核心工作流程是什么？"
)
vector = response.data[0].embedding  # 这就是向量了，一个浮点数列表
print(len(vector))  # 1536
```

> **预警**：如果你用的是本地模型，注意向量维度要和后面向量数据库的索引配置一致，不然插不进去就尴尬了 (￣▽￣)"

---

## 第三步：存入向量数据库 —— 给知识找个家

向量有了，接下来得找个地方把它们存起来，而且要支持**高效的相似度搜索**。

这里插一嘴：普通的关系型数据库（MySQL 之流）能不能存？能，但你想想，每次查询都要把用户的 query 向量跟库里几万条向量逐一计算距离，那速度……啧啧，黄花菜都凉了。

所以咱需要**向量数据库**，它专门针对向量做了索引优化（比如 HNSW、IVF 这些索引算法），让相似度搜索能跑到毫秒级。

### 主流向量数据库选哪个？

| 数据库 | 类型 | 适用场景 |
|--------|------|----------|
| **Chroma** | 轻量嵌入式 | 学习、原型、小项目，pip install 就能用 |
| **Milvus** | 分布式 | 生产环境，数据量大，性能要求高 |
| **Qdrant** | 高性能 | 生产环境，Rust 写的，性能猛猛的 |
| **Weaviate** | 全功能 | 自带向量化和问答模块，开箱即用 |
| **Pinecone** | 云服务 | 不想自己运维的懒人首选（bushi） |
| **FAISS** | 库（非数据库） | Meta 出品，纯向量索引库，不能持久化 |
| **pgvector** | PostgreSQL 插件 | 已经用了 PG 的团队的省心之选 |

对于新手朋友，咱强烈推荐从 **Chroma** 上手，部署零门槛：

```python
import chromadb

# 创建一个 Chroma 客户端（数据存在本地文件夹）
client = chromadb.PersistentClient(path="./my_knowledge_base")

# 创建一个集合（可以理解为一张表）
collection = client.get_or_create_collection(
    name="company_docs",
    metadata={"hnsw:space": "cosine"}  # 用余弦相似度
)

# 把切好的文档块和对应的向量塞进去
collection.add(
    documents=["Redis 集群至少需要 3 个主节点...", "MySQL 的默认端口是 3306..."],
    embeddings=[vector_1, vector_2],  # 上一步生成的向量
    metadatas=[{"source": "运维手册.pdf", "page": 3}, {"source": "运维手册.pdf", "page": 7}],
    ids=["doc_001", "doc_002"]
)
```

搞定！知识库就这么建好了，so easy (゜-゜)つロ


---

## 第四步：相似度检测 —— 找到最相关的"小纸条"

知识库有了，现在用户提了一个问题，比如："Redis 集群最少要几个节点？"

这时候 RAG 的工作流程是：

1. 把用户的问题也做一次向量化（用同一个 Embedding 模型）
2. 拿问题向量去向量数据库里做**相似度检索**
3. 找到最相似的 N 个文档块（这个 N 就是 **top_k**，通常取 3~10）

```python
# 用户问题向量化
question = "Redis 集群最少要几个节点？"
question_vector = get_embedding(question)

# 去向量数据库里检索最相似的 5 个文档块
results = collection.query(
    query_embeddings=[question_vector],
    n_results=5,  # top_k = 5
    include=["documents", "metadatas", "distances"]
)

# 看看召回了啥
for doc, metadata, distance in zip(results['documents'][0], 
                                     results['metadatas'][0],
                                     results['distances'][0]):
    print(f"距离: {distance:.4f} | 来源: {metadata['source']} | 内容: {doc[:50]}...")
```

### 相似度怎么算的？

常见的相似度度量有三种：

- **余弦相似度（Cosine Similarity）**：看两个向量在方向上的接近程度，不考虑长度。**最常用，推荐默认选这个。**
- **欧氏距离（Euclidean Distance）**：两点之间的直线距离。向量被归一化之后，它和余弦相似度等价。
- **点积（Dot Product）**：向量对应位置相乘再求和。如果你的 Embedding 模型输出的是归一化向量，点积就等价于余弦相似度。

> **小提示**：不同 Embedding 模型可能推荐不同的相似度度量。比如 OpenAI 的 embedding 推荐用余弦相似度，而有的模型推荐用点积。使用前瞄一眼文档准没错。

### 混合检索了解一下？

有时候纯靠向量相似度不太够，比如用户问"公司 2024 年的报销政策"，向量检索可能返回 2023 年的政策（语义上很像，但不是用户想要的年份）。

这时候可以上**混合检索（Hybrid Search）**：向量检索 + 关键词检索（BM25）结合，既能抓到语义相关的，又能抓到关键词精确匹配的。很多向量数据库（如 Weaviate、Milvus）都原生支持混合检索，开箱即用。


---

## 第五步：拼接上下文 —— 把佐料都备好

检索回来了 top_k 个文档块，但这还没完。你想想，这些块可能来自不同的文档、不同的章节，直接一股脑丢给 LLM 的话，它可能搞不清哪个是哪个。

所以咱得**把检索结果整理一下，拼成一个结构清晰的 prompt**。这一步虽说不算复杂，但做得好不好直接影响最终答案的质量。

```python
def build_prompt(question, retrieved_docs):
    """把用户问题和检索到的文档拼成最终的 prompt"""
    
    # 先整理一下检索到的文档，加个编号和来源
    context_parts = []
    for i, doc in enumerate(retrieved_docs):
        source = doc.get('metadata', {}).get('source', '未知来源')
        context_parts.append(f"[文档片段 {i+1}] (来源: {source})\n{doc['content']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # 拼接最终的 prompt
    prompt = f"""你是一个专业的 AI 助手。请根据以下参考资料回答用户的问题。
如果参考资料中没有相关信息，请如实说"参考资料中未找到相关信息"，不要编造。

## 参考资料：
{context}

## 用户问题：
{question}

## 回答要求：
1. 优先使用参考资料中的信息
2. 如果引用资料中的内容，请注明来源
3. 回答要清晰、有条理

## 你的回答："""
    
    return prompt
```

一个典型的 prompt 模板长这样，包含了：
- **角色设定**：告诉模型它是谁、该干什么
- **参考资料**：检索到的文档内容，带编号和来源
- **用户问题**：原始问题
- **约束条件**：防止模型瞎编（这点很重要！）

### 一些实用的小技巧

**rerank（重排序）**：检索回来的 top_k 个结果不一定都跟问题强相关，可以用一个 rerank 模型再筛一遍，把最相关的排前面。Cohere 的 rerank API 和 `bge-reranker` 都是不错的选择。

**按相关度截断**：设一个相似度阈值，低于这个值的文档直接丢掉，避免给模型塞垃圾信息。但这个阈值不好调，设太高可能啥都召不回，设太低又等于没设。

**注意 token 预算**：不管你怎么拼，最后塞进 prompt 的总 token 数不能超过模型的上下文窗口（而且还得给模型的输出预留空间）。建议写个函数帮你自动计算和截断。

---

## 第六步：生成答案 —— 大模型闪亮登场

好了，prompt 已经拼好，最后一步就简单了——**把 prompt 丢给大模型，让它生成答案**。

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个专业的技术助手。"},
        {"role": "user", "content": final_prompt}  # 上一步拼好的 prompt
    ],
    temperature=0.3,  # RAG 场景建议温度低一点，减少随机性
    max_tokens=2000
)

answer = response.choices[0].message.content
print(answer)
```

到这一步，用户就能得到一个**基于你私有知识库的靠谱回答**了！撒花 ✿✿ヽ(°▽°)ノ✿

### 为什么不直接微调模型？

有朋友可能会问："我把文档拿去微调一个专用模型不香吗？"

香是香，但有几个问题：
- **成本高**：微调需要 GPU、数据标注、反复实验
- **更新麻烦**：知识更新了还得重新微调，RAG 直接更新向量库就行
- **可解释性差**：微调后的模型"为什么这么回答"你很难解释，RAG 的每一步都看得见摸得着

所以现在业内的主流做法是 **RAG 优先，微调兜底**：先用 RAG 解决大部分知识检索问题，真遇到 RAG 搞不定的专业领域任务再考虑微调。

---

## 完整流程串起来

来，咱用一段代码把整个流程串一遍，让大家有个全局视角：

```python
# ============ 离线阶段：构建知识库 ============

# 1. 加载文档
with open("company_faq.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

# 2. 文档切块
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(raw_text)

# 3. 向量化 + 存入向量数据库
import chromadb
from openai import OpenAI

openai_client = OpenAI()
chroma_client = chromadb.PersistentClient(path="./knowledge_base")
collection = chroma_client.get_or_create_collection(name="faq")

for i, chunk in enumerate(chunks):
    # 向量化
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk
    )
    embedding = response.data[0].embedding
    # 存入数据库
    collection.add(
        documents=[chunk],
        embeddings=[embedding],
        ids=[f"chunk_{i}"]
    )

print(f"知识库构建完成，共 {len(chunks)} 个文档块")

# ============ 在线阶段：回答用户问题 ============

def rag_query(question: str) -> str:
    # 1. 问题向量化
    q_embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    ).data[0].embedding
    
    # 2. 相似度检索
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=5
    )
    
    # 3. 拼接上下文
    retrieved_docs = [
        {"content": doc, "metadata": {}}
        for doc in results['documents'][0]
    ]
    
    context_parts = []
    for i, doc in enumerate(retrieved_docs):
        context_parts.append(f"[片段 {i+1}]\n{doc['content']}")
    context = "\n\n---\n\n".join(context_parts)
    
    prompt = f"""根据以下参考资料回答问题，如果资料中没有相关信息请如实说。

## 参考资料：
{context}

## 用户问题：
{question}

## 你的回答："""
    
    # 4. 生成答案
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    return response.choices[0].message.content

# 试一下
print(rag_query("公司年假怎么算的？"))
```

> **注意哈**：上面这段代码是为了让大家理解流程所以写得比较精简，生产环境里你还得加上错误处理、日志、流式输出等一堆东西。

---

## 再补充几个容易踩的坑

### 1. Embedding 模型选型要慎重

中英文混用的场景，别傻乎乎地拿一个纯英文 embedding 模型去向量化中文文档，效果会非常感人（别问我怎么知道的）。中文场景推荐 `bge-large-zh`、`m3e-base` 或者 `text-embedding-3-small`（OpenAI 的新模型多语言效果还不错）。

### 2. top_k 不是越大越好

有人觉得"我把 top_k 设成 50，召回更多文档给模型参考不就更全面了吗？" 实际上这会导致两个问题：
- prompt 变得超长，token 费用飙升
- 召回太多弱相关的内容反而会干扰模型判断

一般 top_k 取 3~10 就够用了，具体可以跑几轮实验看看效果再定。

### 3. 文档质量直接决定 RAG 效果

这个说实话是最容易被忽视的。如果你的源文档排版稀烂、全是扫描件 OCR 出来的乱码、或者各种拼写错误，那再怎么调 chunk_size 和 embedding 模型都救不回来。**Garbage in, garbage out**，前期在文档整理上多花点功夫，后面能省不少事。

### 4. 别忘了处理"不知道怎么回答"的情况

如果检索回来的所有文档相关度都很低（比如都低于 0.5 的阈值），这说明知识库里可能没有相关信息。这时候应该直接告诉用户"抱歉，暂时没找到相关信息"，而不是让模型硬编。咱可以在代码里加一个兜底逻辑：

```python
# 检查检索质量
if results['distances'][0][0] < 0.5:  # 余弦相似度低于阈值
    return "抱歉，当前知识库中暂未找到与您问题相关的信息，请尝试换个问法或者联系管理员补充资料。"
```

---

## 总结一下

RAG 的核心工作流程其实就六个步骤：

> **文档切块 → 向量化 → 存入向量库 → 相似度检索 → 拼接上下文 → 生成答案**

看起来每一步都不复杂，但要做到生产级别的效果，还是有不少细节需要打磨的。比如 chunk 策略怎么选、embedding 模型用什么、检索要不要加 rerank、prompt 怎么设计才能抑制幻觉……

以上就是个人在 RAG 方面的一些经验分享，希望能帮到正在折腾这方面的新手朋友们。如果哪里有错误或者遗漏，也请大佬们不吝赐教指出！

本文完结撒花！！！

---

*参考资料：*
- [LangChain 官方文档 - Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [Chroma DB 使用指南](https://docs.trychroma.com/)
- [OpenAI Embeddings 文档](https://platform.openai.com/docs/guides/embeddings)
