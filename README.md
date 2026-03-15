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
│  [评分]→[LLM判定]→[综合风险合成]→[报告]                            │
└──────┬─────────────────────────────────────────────┬─────────────┘
       │                                             │
┌──────▼──────────┐                   ┌─────────────▼─────────────┐
│  文档处理层      │                   │       智能分析层            │
│  DocumentParser  │                   │  RiskScorer               │
│  ChunkSplitter   │                   │  StructureComparator      │
│  MetadataExtract │                   │  FieldOverlapDetector     │
│  KeyFieldExtract │                   │  RareTokenAnalyzer  [P3]  │
│  DocxMetaExtract │                   │  PriceAnalyzer      [P3]  │
│  WhitelistFilter │                   │  RiskSynthesizer    [P3]  │
└──────┬──────────┘                   │  LLM RiskReasonChain      │
       │                              │  KeywordExtractor         │
       │                              └─────────────┬─────────────┘
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
│   │   │   ├── structure_node.py   # 结构+字段+罕见序列+价格+元数据分析 [P3]
│   │   │   ├── whitelist_node.py
│   │   │   ├── embed_node.py
│   │   │   ├── retrieve_node.py
│   │   │   ├── score_node.py
│   │   │   ├── llm_node.py
│   │   │   └── report_node.py      # 综合风险合成 [P3]
│   │   └── routers.py
│   │
│   ├── document/                   # 文档处理层
│   │   ├── parser.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── text_parser.py
│   │   ├── chunker.py
│   │   ├── metadata_extractor.py
│   │   ├── field_extractor.py      # 关键字段提取（电话/邮箱/联系人/公司/团队成员）
│   │   └── docx_meta.py            # DOCX 元数据提取与对比 [P3]
│   │
│   ├── analysis/                   # 智能分析层
│   │   ├── similarity.py
│   │   ├── scorer.py               # RiskScorer（文本综合评分）
│   │   ├── structure_comparator.py # 章节结构相似度分析
│   │   ├── field_overlap_detector.py # 关键字段重叠检测（含团队成员）
│   │   ├── rare_token_analyzer.py  # 罕见汉字4-gram + 量化参数共现 [P3]
│   │   ├── price_analyzer.py       # 报价接近度检测 [P3]
│   │   ├── risk_synthesizer.py     # 多维度综合风险合成 [P3]
│   │   ├── whitelist_filter.py
│   │   └── keyword_extractor.py
│   │
│   └── chains/ / vectorstore/ / report/ / storage/
│
├── frontend/                       # React Web UI
│   └── src/pages/ReportPage/       # 风险报告展示页（含 RiskSynthesisPanel [P3]）
│
├── scripts/
│   └── validate_corpus.py          # 测试语料覆盖率矩阵验证脚本 [P3]
│
└── tests/
    └── unit/                       # 82 个单元测试
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
analyze_structure_and_fields   ← Phase 2/3：结构+字段+罕见序列+价格+元数据
  │
  ▼
filter_whitelist → embed_and_store → retrieve_similar_pairs → score_candidates
  │
  ├─[无候选对]──→ generate_report ──→ END
  │
  └─[有候选对]──→ llm_analyze_pairs ──→ generate_report ──→ END
                                              │
                                       RiskSynthesizer（Phase 3）
                                       整合所有信号 → 综合风险等级
