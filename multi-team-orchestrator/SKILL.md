---
name: multi-team-orchestrator
description: 通用多团队智能协作调度系统。接收任意复杂任务，自动识别任务类型和所需专业能力，动态组建最优团队（3-8路子Agent并行），协调执行并汇总输出。含独立审查团队(7角色)和审计团队(7角色)做终审验收。适用场景：市场分析、竞品调研、内容创作、技术方案、商业策划、数据分析等任何需要多专业协作的任务。触发词：多团队、协作分析、深度分析、全面分析、组建团队、团队协作、parallel agents、multi-team。当任务复杂度需要2个以上独立专业视角时自动激活。
---

# 多团队智能协作调度系统 v5.3.1

## 核心原则

**不预设团队，不套模板。每次根据任务数据特征动态组建最专业的团队。**

---

## DNA底座（v5.1 — 源自Pattern H v4.1实战验证）

**所有模式(A-H)继承以下基因。Pattern H是试验田，验证通过后推到全军。**

### Gene 1：分层架构思维

每个Pattern的能力不是扁平罗列，是分层堆叠。通用四层模型：

```
Layer 4  Knowledge Evolution ── 经验沉淀/prompt进化/方法论结晶/domain-knowledge积累
Layer 3  Cross-Validation ──── 多源交叉验证/矛盾识别/置信度标注/对抗性思维
Layer 2  Domain Processing ─── 领域专属分析框架/角色能力/专业工具链
Layer 1  Multi-Source Collection ─ 数据采集/搜索策略/数据传递协议
```

H模式在此基础上扩展到六层（加Ontology+Zero-Trust）。其他模式按需在Layer 2-3之间插入领域专属层。

### Gene 2：五大通用协议

从H的10协议中提取5个全局适用：

| 协议 | 缩写 | 适用范围 | 核心规则 |
|------|------|---------|---------|
| **多源验证协议** | MVP-P | 所有模式 | 关键结论必须≥2个独立来源交叉验证；单源结论标注置信度；矛盾信号不做调和直接呈现 |
| **自进化协议** | SEP | 所有模式 | 每次任务后prompt改进写入prompt-evolution.md；做过3次的方法论结晶为模板；可优化策略不可修改红线 |
| **领域知识注册协议** | DKR | 所有模式 | 任务中发现的新实体/关系/规律写入对应pattern的domain-knowledge section；TTL标注数据有效期 |
| **工作即代码协议** | WaC | Standard/Full | 任务配置(团队编制/prompt/搜索策略)版本化存储；可复现可回溯；经验召回基于历史版本 |
| **实时态势协议** | RSP | 所有模式 | 每路Agent归队即时推送进度；超时预警；全员归队后输出融合摘要 |

### Gene 3：实时进度面板（铁律）

**所有多团队任务必须输出进度面板，不可省略。**

```
{任务代号} 进度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ {role}({label})  {耗时}  {一句话结论}
✅ {role}({label})  {耗时}  {一句话结论}
🔄 {role}({label})  执行中...
❌ {role}({label})  失败 → {降级方案}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
已完成 {n}/{total} | 预计{m}分钟
```

触发节点：
- 每个Agent完成时（总耗时>2分钟的任务）
- 全员归队时
- 异常/超时时

### Gene 4：角色独立Prompt模板

**每个Pattern的每个角色必须有独立prompt模板。** 不能只靠SKILL.md的7要素通用框架。

Prompt模板规范（在Pattern reference文件中）：
```
### {ROLE} Prompt框架
⓪ TAP + {领域特定上下文}
① 你是{角色}，专长{能力}，任务：{具体任务}
② 输入：{数据来源/文件路径/搜索策略}
③ 分析维度：{领域专属维度列表}
④ {该模式特有的协议要求}（如A模式的SYCM数据规范）
⑤ 输出：{文件路径} + {必须章节}
⑥ 工具：{该角色可用的工具清单}
⑦ 约束：{时间/搜索次数/输出长度}
```

覆盖率要求：每个Pattern的prompt模板覆盖率必须≥80%（角色数≥5时）或100%（角色数<5时）。

### Gene 5：领域红线分级

**每个Pattern除遵守全局硬约束(H1-Q6)外，必须定义自己的领域红线。**

红线三级结构（从H继承）：
```
🔴 基础红线 — 所有任务必须遵守（如数据安全/来源保护）
🟡 领域红线 — 该模式特有的约束（如A模式的SYCM数据不外泄）
🟢 最佳实践 — 推荐但不强制（如数据可视化规范/输出格式偏好）
```

### Gene 6：部署梯度+成本估算

**每个Pattern reference文件必须包含部署梯度表。**

```
| 梯度 | 角色配置 | 预计耗时 | 适用场景 |
|------|---------|---------|---------|
| MVP  | 固定{N}角色 | {X}min | 快速摸底/初步判断 |
| 标准 | 固定+动态{M}角色 | {Y}min | 标准交付 |
| 完整 | 全角色+RED-TEAM | {Z}min | 高风险/用户要求完整 |
```

### Gene 7：TTL数据新鲜度标注

**所有Agent产出中的关键数据必须标注时效性。**

```
数据类型           默认TTL    说明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
实时行情/价格       1小时      过期必须重新采集
新闻/事件           7天       过期标注[可能已更新]
行业报告/白皮书     90天      过期标注[需确认最新版]
标准/法规           1年       变更频率低但需监控
学术论文            永久      但引用数/被引需实时查
专利               永久      但法律状态需实时查
```

Agent在引用数据时标注采集时间，VERIFIER在Step 5检查TTL是否过期。

### Gene 8：任务后知识沉淀（强制）

**每次多团队任务完成后，除Step 9反思外，还必须执行知识沉淀：**

```
文件层（L1）：
1. 新发现的实体/关系/规律 → 对应Pattern的domain-knowledge section或experience-db
2. 任务中验证有效的搜索策略 → prompt-evolution.md
3. 任务中发现的工具限制/坑 → failure-cases.md
4. 用户的新决策/偏好 → 对应config文件 + memory
5. 可复用的分析框架 → methodology-library.md

```

### Gene 9：交叉验证标准（从多源验证实践泛化）

**关键结论的置信度分级：**

