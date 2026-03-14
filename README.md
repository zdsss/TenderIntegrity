# TenderIntegrity — 标书雷同与语义查重

> 面向医疗采购监管的前置风险筛查工具

---

## 项目简介

TenderIntegrity 通过「向量语义检索 + LLM 智能判定」两阶段流程，自动识别标书文件中的雷同段落，辅助监管人员快速定位围标风险。支持 PDF、Word、TXT 三种格式，输出 JSON / CSV / PDF 风险报告。

---

## 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                      接入层 (API Layer)                           │
│         FastAPI REST API  /  CLI 命令行  /  未来 Web UI            │
└───────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                  工作流编排层 (LangGraph StateGraph)               │
│  [上传]→[解析]→[分块]→[向量化]→[检索]→[评分]→[LLM判定]→[报告]      │
└──────┬─────────────────────────────────────────────┬─────────────┘
       │                                             │
┌──────▼──────────┐                   ┌─────────────▼─────────────┐
│  文档处理层      │                   │       智能分析层            │
│  DocumentParser  │                   │  SimilarityEngine         │
│  ChunkSplitter   │                   │  RiskScorer               │
│  MetadataExtract │                   │  LLM RiskReasonChain      │
│  WhitelistFilter │                   │  KeywordExtractor         │
└──────┬──────────┘                   └─────────────┬─────────────┘
       │                                             │
┌──────▼─────────────────────────────────────────────▼────────────┐
│                    基础设施层 (Infrastructure)                     │
│  ChromaDB（向量存储） │ SQLite→PostgreSQL（元数据）                  │
│  Claude API（LLM）   │ BGE-M3 Embedding（中文语义）│ 文件存储        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 技术选型

| 组件 | 选型 | 说明 |
|---|---|---|
| LLM | Claude claude-sonnet-4-6 | 中文能力强，结构化输出稳定 |
| Embedding | BGE-M3（BAAI，离线部署） | 中文语义优化，无 API 依赖 |
| 向量库 | ChromaDB（MVP）→ Milvus（生产） | 零配置本地化，后期可平滑迁移 |
| 工作流编排 | LangGraph 0.2.x | 有状态 DAG，支持断点恢复和并行分发 |
| LLM 框架 | LangChain 0.3.x（LCEL） | 成熟 Chain 抽象，Pydantic 输出解析 |
| API 框架 | FastAPI | 异步、自动文档、Pydantic 集成 |
| 元数据存储 | SQLite（MVP）→ PostgreSQL（生产） | 轻量起步，平滑扩展 |
| 文档解析 | pdfplumber + python-docx + chardet | 三格式覆盖 |
| 中文分词 | jieba | 关键词提取 |
| 依赖管理 | uv | 速度快，现代 Python 工具链 |

---

## 项目结构