```

### 工作流节点说明

| 节点 | 职责 |
|---|---|
| `parse_documents` | 调用 DocumentParser 提取原始文本 |
| `chunk_documents` | 自然段落切分 + 章节识别 + 类型分类 |
| `analyze_structure_and_fields` | 章节结构相似度 + 字段重叠 + 罕见序列 + 价格 + DOCX元数据 |
| `filter_whitelist` | 正则 + 向量两层白名单标记 |
| `embed_and_store` | BGE-M3 批量向量化，写入 ChromaDB |
| `retrieve_similar_pairs` | 跨文档向量检索，生成候选相似对 |
| `score_candidates` | 综合评分 + 过滤低风险对 |
| `llm_analyze_pairs` | 调用 Claude，生成中文判定理由（分析所有 ≥45 分对，上限 20 对） |
| `generate_report` | 调用 RiskSynthesizer 合成最终风险等级，汇总结构化风险报告 |
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

### 整体文档风险判定（Phase 3：综合多维度信号）

Phase 3 引入 `RiskSynthesizer`，将文本维度分数与非文本信号整合，任一强信号可直接触发风险升级：

**文本基础维度（Phase 2）**

| 条件 | 文本风险 |
|---|---|
| `similarity_rate ≥ 0.30` 或 `高风险对/总对数 ≥ 0.05` | 高风险 |
| `similarity_rate ≥ 0.15` 或 `(高风险对 ≥ 1 且 中风险对 ≥ 3)` | 中风险 |
| 其他 | 低风险 |

> `similarity_rate` = 被任意风险对（high/medium/low）覆盖的不重复 chunk 数 / 文档 A 总 chunk 数

**非文本信号升级规则（Phase 3）**

| 触发条件 | 最终判定 |
|---|---|
| 电话或邮箱精确重叠 | → **HIGH**（无论文本分） |
| 团队成员姓名精确重叠 ≥ 1 人 | → **HIGH** |
| 罕见汉字序列 / 量化参数共现 ≥ 2 项 | → **HIGH** |
| 报价接近度 ≤ 1%（疑似协同定价） | → **HIGH** |
| DOCX 文件作者或公司属性完全相同 | → **HIGH** |
| 结构分 ≥ 70 且文本雷同率 ≥ 30% | → **HIGH** |
| 结构分 ≥ 50 且字段模糊重叠 ≥ 1 项 | → **MEDIUM↑** |
| 文件修改时间差 ≤ 30 分钟且文本率 ≥ 15% | → **MEDIUM↑** |
| 报价接近度 ≤ 5% | → **MEDIUM↑** |

---

## 系统能力边界与检测矩阵

### 当前覆盖信号（Phase 3）

| 围标信号类型 | 检测维度 | Phase | 可信度 |
|---|---|---|---|
| 文字逐字复制 | 向量相似度 + 关键词重叠 | P1 | 高 |
| 语义改写（同义替换） | LLM 分析（≥45 分对，Chain-of-Thought） | P2 | 中~高 |
| 章节结构版式同源 | StructureComparator（Jaccard + 序列相似） | P2 | 中 |
| 联系电话 / 邮箱精确重叠 | FieldOverlapDetector 精确匹配 | P2 | 高 |
| 联系电话近似重叠（末位变换） | FieldOverlapDetector 模糊匹配（阈值 0.80） | P3 | 中 |
| 联系人 / 公司名重叠 | FieldOverlapDetector 精确 + 模糊 | P2 | 高 / 中 |
| 团队核心成员姓名重叠 | FieldOverlapDetector + 角色正则提取 | P3 | 高 |
| 表格参数完全一致 | 向量相似度（table_row chunk） | P1 | 高 |
| 罕见错别字 / 低频表述共现 | RareTokenAnalyzer 4-gram 罕见序列 | P3 | 高 |
| 量化参数精确复用（响应时限等） | RareTokenAnalyzer 数字+单位模式 | P3 | 高 |
| 报价协同定价（接近度分析） | PriceAnalyzer（≤1%→高，≤5%→中） | P3 | 高 |
| DOCX 文件作者 / 公司元数据相同 | DocxMetaExtract（core_properties） | P3 | 高 |
| 文件时间戳聚集（≤30分钟内完成） | DocxMetaExtract 修改时间差 | P3 | 中 |

### 检测盲区（当前局限）

| 盲区 | 说明 | 后续方向 |
|---|---|---|
| 价格梯度协同 | 仅检测两文档总价接近度，不分析多文档等差/等比分布 | 多文档矩阵模式扩展 |
| 联系人 NER | 依赖角色关键词上下文提取，无实体识别 | 接入 NER 模型 |
| 跨项目历史查重 | 当前仅比对本次上传文档 | 历史文档向量库 |
| all_vs_all 并行 | 多文档矩阵模式无并发优化 | LangGraph Send API |
| 图片/扫描件 | 不解析图片内嵌文字 | OCR 接入 |

---

## 报告输出字段（Phase 3）

Phase 3 报告在 Phase 2 基础上新增以下顶层字段：

```json
{
  "composite_risk": {
    "final_level": "high",
    "text_risk_level": "low",
    "triggered_signals": [
      "电话/邮箱精确重叠: phone = \"13812345678\"",
      "罕见序列匹配 3 项（含低频汉字4-gram和量化参数复用）"
    ],
    "signal_breakdown": { "text": "low", "field_overlaps": {...}, "rare_token": {...} }
  },
  "rare_token_analysis": {
    "risk_level": "high",
    "total_match_count": 3,
    "number_unit_matches": ["24小时响应", "600家供应商"],
    "matches": [{ "token": "核心处理能力", "token_type": "4gram", ... }]
  },
  "price_analysis": {
    "risk_level": "high",
    "total_a": 1000000,
    "total_b": 1005000,
    "proximity_ratio": 0.005,
    "is_price_coordinated": true
  },
  "meta_comparison": {
    "risk_level": "medium",
    "same_author": false,
    "is_timestamp_clustered": true,
    "time_gap_minutes": 12.5,
    "risk_notes": ["两份文档修改时间相差 12.5 分钟（≤30分钟），疑似同批次制作"]
  }
}
```

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
# 后端单元测试（82 个）
uv run pytest tests/unit/ -v

# 前端测试（48 个）
cd frontend && npm test

# 测试语料覆盖率矩阵（需提供语料，见 tests/corpus/README）
uv run python scripts/validate_corpus.py --corpus-dir tests/corpus/
```