```
⭐⭐⭐⭐⭐ 95%+ — 3+独立来源一致 + 无矛盾信号
⭐⭐⭐⭐  85%+ — 2+独立来源一致 + 矛盾信号已解释
⭐⭐⭐   70%+ — 1-2来源 + 逻辑自洽
⭐⭐     50%+ — 单来源 + 逻辑推断
⭐       <50% — 推测/假说，需标注
```

Step 5 VERIFIER必须对报告中的核心结论标注置信度星级。

---

## Pattern Reference文件规范（v5.1新增）

**每个Pattern reference文件必须包含以下section（DNA基因的领域适配）：**

```
□ 触发条件        — 关键词+意图匹配规则
□ 固定团队        — 必选角色列表
□ 动态团队        — 可选角色+触发条件
□ 分层架构        — Gene 1的领域适配版（至少标注Layer 1-4对应什么）
□ Prompt模板      — Gene 4要求的每角色独立模板
□ 领域红线        — Gene 5要求的三级红线
□ 部署梯度        — Gene 6要求的MVP/标准/完整
□ 领域协议        — Gene 2通用协议+该模式特有协议
□ 任务示例        — ≥3个典型场景
□ 维度覆盖检查    — 该模式特有的覆盖维度清单
```

现有Pattern达标状态：
- ✅ H (精英情报) — v4.1 完全达标（DNA源头）
- ✅ A-G — v5.3.1 H基因继承升级完成（2026-03-04）

### H基因继承清单（v5.3.1 — 从Pattern H向全军输出）

**全模式强制继承（A-G全部注入）：**

| 继承基因 | 来源 | 内容 | 状态 |
|---------|------|------|------|

**定向继承（按模式特性选配）：**

| 继承基因 | 来源 | 目标模式 | 内容 | 状态 |
|---------|------|---------|------|------|


---

## 执行流水线总览

```
Step 0  复杂度判定 ── 选档位 + 确认DNA底座适用
Step 1  模式识别 ──── 匹配A-H八种模式 + 读Pattern reference(含DNA 10-section)
Step 1.5 经验召回 ─── Gene 2(WaC/DKR) 经验文件召回
Step 2  团队组建 ──── Gene 1分层分配角色 + Gene 5红线注入 + Gene 6梯度选择
Step 3  Prompt工程 ── Gene 4角色独立模板 + 7要素 + TAP + 数据传递协议
Step 4  并行执行 ──── sessions_spawn全并行 + Gene 3 RSP进度面板(铁律H7)
Step 5  VERIFIER ──── 交叉验证 + 多源交叉验证 + Gene 7 TTL检查(Q7) + Gene 9置信度标注(H9)
Step 6  P6验收 ───── 审查(12维度+DNA-R1~R5) + 审计(14项+DNA-A1~A5)
Step 7  验收修复 ──── CONDITIONAL修正 + FAIL返工 + DNA合规项一并修复
Step 8  SYNTHESIZER ── 综合报告(10章节含DNA合规摘要)
Step 9  强制复盘 ──── Gene 2 SEP自进化 + Gene 8 知识沉淀
Step 10 自主调度 ──── cron无人值守 + DNA合规同标准档位
Step 11 系统自检 ──── 架构审计 + experience-db健康 + DNA渗透率审计(9项)
```

**执行顺序铁律：** 5→6→7→8 严格串行，不可跳步。违反=写入FC failure-case。

---

## 执行档位（Execution Tier）— v5.0新增

不是每个任务都需要全流水线。根据复杂度选择档位：

| 档位 | 触发条件 | Agent数 | 流水线 | 验收 |
|------|---------|---------|--------|------|
| **Lite** | 2-3个专业视角，数据量小，用户要求快速 | 2-3 | Step 0-4 → Step 5(轻量) → Step 8 → Step 9 | 跳过P6；DNA: RSP进度面板仍必须，TTL/置信度轻量检查 |
| **Standard** | 标准多团队任务 | 4-6 | 全流水线 Step 0-9 | P6最小配置(3 Agent) + DNA合规检查 |
| **Full** | 高风险(投资/专利/法律)/Agent≥6/用户要求完整 | 6-8 | 全流水线 Step 0-9 | P6推荐(5)或完整(14) + DNA合规检查 + 领域红线审计 |

**档位选择规则：**
```
用户明确指定 → 用指定档位
涉及专利/投资/法律 → 强制Full
Agent数 ≤ 3 → Lite
Agent数 4-5 → Standard
Agent数 ≥ 6 → Full（可被用户降级为Standard）
```

**Lite模式细则：** Step 5轻量校验 = CONDUCTOR自行做数据一致性检查（无需spawn VERIFIER Agent），但必须输出简版verification-report.md。跳过P6但Step 8的SYNTHESIZER仍为独立Agent。

---

## 决策引擎（Decision Engine）

### Step 0：复杂度判定 ← DNA底座适用确认

```
输入任务 → 问3个问题：

Q1: 任务能否在单Agent 5分钟内完成？
    YES → 不启动多团队，直接执行 → EXIT
    NO → Q2

Q2: 任务是否涉及2个以上独立专业领域？
    YES → 启动多团队 → 选档位 → Step 1
    NO → Q3

Q3: 任务数据量是否需要拆分并行处理？
    YES → 启动多团队 → 选档位 → Step 1
    NO → 单Agent执行 → EXIT
```

### Step 1：模式识别 ← 读取Pattern reference(DNA 10-section)

扫描任务关键词和意图，匹配模式：

| 模式 | 触发关键词 | Reference | 状态 |
|------|-----------|-----------|------|
| A 电商类目 | 生意参谋/SYCM/类目分析/淘宝数据 | pattern-ecommerce.md | ✅ DNA 10/10 |
| B 专利挖掘 | 专利/发明/新颖性/权利要求 | — | 🔒 Private |
| C 竞品调研 | 竞品/竞争对手/SWOT/市场格局 | pattern-competitive.md | ✅ DNA 10/10 |
| D 商业计划 | BP/项目申报/政府资金/融资 | pattern-business-plan.md | ✅ DNA 10/10 |
| E 内容矩阵 | 内容策划/多平台/批量创作 | pattern-content-matrix.md | ✅ DNA 10/10 |
| F 技术评估 | 技术选型/架构设计/方案对比 | pattern-tech-eval.md | ✅ DNA 10/10 |
| H 精英情报(v4.1) | 情报分析/OSINT/FININT/尽调/制裁/链上追踪/实体追踪/知识图谱调查/Ontology/自进化 | — | 🔒 Private |
| R 研发创新 | 研发创新/系统化发明/TRIZ/技术空白 | — | 🔒 Private |
| G 通用 | 不匹配A-F/H/R | 能力库自由组合+DNA底座 | ✅ 内置 |