```
TenderIntegrity/
│
├── README.md
├── pyproject.toml                  # uv 依赖管理
├── .env.example                    # 环境变量模板
├── Makefile                        # 常用命令
│
├── config/
│   ├── settings.py                 # Pydantic Settings 统一配置
│   ├── thresholds.yaml             # 相似度/风险分数阈值
│   └── whitelist/
│       ├── legal_refs.txt          # 法规条文正则白名单
│       ├── standard_refs.txt       # 标准引用正则白名单
│       └── common_phrases.txt      # 医疗采购通用表述（向量化）
│
├── src/
│   ├── api/                        # FastAPI 接入层
│   │   ├── main.py
│   │   ├── routers/                # tasks / documents / reports
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   └── dependencies.py
│   │
│   ├── workflow/                   # LangGraph 编排层
│   │   ├── graph.py                # StateGraph 定义
│   │   ├── state.py                # TenderComparisonState
│   │   ├── nodes/                  # 9 个工作流节点
│   │   └── routers.py              # 条件路由函数
│   │
│   ├── document/                   # 文档处理层
│   │   ├── parser.py               # 统一入口（工厂模式）
│   │   ├── pdf_parser.py           # pdfplumber
│   │   ├── docx_parser.py          # python-docx
│   │   ├── text_parser.py          # chardet + 纯文本
│   │   ├── chunker.py              # 段落切分策略
│   │   └── metadata_extractor.py  # 章节识别、段落类型分类
│   │
│   ├── analysis/                   # 智能分析层
│   │   ├── similarity.py           # SimilarityEngine
│   │   ├── scorer.py               # RiskScorer（综合评分）
│   │   ├── whitelist_filter.py     # 三层误报过滤
│   │   └── keyword_extractor.py    # jieba 关键词提取
│   │
│   ├── chains/                     # LangChain 层
│   │   ├── risk_reason_chain.py    # LCEL 风险判定链
│   │   ├── prompts/                # Prompt 模板
│   │   └── output_parsers.py       # Pydantic 结构化输出
│   │
│   ├── vectorstore/                # 向量数据库层
│   │   ├── client.py               # ChromaDB 客户端单例
│   │   ├── repository.py           # CRUD 封装
│   │   └── embedding_service.py    # BGE-M3 封装
│   │
│   ├── report/                     # 报告生成层
│   │   ├── generator.py
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   └── pdf_exporter.py
│   │
│   └── storage/                    # 持久化层
│       ├── database.py             # SQLAlchemy 配置
│       ├── models.py               # Task / Document / RiskPair ORM
│       └── repositories/
│
├── tests/
│   ├── unit/                       # 单元测试
│   ├── integration/                # 集成测试
│   └── e2e/                        # 端到端测试
│
├── scripts/
│   ├── run_comparison.py           # CLI 触发比对任务
│   └── seed_whitelist.py           # 初始化白名单数据
│
└── doc/                            # 产品文档 & 测试样本
```

---

## 快速开始

### 1. 安装依赖

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
make install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY
```

### 3. 初始化白名单数据

```bash
make seed-whitelist
```

### 4. 运行命令行比对（不需要启动服务器）

```bash
python scripts/run_comparison.py \
  --doc-a doc/测试样本A_疑似围标投标文件.docx \
  --doc-b doc/测试样本B_疑似围标投标文件.docx \
  --output reports/
```

### 5. 启动 API 服务器

```bash
make run
# 访问 http://localhost:8000/docs 查看 API 文档
```

---

## LangGraph 工作流

```
START
  │
  ▼
parse_documents ──[解析失败]──→ handle_error ──→ END
  │
  ▼
chunk_documents → filter_whitelist → embed_and_store
  │
  ▼
retrieve_similar_pairs → score_candidates
  │
  ├─[无高/中风险对]──→ generate_report ──→ END
  │
  └─[有候选对]──→ llm_analyze_pairs ──→ generate_report ──→ END
```

### 工作流节点说明

| 节点 | 职责 |
|---|---|
| `parse_documents` | 调用 DocumentParser 提取原始文本 |
| `chunk_documents` | 自然段落切分 + 章节识别 + 类型分类 |
| `filter_whitelist` | 正则 + 向量两层白名单标记 |
| `embed_and_store` | BGE-M3 批量向量化，写入 ChromaDB |
| `retrieve_similar_pairs` | 跨文档向量检索，生成候选相似对 |
| `score_candidates` | 综合评分 + 过滤低风险对 |
| `llm_analyze_pairs` | 调用 Claude，生成中文判定理由 |
| `generate_report` | 汇总生成结构化风险报告 |
| `handle_error` | 捕获异常，记录错误 |

---

## 风险评分算法

```
base_risk_score = (
    vector_similarity  × 0.60 +   # 余弦相似度
    keyword_overlap    × 0.25 +   # jieba 关键词 Jaccard
    context_bonus      × 0.15     # 同章节 +0.1，tech_spec +0.05
) × 100