---

## 报告输出示例

```json
{
  "task_id": "abc123",
  "overall_risk_level": "high",
  "overall_similarity_rate": 0.18,
  "risk_summary": { "high_count": 2, "medium_count": 5, "low_count": 3 },
  "composite_risk": {
    "final_level": "high",
    "text_risk_level": "medium",
    "triggered_signals": [
      "电话/邮箱精确重叠: phone = \"13812345678\"",
      "结构分 72.0/100 (≥70) + 文本雷同率 32.0% (≥30%)"
    ]
  },
  "structure_analysis": {
    "title_jaccard": 0.875,
    "sequence_similarity": 0.92,
    "overall_score": 72.0,
    "structure_risk_level": "high"
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
  "rare_token_analysis": {
    "risk_level": "medium",
    "total_match_count": 1,
    "number_unit_matches": ["24小时响应"]
  },
  "price_analysis": {
    "risk_level": "none",
    "proximity_ratio": null
  },
  "meta_comparison": {
    "risk_level": "none",
    "is_timestamp_clustered": false
  },
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

### Phase 3 — 围标深度信号 ✅
- [x] **Q1**: 罕见汉字序列共现检测（4-gram 低频共现 + 量化参数精确复用）
- [x] **Q2**: 价格异常分析（总报价接近度，≤1%→高风险，≤5%→中风险）
- [x] **Q3**: DOCX 文件元数据对比（作者、公司、修改时间戳聚集）
- [x] **Q4**: 扩展团队成员提取（架构师、实施顾问、测试工程师等 6 类角色）+ 电话模糊阈值 0.85→0.80
- [x] **Q5**: 综合风险合成器（RiskSynthesizer）—— 修复"非文本信号不参与最终判定"架构缺陷
- [x] **Q6**: LLM Prompt 新增 `error_replication`（错误复现）和 `key_number_duplicate` 风险类型

### Phase 4 — 规划中
- [ ] 多文档价格梯度分析（等差/等比分布检测）
- [ ] all_vs_all 并发优化（LangGraph Send API）
- [ ] 历史文档跨项目查重（持久化向量库）
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

**为什么需要综合风险合成器（Phase 3）？**
Phase 2 的 `overall_risk_level` 完全由文本分数决定，`structure_analysis` 和 `field_overlaps` 是纯装饰字段，不影响最终判定。当一对文档存在电话精确重叠（高风险）但文本经过语义改写（分数偏低）时，系统会错误输出 `low` 风险。`RiskSynthesizer` 解决了这个根本性问题——任何强信号（精确字段重叠、罕见序列共现、价格接近、元数据同源）都可以独立触发风险升级，不再依赖文本分数的"一票否决"。

**为什么检测罕见4-gram而非直接比较全文？**
全文 n-gram 覆盖大量模板词汇（法规引用、行业通用表述），信噪比极低。只有在单份文档内出现≤2次的罕见字符序列，才能区分"作者原创写法"与"模板内容"。两份文档出现相同罕见写法（尤其是相同错别字），在统计上几乎不可能是巧合，是最强的围标证据之一。