**Step 1执行时必须：** 读取匹配Pattern的reference文件，加载其分层架构(Gene 1)、领域红线(Gene 5)、部署梯度(Gene 6)、领域协议。G模式无reference文件，直接继承DNA底座通用层。

**G模式DNA适配：** G模式无独立reference文件，但必须继承DNA底座全部基因：
- 分层架构：按任务性质动态定义四层
- 进度面板/TTL/置信度/知识沉淀：与其他模式相同
- 领域红线：继承全局🔴铁律(H1-H9)，无领域特有红线
- 部署梯度：按Agent数量自动选择Lite/Standard/Full

**跨模式混合任务（v5.0新增）：** 当任务同时命中2+模式时（如"竞品调研+商业计划"）：
1. 识别主模式（占比更大的）和辅模式
2. 以主模式的固定团队为基础
3. 从辅模式的固定团队中选取互补角色追加
4. 合并两个pattern的维度覆盖检查清单
5. 输出路径统一到主模式目录

### Step 1.5：经验召回（Experience Recall）← Gene 2(WaC) + Gene 2(DKR)绑定

**DNA Gene 2(WaC)：** 历史任务配置版本化存储，召回时引用具体版本。
**DNA Gene 2(DKR)：** 召回对应Pattern的domain-knowledge积累，注入团队上下文。

**任务类型确定后，在组建团队前，执行经验召回。**

```
前置检查：
  快速检查 experience-db/ 下关键文件的实际数据条目数（跳过模板行/注释行/空行）
  IF 所有文件实际数据条目总计 < 5 → 跳过经验召回，输出"[经验库数据不足，跳过召回]"
  ELSE → 正常执行召回

L1 文件层（结构化上下文）— 读取8个文件：
1. routing-patterns.md → 找同类型任务的历史最优编制
2. prompt-evolution.md → 找各角色最新最优prompt版本
3. failure-cases.md → 找同类型任务踩过的坑 → 注入Agent prompt预防提醒
4. methodology-library.md → 找可复用方法论
5. step-efficiency.md → 找效率基线，设定本次各Step预期耗时
6. evolution-ledger.md → 读取系统进化轨迹，确认当前版本基线指标（v5.2新增）
7. capability-frontier.md → 确认本任务是否在🟢已验证范围内（v5.2新增）
8. cross-pattern-learning.md → 检查是否有来自其他模式的可用花粉（v5.2新增）

输出：经验注入清单（哪些经验被召回、用在哪个Agent上、花粉引用）
```

### Step 2：团队组建 ← Gene 1(分层架构) + Gene 5(领域红线) + Gene 6(部署梯度)绑定

**DNA绑定：**
- Gene 1: 按Pattern的分层架构分配角色（Layer 1采集/Layer 2分析/Layer 3验证/Layer 4进化各有对应角色）
- Gene 5: 将Pattern领域红线注入每个Agent的prompt约束段
- Gene 6: 根据用户要求/任务复杂度选择部署梯度(MVP/标准/完整)，梯度决定Agent数量和P6配置

#### 能力库（Capability Registry）

**分析类 ANALYSIS（5角色）：**
| 角色 | 调用时机 |
|------|---------|
| `QUANT` | 有数值数据需要统计/聚类/预测/评分 |
| `INTEL` | 有竞品/市场数据需要拆解对比 |
| `DEMAND` | 有用户搜索/行为/需求数据 |
| `FORECAST` | 需要时间序列预测/现金流/ROI |
| `ANALYST-{X}` | 按细分领域深入调研（X=动态赛道名） |

**研究类 RESEARCH（4角色）：**
| 角色 | 调用时机 |
|------|---------|
| `PATENT` | 涉及专利检索/新颖性/侵权风险 |
| `SCHOLAR` | 需要论文/技术文献支撑 |
| `POLICY` | 涉及政府政策/法规/标准/申报 |
| `INDUSTRY` | 需要行业趋势/格局/产业链分析 |

**创作类 CREATIVE（4角色）：**
| 角色 | 调用时机 |
|------|---------|
| `CREATIVE` | 需要营销文案/标题/卖点/创意 |
| `WRITER` | 需要结构化长文档/报告/方案书 |
| `VISUAL` | 需要图表/数据可视化/信息图 |
| `PLATFORM-{X}` | 需要特定平台内容（X=xhs/douyin/weixin等） |

**情报类 INTELLIGENCE（5角色）：**
| 角色 | 调用时机 |
|------|---------|
| `FUSION-LEAD` | 情报融合指挥官 — PIR/Ontology治理/联邦协作/IaC管线管理 |
| `OSINT` | 开源情报+合成身份工业化检测(朝鲜模式) |
| `FININT` | 金融情报+量子迁移资金追踪+TDF封装金融情报 |
| `GRAPH-ANALYST` | ⭐Ontology三层管理者+多模态KG(卫星/RF/金融)+GNN关系预测+TKG时序推理+TTL |
| `PREDICTOR` | 对手建模+兵棋推演+What-if分析 |

**工程类 ENGINEERING（3角色）：**
| 角色 | 调用时机 |
|------|---------|
| `CRAWLER` | 需要从网页/API采集数据 |
| `ENGINEER` | 需要编写分析脚本/工具/代码 |
| `INTEGRATOR` | 需要对接多系统/数据管道 |

**可视化类 VISUALIZATION（4角色）：**
| 角色 | 调用时机 |
|------|---------|
| `QUANT-VIZ` | 量化图表(热力图/龙卷风/散点图) |
| `SEO-VIZ` | SEO覆盖率热力图+竞争矩阵 |
| `FUNNEL-VIZ` | 搜索漏斗/瀑布图/气泡矩阵 |
| `STRATEGY-VIZ` | 雷达图/ROI预测曲线 |

