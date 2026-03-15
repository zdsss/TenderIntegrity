# TenderIntegrity — 标书雷同与语义查重

> 面向医疗采购监管的前置风险筛查工具

---

## 项目简介

TenderIntegrity 通过「向量语义检索 + 结构分析 + 关键字段比对 + LLM 智能判定」多维流程，自动识别标书文件中的雷同段落和围标信号，辅助监管人员快速定位风险。支持 PDF、Word、TXT 三种格式，输出 JSON / CSV / PDF 风险报告。

---

## 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                      接入层 (API Layer)                           │
│         FastAPI REST API  /  CLI 命令行  /  React Web UI          │
└───────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                  工作流编排层 (LangGraph StateGraph)               │
│  [解析]→[分块]→[结构/字段分析]→[白名单]→[向量化]→[检索]→           │
│  [评分]→[LLM判定]→[报告]                                          │
└──────┬─────────────────────────────────────────────┬─────────────┘
       │                                             │
┌──────▼──────────┐                   ┌─────────────▼─────────────┐
│  文档处理层      │                   │       智能分析层            │
│  DocumentParser  │                   │  RiskScorer               │
│  ChunkSplitter   │                   │  StructureComparator      │
│  MetadataExtract │                   │  FieldOverlapDetector     │
│  KeyFieldExtract │                   │  LLM RiskReasonChain      │
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
| 前端 | React 19 + TypeScript + Ant Design v6 + Vite | 现代 SPA |

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
│   │
│   ├── workflow/                   # LangGraph 编排层
│   │   ├── graph.py                # StateGraph 定义
│   │   ├── state.py                # TenderComparisonState
│   │   ├── nodes/                  # 工作流节点
│   │   │   ├── parse_node.py
│   │   │   ├── chunk_node.py
│   │   │   ├── structure_node.py   # 结构相似度 + 字段重叠分析
│   │   │   ├── whitelist_node.py
│   │   │   ├── embed_node.py
│   │   │   ├── retrieve_node.py
│   │   │   ├── score_node.py
│   │   │   ├── llm_node.py
│   │   │   └── report_node.py
│   │   └── routers.py
│   │
│   ├── document/                   # 文档处理层
│   │   ├── parser.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── text_parser.py
│   │   ├── chunker.py
│   │   ├── metadata_extractor.py
│   │   └── field_extractor.py      # 关键字段提取（电话/邮箱/联系人/公司）
│   │
│   ├── analysis/                   # 智能分析层
│   │   ├── similarity.py
│   │   ├── scorer.py               # RiskScorer（综合评分）
│   │   ├── structure_comparator.py # 章节结构相似度分析
│   │   ├── field_overlap_detector.py # 关键字段重叠检测
│   │   ├── whitelist_filter.py
│   │   └── keyword_extractor.py
│   │
│   └── chains/ / vectorstore/ / report/ / storage/
│
├── frontend/                       # React Web UI
│   └── src/pages/ReportPage/       # 风险报告展示页
│
└── tests/
    └── unit/                       # 49 个单元测试
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

### 3. 启动 API 服务器 + 前端

```bash
make run
# 后端: http://localhost:8000/docs
cd frontend && npm run dev
# 前端: http://localhost:5173
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
chunk_documents
  │
  ▼
analyze_structure_and_fields   ← Phase 2 新增：结构相似度 + 字段重叠
  │
  ▼
filter_whitelist → embed_and_store → retrieve_similar_pairs → score_candidates
  │
  ├─[无候选对]──→ generate_report ──→ END
  │
  └─[有候选对]──→ llm_analyze_pairs ──→ generate_report ──→ END
```

### 工作流节点说明

| 节点 | 职责 |
|---|---|
| `parse_documents` | 调用 DocumentParser 提取原始文本 |
| `chunk_documents` | 自然段落切分 + 章节识别 + 类型分类 |
| `analyze_structure_and_fields` | 章节结构相似度（Jaccard + 编辑距离）+ 关键字段重叠检测 |
| `filter_whitelist` | 正则 + 向量两层白名单标记 |
| `embed_and_store` | BGE-M3 批量向量化，写入 ChromaDB |
| `retrieve_similar_pairs` | 跨文档向量检索，生成候选相似对 |
| `score_candidates` | 综合评分 + 过滤低风险对 |
| `llm_analyze_pairs` | 调用 Claude，生成中文判定理由（分析所有 ≥45 分对，上限 20 对） |
| `generate_report` | 汇总生成结构化风险报告（含结构分析和字段重叠） |
| `handle_error` | 捕获异常，记录错误 |

---

## 风险评分算法