白名单段落惩罚 × 0.20
LLM 调整 ±20 分
最终分 = base_risk_score + llm_adjustment
```

### 风险等级

| 分数 | 风险等级 |
|---|---|
| 85 ~ 100 | 🔴 高风险 (high) |
| 65 ~ 84 | 🟡 中风险 (medium) |
| 45 ~ 64 | 🟢 低风险 (low) |
| 0 ~ 44 | ⚪ 无明显风险（不进报告） |

---

## 误报过滤（白名单三层防御）

| 层次 | 方法 | 覆盖类型 |
|---|---|---|
| 第1层（正则） | 规则匹配 | 《X法》第X条、GB/T XXXX、YY/T XXXX |
| 第2层（向量） | 与白名单库相似度 > 0.88 | 医疗采购通用惯例表述 |
| 第3层（LLM） | Claude 主动识别 | 改写后的通用表述，前两层漏网情形 |

---

## REST API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/documents/upload` | 上传标书文件 |
| POST | `/api/v1/tasks` | 创建比对任务 |
| GET | `/api/v1/tasks/{task_id}` | 查询任务进度 |
| GET | `/api/v1/tasks/{task_id}/report` | 获取 JSON 报告 |
| GET | `/api/v1/tasks/{task_id}/report/csv` | 导出 CSV 报告 |
| GET | `/api/v1/tasks/{task_id}/report/pdf` | 导出 PDF 报告 |
| GET | `/api/v1/tasks` | 历史任务列表 |
| DELETE | `/api/v1/tasks/{task_id}` | 删除任务 |

---

## 测试

```bash
# 单元测试
make test-unit

# 集成测试
make test-integration

# 端到端测试（需配置 ANTHROPIC_API_KEY）
make test-e2e
```

---

## 阶段规划

### 阶段 1 — MVP（当前）
- [x] 项目脚手架（pyproject.toml、配置、目录结构）
- [x] 文档解析（PDF / Word / TXT）
- [x] 段落切分与元数据提取
- [x] 白名单过滤（正则 + 向量两层）
- [x] BGE-M3 向量化 + ChromaDB 存储
- [x] 跨文档相似度检索
- [x] 综合风险评分算法
- [x] LangGraph 完整工作流（9节点）
- [x] LLM 风险判定（Claude + Pydantic 结构化输出）
- [x] JSON + CSV 风险报告导出
- [x] CLI 命令行入口

### 阶段 2 — 功能增强
- [ ] FastAPI REST API 完整实现
- [ ] 多文档 All-vs-All 矩阵比对
- [ ] LangGraph Send API 并行分发
- [ ] PDF 报告导出（WeasyPrint）
- [ ] 任务进度查询 API
- [ ] 基础 Web 展示页面

### 阶段 3 — 平台化
- [ ] 历史文档管理与跨项目比对
- [ ] 审查人员标注与协作功能
- [ ] JWT 用户认证与权限管理
- [ ] Milvus 向量库 + PostgreSQL 数据库
- [ ] 监控、日志与 LLM 成本追踪

---

## 报告输出示例

```json
{
  "task_id": "abc123",
  "overall_risk_level": "high",
  "overall_similarity_rate": 0.34,
  "risk_summary": {
    "high_count": 5,
    "medium_count": 12,
    "low_count": 8
  },
  "risk_pairs": [
    {
      "pair_id": "...",
      "risk_level": "high",
      "risk_type": "semantic_paraphrase",
      "final_score": 87.5,
      "doc_a": { "section": "技术方案", "page": 12, "text": "..." },
      "doc_b": { "section": "技术方案", "page": 8, "text": "..." },
      "vector_similarity": 0.94,
      "reason_zh": "两段文字在描述医疗设备技术参数时...",
      "suggest_action": "建议重点复核技术方案章节"
    }
  ]
}
```

---

## 设计决策

**为什么两阶段（向量 + LLM）而非纯 LLM？**
向量检索从 200+ 段落组合中快速筛出 20~30 对候选，仅对候选对调用 LLM，节省约 80% API 成本。

**为什么用 LangGraph？**
工作流有条件分支、并发需求、进度查询需求。LangGraph StateGraph 天然支持这些场景，且支持断点续传。

**Chunking 为什么按自然段落？**
标书段落本身具有语义完整性，固定长度切分会破坏语义单元，导致向量质量下降和误配对。

**白名单为什么三层？**
正则处理显式引用（快速），向量处理改写后通用表述（准确），LLM 兜底前两层漏网（完整）。