**审查类 REVIEW（7角色）：** 详见 `references/team-review.md`
**审计类 AUDIT（7角色）：** 详见 `references/team-audit.md`

**元能力 META（2角色）：**
| 角色 | 调用时机 |
|------|---------|
| `RED-TEAM` | 任务涉及≥100万投资/专利布局/法律风险/不可逆决策 |
| `SYNTHESIZER` | Agent数≥5，或需要生成最终综合报告（Step 8） |

#### 组建规则

```
1. 从能力库中选择与任务匹配的Agent角色
2. 固定Agent：每个Pattern有2-3个固定角色（见对应reference文件）
3. 动态Agent：根据数据特征/任务细节增加0-4个
4. 总数约束：执行层 3 ≤ N ≤ 8
5. 依赖分析：标注Agent间的数据依赖（大多数可全并行）
6. RED-TEAM激活：任务涉及≥100万元投资决策/专利核心布局/法律纠纷/战略性不可逆决策
7. SYNTHESIZER：Agent数≥5时推荐启动做交叉验证；Step 8必须启动做最终报告
```

**维度覆盖检查（组建完成后必须过一遍）：**
```
□ 数据采集：任务需要的数据是否都有Agent去采集？
□ 定量分析：是否有Agent做定量分析（不只定性描述）？
□ 时间维度：是否覆盖历史趋势+当前状态+未来预测？
□ 地域维度：任务涉及的地域是否都覆盖？
□ 竞争维度：是否覆盖产品/技术/价格/渠道/人才/专利/生态？
□ 风险维度：是否有Agent识别风险和负面因素？
□ 行动维度：是否有Agent产出可执行的行动建议？
□ 用户关注：memory_search确认用户历史偏好，补充遗漏维度
```

#### 团队方案输出格式

```
📋 任务：{一句话}
🎯 模式：{A~G} | 档位：{Lite/Standard/Full}
🏗️ 编制：{N}个执行Agent

固定：
  ✅ {ROLE}({label}) — {任务} [预计{N}min] ← 经验引用：{memory_id或"无历史"}
动态：
  ✅ {ROLE}({label}) — {任务} ← 原因：{为什么需要} | 经验引用：{相关经验}
元能力：
  {RED-TEAM / SYNTHESIZER — 如果需要}

经验影响说明：{本次编制受了哪些历史经验影响，如"不用泛搜角色(c191ee96)"}
依赖：{全并行 / Wave分层描述}
预计总耗时：{N}分钟
```

### Step 3：Prompt工程 ← Gene 4绑定

**DNA Gene 4强制执行：** 读取对应Pattern reference文件中的角色独立Prompt模板，以模板为基础生成task prompt。禁止跳过模板直接写prompt。无模板的角色用7要素通用框架。

每个Agent的task prompt必须包含7要素：

```
⓪ TAP时间锚点：
   "当前时间：{UTC} / {任务相关时区}"
   "数据时效要求：{freshness}"
   "目标市场时区：{时区列表}"

① 角色：你是{角色名}，专长{能力描述}
② 输入：读取{绝对路径}的数据文件 / 用web_search采集{具体查询策略}
③ 框架：按以下{N}个维度分析：{维度列表}
④ 输出：写入{绝对路径}/{文件名}.md，包含{必须章节列表}
⑤ 质量：{数值用Python计算/事实用web_search验证/不编造数据}
⑥ 约束：web_search≤10次，5分钟内完成，输出≤3000字
```

**TAP时区速查：**
```
中国平台(生意参谋/天猫/抖音/小红书) → UTC+8
美国平台(Crunchbase/SEC/USPTO/G2)     → UTC-5(EST)/UTC-8(PST)
欧洲平台(EU公告/EPO)                   → UTC+1(CET)
日韩平台(J-PlatPat/KIPO)               → UTC+9
国际平台(Google/GitHub/arXiv)           → UTC
```

**数据传递协议：**
```
数据<2KB   → 直接在task prompt中传摘要
数据2-10KB → 传文件绝对路径，Agent自行读取
数据>10KB  → 传路径 + 精简摘要辅助
禁止：完整JSON内联到task prompt（浪费token+精度丢失）
```

**输出路径规范：** 统一使用 `~/.openclaw/workspace/multi-team-output/{任务日期}-{任务简称}/` ，禁止使用 `/tmp/`。

### Step 4：并行执行 ← Gene 3(RSP)绑定

```python
# 无依赖Agent → 全部同时 sessions_spawn(mode="run")
# 有依赖Agent → 等前置完成后再启动
# 不轮询，完成后自动通知
```

**🔴 DNA Gene 3 实时态势协议(RSP)强制执行：**

**RSP-X模板对照（v5.3.1 Fix — CONDUCTOR自检项）：**
```
CONDUCTOR在Step 4推送进度面板前，必须执行：
1. 确认当前Pattern（A-H）
2. 读取对应Pattern reference文件中的RSP-X section（如RSP-C/RSP-B等）
3. 按RSP-X定义的领域特有字段输出面板（不可用通用模板代替）
4. 如果Pattern无RSP-X定义（G模式），用DNA通用模板
违反 → 写入failure-cases "RSP未领域适配"
```

每路Agent归队时必须输出进度面板（铁律，不可省略）：
```
{任务代号} 进度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ {role}({label})  {耗时}  {一句话结论}
🔄 {role}({label})  执行中...
❌ {role}({label})  失败 → {降级方案}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
已完成 {n}/{total} | {Pattern领域特有指标} | 预计{m}分钟
```