```
base_risk_score = (
    vector_similarity  × 0.60 +   # 余弦相似度
    keyword_overlap    × 0.25 +   # jieba 关键词 Jaccard
    context_bonus      × 0.15     # 同章节 +0.1，tech_spec +0.05
) × 100

白名单段落惩罚 × 0.50（Phase 2 调整：降低置信度而非彻底压分）
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

### 整体文档风险判定（Phase 2 修复：比例判定）

| 条件 | 判定 |
|---|---|
| `similarity_rate ≥ 0.30` 或 `高风险对/总对数 ≥ 0.05` | 高风险 |
| `similarity_rate ≥ 0.15` 或 `(高风险对 ≥ 1 且 中风险对 ≥ 3)` | 中风险 |
| 其他 | 低风险 |

> `similarity_rate` = 被任意风险对（high/medium/low）覆盖的不重复 chunk 数 / 文档 A 总 chunk 数

---

## 系统能力边界

当前系统（Phase 2）可检测以下围标场景：

| 场景 | 检测维度 | 可信度 |
|---|---|---|
| 文字逐字复制 | 向量相似度 + 关键词重叠 | 高 |
| 语义改写（同义替换） | LLM 分析（已覆盖 ≥45 分对） | 中~高 |
| 章节结构一致（版式同源） | StructureComparator | 中 |
| 联系方式/人员重叠 | FieldOverlapDetector | 高（精确匹配）/ 中（模糊） |
| 表格参数完全一致 | 向量相似度（table_row chunk） | 高 |

---

## 已知局限

| 编号 | 问题描述 | Phase 3 规划 |
|---|---|---|
| P5 残留 | 结构相似度仅比较标题列表，未分析章节长度比例 | 加入段落密度分析 |
| P6 残留 | 联系人提取依赖关键词上下文，无实体识别 | 接入 NER 模型 |
| 价格梯度 | 未检测投标价格分布异常（等差/等比梯度） | Phase 3 新增 |
| 时间戳聚集 | 未检测文件修改时间异常接近 | Phase 3 新增 |
| 多文档矩阵 | all_vs_all 模式下无并行优化 | LangGraph Send API |

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
# 后端单元测试（49 个）
uv run pytest tests/unit/ -v

# 前端测试（48 个）
cd frontend && npm test
```

---

## 报告输出示例

```json
{
  "task_id": "abc123",
  "overall_risk_level": "high",
  "overall_similarity_rate": 0.34,
  "risk_summary": { "high_count": 5, "medium_count": 12, "low_count": 8 },
  "structure_analysis": {
    "title_jaccard": 0.875,
    "sequence_similarity": 0.92,
    "overall_score": 89.75,
    "structure_risk_level": "high",
    "matched_sections": [["第一章 总则", "第一章 总则"], ["第二章 技术要求", "第二章 技术要求"]]
  },
  "field_overlaps": [
    {
      "field_type": "phone",
      "value_a": "13812345678",
      "value_b": "13812345678",
      "overlap_type": "exact",
      "risk_note": "两份文档出现相同联系电话 13812345678，疑似同一投标主体"
    }
  ],
  "risk_pairs": [
    {
      "pair_id": "...",
      "risk_level": "high",
      "final_score": 87.5,
      "reason_zh": "两段文字在描述医疗设备技术参数时用词高度一致...",
      "suggest_action": "建议重点复核技术方案章节"
    }
  ]
}
```

---

## 阶段规划

### Phase 1 — MVP ✅
- [x] 项目脚手架（pyproject.toml、配置、目录结构）
- [x] 文档解析（PDF / Word / TXT）
- [x] 段落切分与元数据提取
- [x] 白名单过滤（正则 + 向量两层）
- [x] BGE-M3 向量化 + ChromaDB 存储
- [x] 跨文档相似度检索
- [x] 综合风险评分算法
- [x] LangGraph 完整工作流
- [x] LLM 风险判定（Claude + Pydantic 结构化输出）
- [x] JSON + CSV 风险报告导出
- [x] FastAPI REST API + React Web UI

### Phase 2 — 算法准确性 + 围标多维信号 ✅
- [x] **P1 修复**: `similarity_rate` 覆盖 high/medium/low 所有风险对
- [x] **P2 修复**: 整体风险判定改为覆盖比例双维度判定（不再用绝对数量）
- [x] **P3 修复**: LLM 分析阈值降至 45 分，覆盖语义改写场景（上限 20 对/任务）
- [x] **P4 修复**: 白名单惩罚系数 0.20 → 0.50（降低置信度而非彻底压分）
- [x] **P5**: 新增章节结构相似度分析（StructureComparator）
- [x] **P6**: 新增关键字段提取与重叠检测（联系电话/邮箱/联系人/公司名）
- [x] 前端报告页展示结构相似度 + 字段重叠 Alert

### Phase 3 — 围标深度信号（规划中）
- [ ] 价格梯度异常检测（等差/等比价格分布）
- [ ] 文件时间戳聚集分析（修改时间异常接近）
- [ ] 商务条款高度一致性检测
- [ ] 多文档矩阵比对（LangGraph Send API 并行）
- [ ] 历史文档跨项目查重
- [ ] NER 实体识别增强联系人提取

---

## 设计决策

**为什么两阶段（向量 + LLM）而非纯 LLM？**
向量检索从 200+ 段落组合中快速筛出候选，仅对 ≥45 分候选对调用 LLM（上限 20 对），节省约 80% API 成本。

**为什么用 LangGraph？**
工作流有条件分支、并发需求、进度查询需求。LangGraph StateGraph 天然支持这些场景，且支持断点续传。

**Chunking 为什么按自然段落？**
标书段落本身具有语义完整性，固定长度切分会破坏语义单元，导致向量质量下降和误配对。

**为什么加结构分析和字段提取？**
向量相似度只能发现文字层面的雷同，但围标文件通常呈现版式同源（章节结构一致）和主体关联（电话/联系人重叠）等特征，这些信号与文字内容无关，必须单独提取。