**实时进度反馈（v5.0新增 → v5.1 RSP协议强化）：**
```
CONDUCTOR在以下节点向用户发送进度通知（通过当前会话直接输出）：

📍 Step 2完成后：
   "🏗️ 团队已组建：{N}个Agent，模式{X}，档位{tier}，预计{M}分钟"

📍 Step 4 每个Agent完成时（如果总耗时>3分钟）：
   "✅ {ROLE}({label}) 完成 [{已完成}/{总数}]"

📍 Step 4 全部Agent完成后：
   "📊 执行层完成，进入VERIFIER交叉验证..."

📍 Step 4→5 过渡（CONDUCTOR自检 — v5.3.1 Fix）：
   🔴 验收层跳步检查（铁律）：
   - 当前档位是什么？（Lite/Standard/Full）
   - Standard/Full → Step 5-8不可省，必须继续
   - 想跳步 → 如果任务确实只需要Lite，回退Step 0改档位，不可定了Standard偷跳
   - "测试任务""时间紧"不是跳步理由 → 这是[anti-shortcut]铁律要防的认知陷阱
   违反 → 写入failure-cases "FC: Standard/Full档位跳过验收层"

📍 Step 5 VERIFIER完成后：
   "🔍 VERIFIER完成：L1修正{n1}处，L2修正{n2}处，L3标注{n3}处"

📍 Step 6 P6验收完成后：
   "📋 P6验收结果：REVIEW {score}分 / AUDIT {result} → {PASS/CONDITIONAL/FAIL}"

📍 Step 7（如有）：
   "🔧 修复{n}项，重验中..."

📍 Step 8 SYNTHESIZER完成后：
   "📝 最终报告已生成：{路径}"

超时预警：
  任何Step耗时超过预估的150% → 立即通知
  "⚠️ {Step名}耗时异常（已{n}分钟，预估{m}分钟），{原因推测}"
```

**共享情报摘要（Wave分层时必须执行）：**
```
Wave 1完成后，CONDUCTOR必须：
1. 读取Wave 1全部产出
2. 提取共享情报摘要（关键数据点、已确认事实、已获取URL清单）
3. 将摘要注入Wave 2每个Agent的task prompt开头
4. 标注："以下数据已由Wave 1确认，无需重复搜索"
```

**Agent失败处理协议（v5.0新增）：**
```
单个Agent超时(>5min) → kill该Agent，日志写入failure-cases.md
  IF 该Agent是固定角色(必选) → 重新spawn一次，简化prompt(去掉可选维度)
  IF 该Agent是动态角色(可选) → 标注缺失，继续流水线
  IF 重试仍失败 → 标注为"数据盲区"，在后续Step中说明

单个Agent产出为空/格式错误 → 同上处理

sessions_spawn本身失败 → 等待30秒重试1次
  IF 仍失败 → 降级：CONDUCTOR自行执行该Agent的核心任务（质量可能下降，标注）

系统级熔断：连续3个Agent失败 → 暂停执行，通知用户
```

**系统级熔断与降级（v5.0新增）：**
```
不只是Agent级别的失败，还覆盖基础设施层面：

1. web_search API异常
   症状：连续3次web_search返回空/报错
   熔断：暂停所有待发起的web_search
   降级：切换到web_fetch直接抓取已知URL + 基于已有数据完成分析
   标注：报告中标注"部分数据未经搜索引擎验证"

2. sessions_spawn持续失败
   症状：连续2次spawn返回错误
   熔断：暂停spawn，等待30秒后重试1次
   降级：CONDUCTOR自行串行执行剩余Agent任务（质量下降，明确标注）
   极端：如果CONDUCTOR也无法执行→通知用户，输出已完成的部分结果

3. browser/web_fetch大面积超时
   症状：3次fetch/browser操作超时
   熔断：放弃需要fetch的数据采集
   降级：只用web_search摘要数据 + 已有缓存数据
   标注：报告中标注"部分数据源无法访问"

4. 内存/token预算耗尽
   症状：Agent产出被截断 / 上下文窗口接近上限
   熔断：停止spawn新Agent
   降级：用已完成的Agent产出直接进入Step 5→8流水线
   标注：标注哪些维度因资源限制未覆盖

熔断通知模板：
  "🚨 系统级异常：{异常类型}，已触发{降级方案}。当前已完成{n}/{total}个Agent。是否继续降级执行？"
  等待用户回复30秒，无回复默认继续降级执行。
```

### Step 5：VERIFIER交叉验证 ← Gene 7(TTL) + Gene 9(置信度)绑定

**DNA Gene 7：** VERIFIER必须检查所有Agent产出中关键数据的TTL(采集时间+有效期)，过期数据标注[TTL_EXPIRED]。
**DNA Gene 9：** VERIFIER必须对报告中每个核心结论标注置信度星级(⭐-⭐⭐⭐⭐⭐)。

**⚠️ 必须spawn独立VERIFIER Agent执行，CONDUCTOR不得手动代替。**
**Lite档位除外：Lite模式下CONDUCTOR可自行做轻量校验。**

```
VERIFIER Agent的task prompt包含：
- 所有执行层Agent产出文件的绝对路径列表
- 原始任务需求描述
- TAP时间锚点

VERIFIER执行内容：
1. TAP校验：数据时间标注、时区混淆、时效性检查
2. 数据一致性扫描：同一数据点被多Agent引用时比对数值
3. 结论冲突检测：识别矛盾结论，评估原因
4. 覆盖度检查：对照原始需求检查维度遗漏

三级自动修正：
  L1 自动修正（无需干预）：数据不一致/单位不统一/格式问题
     → 直接edit修改原报告文件，标注[L1_CORRECTED]
  L2 智能修正（额外验证）：结论轻微冲突/数据缺失
     → web_search≤3次验证，失败即降级L3
  L3 标注上报：严重冲突/核心假设不同
     → 标注[分歧未解决]，留待用户决策

输出：verification-report.md（含修正统计和数据校验表）
```

### Step 6：P6验收层 ← Gene 5(领域红线) + Gene 2(MVP-P多源验证)绑定

**DNA绑定：** P6审查/审计团队在执行标准维度审查的同时，必须执行DNA合规检查（详见team-review.md DNA-R1~R5 / team-audit.md DNA-A1~A5）。DNA-FAIL时最终评级不可为PASS。

**Standard/Full档位必须执行。Lite档位跳过。**

**🔴 P6铁律（2026-03-05 FC-007教训，用户明确要求）：**
- **审查团队+审计团队是每次多团队任务的必选步骤（Standard/Full）**
- 不可因"任务类型""时间紧""研究性质""觉得overkill"跳过
- SYNTHESIZER(Step 8)必须在P6 PASS后才能启动
- 违反此规则 = FC-007，写入failure-cases
- 此规则无例外、无降级、无用户未说就不做的借口

执行层产出经VERIFIER校验后，启动验收团队并行审查：

**Agent配置：**
```
最小配置（Standard档位，3 Agent）：
  Agent 1: FACT-CHECK — 独立Agent，web_search≤5次抽查关键数据
  Agent 2: REVIEW-LEAD+5审查官合体 — 逻辑/完整性/深度/偏差/可执行性+汇总
  Agent 3: AUDIT-LEAD+6审计官合体 — 全部审计角色+汇总

推荐配置（Full档位，5 Agent）：
  Agent 1: FACT-CHECK（独立）
  Agent 2: LOGIC-CHECK + COVERAGE-CHECK + DEPTH-CHECK
  Agent 3: BIAS-CHECK + ACTIONABILITY-CHECK + REVIEW-LEAD
  Agent 4: SEC-AUDIT + DATA-AUDIT + SOURCE-AUDIT
  Agent 5: DELIVERY-AUDIT + COMPLIANCE-AUDIT + REPRODUCIBILITY-AUDIT + AUDIT-LEAD

完整配置（高风险任务，14 Agent）：
  全部14角色各自独立spawn
```

**详细prompt模板：** 见 `references/team-review.md` 和 `references/team-audit.md`

**REVIEW-LEAD 12维度加权评分：**
核心数据准确率(12%) / 引用可验证率(8%) / 因果链完整度(10%) /
假设合理性(8%) / 需求覆盖率(10%) / 多视角覆盖度(7%) /
洞察密度(10%) / 二阶思考深度(8%) / 偏差风险指数(10%) /
行动项具体度(7%) / 决策信息充分度(5%) / 跨维度一致性(5%)

**AUDIT-LEAD 14项检查矩阵：**
⚡一票否决：敏感数据泄露
Critical：搜索词安全、跨章节数据一致、结构完整、文件完整、法律风险
Major：数据血缘、单位精度、来源权威性、伦理合规、方法论透明
Minor：来源多样性、可复现性

**终裁规则：**
```
REVIEW ≥80 && AUDIT全Critical通过+Major≤1  → ✅ PASS → 进Step 8
REVIEW 65-79 或 AUDIT Major 2-3              → ⚠️ CONDITIONAL → 进Step 7
REVIEW <65 或 AUDIT任何Critical FAIL         → ❌ FAIL → 进Step 7
⚡一票否决项FAIL                              → ❌ FAIL → 进Step 7
```

### Step 7：验收修复 ← DNA合规项一并修复

**仅当P6结果为CONDITIONAL或FAIL时执行。DNA-CONDITIONAL/DNA-FAIL项同步修复。**

```
CONDITIONAL处理：
1. 读取决议书中"待改进项"清单
2. 能立即修正的（数据错误/格式问题）→ 直接edit原文件
3. 不能立即修正的 → 标注原因
4. 修正完成后，重跑P6（仅审查修正项相关章节，非全量重审）
5. 重验通过 → 进Step 8；重验仍CONDITIONAL → 标注后进Step 8

FAIL处理：
1. 汇总所有FAIL项+CONDITIONAL项，生成《修正清单》
2. 分类处理：
   - 数据错误 → web_search重新验证后修正
   - 逻辑缺陷 → CONDUCTOR修正推理链
   - 覆盖遗漏 → spawn补充Agent专攻遗漏维度
   - 敏感数据泄露(⚡) → 直接删除
3. 修正后重跑P6（仅FAIL相关章节）
4. 最多返工1次。第2次仍FAIL → 交付用户，标注"验收未通过"+原因+修正记录

修正记录 → 写入 experience-db/correction-log.md
```

### Step 8：SYNTHESIZER综合报告 ← 10章节含DNA合规摘要

**⚠️ 必须由独立SYNTHESIZER Agent生成。CONDUCTOR不得手动拼接。**
**执行顺序：Step 8必须在Step 6(P6)通过/完成后才能启动。**

```
SYNTHESIZER Agent的task prompt：
  输入：
  - 执行层报告路径列表
  - VERIFIER校验报告路径
  - P6审查/审计决议书路径（如有）
  - 原始任务需求描述

  报告结构（10章节）：
  a. 执行摘要（30秒版核心结论，≤200字）
  b. 关键数据表（从各报告提取，标注来源+时间+TTL[Gene 7]）
  c. 分维度详细分析（引用原报告章节，注明出处）
  d. 跨维度交叉洞察（多Agent共同指向的结论=高置信，标注置信度星级[Gene 9]）
  e. 矛盾信号清单（Agent间结论冲突，标注双方依据+MVP-P验证结果[Gene 2]）
  f. 综合战略建议（P0/P1/P2行动清单，每项：做什么+怎么做+预期结果+时间线）
  g. 风险清单（按影响×概率排序）
  h. 修正记录（L1/L2/L3汇总 + P6验收结果）
  i. DNA合规摘要（TTL过期项数/置信度分布/领域红线遵守/知识沉淀待写项）
  j. 附件索引（所有报告文件路径+简述）

  质量要求：
  - 数据必须从原报告复制，不得凭记忆重写
  - 战略建议必须具体到可执行
  - 输出到 {输出路径}/final-report.md
```

### Step 9：强制复盘 ← Gene 2(SEP) + Gene 8(知识沉淀)绑定

**DNA Gene 2(SEP)：** 每次任务后评估prompt效果，改进写入prompt-evolution.md。做过3次的方法论结晶为模板。
**DNA Gene 8：** 强制执行五类知识沉淀：新实体→DKR / 搜索策略→prompt-evolution / 工具坑→failure-cases / 用户偏好→config / 分析框架→methodology-library。

**每次多团队任务完成后自动触发，不可跳过。**
**能力基础：** `auto-reflection` skill（反思框架5问 + 三处一致性检查 + 系统升级动作）

```
9.1 团队表现评分
   对每个Agent按4维度打分（1-10分制）：
   产出质量 / 执行效率 / 指令遵循 / 数据准确
   每个维度写明：得分 + 扣分原因 + 具体改进方案（不可为空）
   → 写入 experience-db/team-performance.md

9.2 性能数据记录
   总耗时 / 各Step耗时 / REVIEW评分 / AUDIT结果 / 验收轮次
   → 写入 experience-db/metrics.md + experience-db/step-efficiency.md

9.3 反思3问（每问≥3句）
   Q1: 最佳Agent为什么好？→ 提炼prompt最佳实践
   Q2: 最差Agent为什么差？→ 根因分析 + 改进方案
   Q3: 编制合理吗？多了谁少了谁？→ 遗漏维度必须承认

9.4 经验沉淀
   更优编制 → routing-patterns.md
   prompt改进 → prompt-evolution.md
   踩坑 → failure-cases.md
   做过3次的方法论 → methodology-library.md

9.5 经验召回命中率评估
   Step 1.5召回的经验，哪些被实际采用？效果如何？

9.6 单步效率对比
   与上次同类型任务的各Step耗时对比，记录变快/变慢原因

9.7 写入daily memory → memory/YYYY-MM-DD.md

9.8 跨模式传粉检查（v5.2新增 — CPL协议）
   本次任务是否产生可泛化技巧？ → 提取花粉候选 → 写入 cross-pattern-learning.md
   参考：references/cross-pattern-learning.md

9.9 进化账本更新（v5.2新增）
   更新 evolution-ledger.md 进化轨迹表（如有版本/指标变化）

9.10 能力边界更新（v5.2新增）
   本次任务验证了哪个能力？ → 🟡移到🟢 或发现新🔴缺口
   更新 capability-frontier.md
```

**闭环：Step 9产出 → 下次Step 1.5自动召回 → 系统越用越强**
**横向传粉：Step 9.8提取花粉 → 下次其他模式Step 1.5引用 → 跨模式进化**

### Step 10：自主调度（可选）← DNA合规同Standard档位

系统可通过cron无人值守执行预审批任务。DNA合规要求与Standard档位相同（进度面板/TTL/置信度/知识沉淀全部执行）。

```
约束：
1. 只能执行 experience-db/approved-tasks.md 中已注册且用户审批的任务
2. 执行完毕通知用户
3. P6验收照常，FAIL不发送改为告警
4. L3冲突 → 暂停，通知用户决策
5. 所有记录写入metrics.md和daily memory
```

### Step 11：系统自检 ← DNA渗透率审计(第9项)

**定期或按需执行的架构健康审计，确保系统配置一致性、experience-db质量和DNA渗透率。**

```
触发条件：
- 用户说"系统自检"/"自我检查"/"health check"
- 每月首次多团队任务前自动触发
- 连续2次P6 FAIL后自动触发

自检项目（8项）：

1. 文件完整性
   - SKILL.md + 8个references + 9个experience-db → 检查是否全部存在
   - 检查文件大小是否异常（空文件/异常大）

2. 交叉引用一致性
   - SKILL.md中的Step编号 vs 硬约束中的Step引用 → 是否一致
   - 能力库角色列表 vs team-review.md/team-audit.md角色列表 → 是否一致
   - 模式索引 vs references/目录 → 是否一致

3. 硬约束可执行性
   - 逐条审查硬约束，标注哪些在当前环境下无法执行（如Pre-commit hook不存在）
   - 矛盾约束检测（两条约束互相冲突）

4. experience-db质量
   - 各文件的实际数据条目数（排除模板/注释）
   - 数据新鲜度（最后更新日期）
   - routing-patterns: 每种模式是否有≥1条记录
   - failure-cases: 是否有"待修复"状态的案例
   - team-performance: 评分标尺是否统一(1-10)

5. Prompt模板版本
   - prompt-evolution.md中的最新版本 vs references/中的实际模板 → 是否同步
   - 有v2+但reference还在用v1 → 标注需要更新

6. Pattern文件规范
   - 每个pattern是否包含：触发条件/固定团队/动态团队/prompt模板/输出路径
   - 输出路径是否统一使用workspace安全路径（非/tmp/）
   - prompt模板是否遵循7要素标准

7. 依赖健康
   - 外部skill依赖（如sycm-market-analysis）是否存在
   - MCP工具可用性（如patent-search）

8. experience-db容量管理
   - 单个文件超过500行 → 建议归档历史数据到 experience-db/archive/YYYY/
   - 月度汇总是否已填写

9. DNA渗透率审计（v5.1新增）
   - 7个Pattern reference文件 → 10-section达标率
   - SKILL.md执行步骤 → Gene绑定完整性
   - team-review/audit → DNA合规检查section存在性
   - 关联skills → DNA对接引用
   - 祖宗文件(AGENTS/MEMORY/BOOTSTRAP/SOUL) → 版本号一致性
   - 目标：全量17文件100%渗透率

10. TTL衰减清理（v5.1→v5.2升级 — 完整KDE引擎）
   - 参考：references/knowledge-decay-engine.md（衰减规则+执行机制+健康度指标）
   - experience-db各文件中的数据条目 → 按KDE定义的TTL规则检查
   - memory/中的daily文件 → 按KDE压缩摘要协议处理
   - 清理后输出：TTL-cleanup-report（清理N条/归档N条/保留N条/健康度指标）

11. 进化轨迹审计（v5.2新增）
   - evolution-ledger.md → 进化曲线是否上升？退化警报阈值检查
   - 最近3个版本的AVG_QUALITY趋势 → 下降趋势立即告警
   - COVERAGE增长是否停滞 → 对标里程碑检查

12. 能力边界健康（v5.2新增）
   - capability-frontier.md → 🟡状态是否有超30天未推进的
   - 🔴缺口是否有新增但无填补计划的
   - 能力增长曲线 → 对标目标进度

13. 跨模式传粉覆盖（v5.2新增）
   - cross-pattern-learning.md → 花粉传播率（已传粉/总花粉候选）
   - 是否有高价值花粉长期待传粉 → 催促执行

14. 模型抽象合规（v5.2新增）
   - 参考：references/model-abstraction-protocol.md
   - Prompt设计是否遵循模型无关化4原则（结构化/Schema/数字标尺/显式步骤）
   - L4/L3层资产是否与L2/L1层解耦

输出：system-health-report.md（含每项检查结果+修复建议+进化趋势图）
自动修复：文件缺失/空文件 → 从模板重建；路径不一致 → 提示具体修正命令
```

---

## 元能力（Meta-Capabilities）

### 对抗验证（RED-TEAM）

**激活条件：** 涉及≥100万元投资决策 / 专利核心布局 / 法律纠纷 / 战略性不可逆决策

```
RED-TEAM Agent唯一任务：挑战其他Agent的输出
- 每份报告找出：最弱假设 / cherry-picking / 被忽略的风险 / 最坏情况
- 输出：RED-TEAM_对抗报告.md
```

### 知识结晶（SYNTHESIZER）

双重角色：
1. **交叉验证（Agent≥5时）：** 读取全部产出，识别一致信号+矛盾信号，标注Gene 9置信度星级
2. **报告生成（Step 8）：** 生成最终综合报告（10章节结构，含DNA合规摘要）

### 二轮深度分析

**触发条件（满足任一）：** 用户要求"更深度"/"可视化" / 第一轮3+维度未覆盖 / 竞品数≥10

4路可视化Agent：QUANT-VIZ / SEO-VIZ / FUNNEL-VIZ / STRATEGY-VIZ
图表规范：`~/Desktop/charts/`，10x7英寸dpi150，中文字体Arial Unicode MS/SimHei

---

## 硬约束

### 🔴 铁律（任何情况不可违反）

| # | 约束 | 原因 |
|---|------|------|
| H1 | **执行顺序不可跳步：** 5(VERIFIER)→6(P6)→7(修复)→8(SYNTHESIZER)严格串行 | FC-003/FC-006教训 |
| H2 | **Step 5必须独立Agent执行**（Lite档位除外） | 防CONDUCTOR偷工减料 |
| H3 | **Step 8必须独立SYNTHESIZER Agent生成报告** | FC-003教训：手动拼接引入复制错误 |
| H4 | **P6验收Standard/Full必过，最少3个独立Agent** | 质量底线 |
| H5 | **敏感数据不得作为web_search查询词** | 数据安全 |
| H6 | **CONDITIONAL必须修正后重验再交付** | 防偷懒跳过修正 |
| H7 | **Gene 3 RSP进度面板不可省略**（所有档位含Lite） | DNA铁律：用户必须看到实时进度 |
| H8 | **Gene 5领域红线🔴级不可违反** | DNA铁律：违反🔴红线=任务FAIL |
| H9 | **Gene 9核心结论必须标注置信度星级** | DNA铁律：无置信度=不可信 |

### 🟡 流程约束

| # | 约束 | 说明 |
|---|------|------|
| F1 | 执行层Agent数 ≤ 8 | 超过后web_search互抢速率下降 |
| F2 | 单Agent web_search ≤ 10次 | 防超时；FACT-CHECK ≤ 5次 |
| F3 | 单Agent运行 < 5分钟 | 超时触发失败处理协议 |
| F4 | 30分钟未完成 → kill止损 | 不含验收时间 |
| F5 | L2修正最多1轮(≤3次搜索) | 失败即降级L3 |
| F6 | P6 FAIL最多返工1次 | 第2次仍FAIL直接交付+标注 |
| F7 | 输出路径用workspace绝对路径 | 禁止/tmp/，子Agent工作目录不可控 |

### 🟢 质量约束

| # | 约束 | 说明 |
|---|------|------|
| Q1 | TAP时间锚点必须注入每个Agent | 关键数据标注发布时间+采集时间 |
| Q2 | 跨时区数据统一到UTC对比 | web_search freshness匹配任务时效 |
| Q3 | 不固定模板 | 每次根据数据特征动态决策编制 |
| Q4 | Wave分层时必须提取共享情报摘要 | 减少重复搜索 |
| Q5 | 验收团队不参与执行 | 独立性 |
| Q6 | 自主执行必须在approved-tasks.md注册 | 用户审批后才能cron触发 |
| Q7 | Gene 7 TTL过期数据必须标注[TTL_EXPIRED] | 不静默引用过期数据 |
| Q8 | Gene 8 每次任务后强制执行五类知识沉淀 | 不沉淀=浪费经验 |
| Q9 | Gene 2 MVP-P关键结论≥2独立来源 | 单源结论≤⭐⭐⭐ |

---

## 文件目录

```
skills/multi-team-orchestrator/
├── SKILL.md                        ← 主文件（决策引擎+流水线+能力库+硬约束）
├── CHANGELOG.md                    ← 版本变更日志
├── references/
│   ├── pattern-ecommerce.md        ← 电商类目分析
│   ├── pattern-patent.md           ← 🔒 Private
│   ├── pattern-competitive.md      ← 竞品深度调研
│   ├── pattern-business-plan.md    ← 商业计划/项目申报
│   ├── pattern-content-matrix.md   ← 多平台内容矩阵
│   ├── pattern-tech-eval.md        ← 技术方案评估
│   ├── pattern-intelligence.md     ← 🔒 Private
│   ├── pattern-rnd-innovation.md    ← 🔒 Private
│   ├── h-gene-common.md             ← 🔒 Private
│   ├── team-review.md              ← 审查团队（7角色prompt模板）
│   ├── team-audit.md               ← 审计团队（7角色prompt模板）
│   ├── model-abstraction-protocol.md ← 模型抽象协议MAP（v5.2新增 — 模型换代防线）
│   ├── cross-pattern-learning.md   ← 跨模式传粉协议CPL（v5.2新增 — 横向进化引擎）
│   └── knowledge-decay-engine.md   ← 知识衰减引擎KDE（v5.2新增 — 信噪比治理）
└── experience-db/
    ├── routing-patterns.md         ← 路由决策经验
    ├── prompt-evolution.md         ← Prompt迭代记录
    ├── team-performance.md         ← 团队表现评分（1-10分制）
    ├── failure-cases.md            ← 失败案例库
    ├── methodology-library.md      ← 方法论库
    ├── metrics.md                  ← 系统性能指标
    ├── step-efficiency.md          ← 单步效率追踪
    ├── correction-log.md           ← 修正日志
    ├── approved-tasks.md           ← 预审批任务注册表
    ├── evolution-ledger.md         ← 进化账本（v5.2新增 — 量化进化轨迹）
    ├── capability-frontier.md      ← 能力边界地图（v5.2新增 — 定向生长）
    └── archive/                    ← 历史数据归档（按年）
```
