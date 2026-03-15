# CHANGELOG

## Orchestrator v5.2 — 自进化六齿轮 — 2026-03-03

**核心命题：** 让系统具备不依赖特定模型的自进化能力。模型是燃料，系统是引擎。

### 新增6个自进化齿轮
1. **进化账本** (experience-db/evolution-ledger.md)
   - 量化进化轨迹：VERSION/ROLES/PATTERNS/GENES/QUALITY/COVERAGE等13项指标
   - 退化警报阈值：AVG_QUALITY连续下降/FC学习率<80%/方法论停滞
   - 历史记录：v3.0→v5.1完整数据行

2. **模型抽象协议MAP** (references/model-abstraction-protocol.md)
   - 4层解耦：业务逻辑(不变) → 角色语义(缓变) → Prompt语法(快变) → 模型接口(适配)
   - 系统80%价值在L3+L4层（模型无关），20%在L1+L2层（需适配）
   - Prompt模型无关化4原则：结构化/Schema约束/数字标尺/显式步骤
   - 模型切换SOP：L1适配(5min) → L2校准(1-2h) → L3验证(30min)
   - 核心资产清单：9类模型无关资产

3. **跨模式传粉协议CPL** (references/cross-pattern-learning.md)
   - 花粉提取→可行性矩阵评估→领域适配注入→传粉历史记录
   - 反向传粉：失败案例跨模式预防注入

4. **能力边界地图** (experience-db/capability-frontier.md)
   - 三色分类：🟢已验证(6项) / 🟡理论就绪(5项) / 🔴已知缺口(6项)
   - 增长追踪：从3/14→6/14，目标Q2达12/14
   - 退化监控：4项指标+4个退化信号

5. **知识衰减引擎KDE** (references/knowledge-decay-engine.md)
   - 分文件TTL规则（experience-db 9文件 + memory/按类型）
   - 知识条目级TTL（价格24h/趋势30d/实体90d/关系180d/方法论∞）
   - 压缩摘要协议：30天daily记录→提炼核心→归档细节
   - 健康度指标：4项（EXPIRED占比/STALE占比/无更新文件数/归档增长率）

6. **结构化经验提取** (SKILL.md Step 9.8-9.10)
   - Step 9.8 跨模式传粉检查（CPL）
   - Step 9.9 进化账本更新
   - Step 9.10 能力边界更新

### 流水线升级
- Step 1.5 经验召回：5→8文件（+evolution-ledger/capability-frontier/cross-pattern-learning）
- Step 9 复盘：+3个子步骤（9.8传粉/9.9账本/9.10边界）
- Step 11 自检：10→14项（+进化轨迹审计/能力边界健康/传粉覆盖/模型抽象合规）

### 文件变更
- SKILL.md: v5.1→v5.2
- CHANGELOG.md: +v5.2记录
- AGENTS.md: +v5.2六齿轮概述
- MEMORY.md: +v5.2核心能力详述
- 新建5个文件（2个experience-db + 3个references）

---

## Orchestrator v5.1 — DNA底座全军继承 — 2026-03-03
- DNA底座：9条基因从Pattern H v4.0提取并写入SKILL.md全局层
  - Gene 1-9: 分层架构/五大通用协议/实时进度面板/角色Prompt/领域红线/部署梯度/TTL/知识沉淀/交叉验证
- 6个Pattern全面升级（6路并行施工）：
  - A(电商)+6 / B(专利)+6 / C(竞品)+5 / D(商业计划)+6 / E(内容矩阵)+5 / F(技术评估)+5
- H(精英情报)补全维度覆盖检查（10项情报专用checklist）
- 祖宗文件同步：AGENTS.md + MEMORY.md + BOOTSTRAP.md → v5.1
- 全7个Pattern达标率：7/7 = 100%（10/10）

## Pattern-Intelligence v4.1 — 实战修复 — 2026-03-03
- 基于PIR-2026-001/002实战复盘的10项修复：
  1. GRAPH-ANALYST prompt +三层Ontology强制写入(语义/动力/动态)
  2. PREDICTOR prompt +双模式切换(侦察预测模式A / RL对手模型模式B)
  3. 全局Prompt约束section(⑧TTL标注/⑨置信度⭐级/⑩输出格式) — 适用全部13角色
  4. 12个角色prompt标题标注v4.1全局约束适用
  5. 部署梯度标注PIR侦察任务至少Standard档位
  6. +六层架构激活追踪section(每次任务后记录L1-L6激活状态)
- v4.0→v4.1: 角色不变(13个)，协议不变(10个)，红线不变(19条)
  变的是prompt精度和运行时自审能力

## Pattern-Intelligence v4.0 — 2026-03-03
- 精英情报团队操作系统升级（不加角色，换底座）
- 6个新prompt模板（含通用v4.0注入指令）
- 部署梯度更新（+v4.0基础设施成本列）

## v5.0 — 2026-03-03

### 架构重构
- **Step重编号：** 5=VERIFIER → 6=P6验收 → 7=验收修复 → 8=SYNTHESIZER → 9=复盘 → 10=自主调度 → 11=系统自检
- **SYNTHESIZER职责分离：** 不再混在Step 5中，独立为Step 8，明确在P6验收通过后执行
- **验收修复独立为Step 7：** CONDITIONAL/FAIL处理逻辑从P6中拆出，含重验机制
- **执行顺序铁律：** 5→6→7→8 严格串行，不可跳步

### 新增能力
- **执行档位（Execution Tier）：** Lite/Standard/Full三档，不再全有全无
- **Agent失败处理协议：** 超时/空产出/spawn失败的重试/降级/熔断机制
- **Step 11系统自检：** 8项架构健康审计（文件完整性/交叉引用/硬约束可执行性/experience-db质量等）
- **跨模式混合任务协议：** 同时命中2+模式时的merge规则
- **experience-db归档：** 超500行自动归档到archive/

### 修复
- **S1 Step编号混乱：** 重编号，Step 7不再是幽灵引用
- **S2 输出路径不安全：** 统一到 `~/.openclaw/workspace/multi-team-output/`，禁止`/tmp/`
- **S3 评分标尺不一致：** 统一1-10分制
- **S4 P6最小配置矛盾：** 明确Standard≥3 Agent，Full推荐5 Agent
- **S5 SYNTHESIZER双重身份：** 交叉验证(Agent≥5)和报告生成(Step 8)两种用途明确区分
- **PR1 CONDITIONAL修正后不重验：** Step 7新增修正后重跑P6机制
- **PR2 RED-TEAM激活标准模糊：** 明确为"≥100万投资/专利核心/法律/不可逆决策"
- **Q1 footer垃圾：** 删除所有文件的重复版本注释
- **Q3 硬约束未分类：** 分三级（🔴铁律/🟡流程/🟢质量）
- **Q5 experience-db模板臃肿：** 精简模板，增加数据区分度

### 删除
- 旧版版本注释（移入本CHANGELOG）
- Step 3.5独立编号（合并到Step 3数据传递协议）

## v4.3 — 2026-03-03
- 实战修复：VERIFIER独立验证/P6≥3Agent/SYNTHESIZER报告/CONDITIONAL修正/共享摘要
- 新增硬约束#16-#23
- TAP时间锚点协议
- Completeness Guard三层防线

## v4.2.1 — 2026-03-03
- Step 1.5扩展为读5个文件
- L2失败降级L3规则
- FAIL返工协议
- 新增correction-log.md和approved-tasks.md

## v4.2 — 2026-03-03
- Step 5自动修正三级协议
- Step 8.6单步效率追踪
- Step 9自主任务调度
- 新增step-efficiency.md

## v4.1 — 2026-03-03
- 自我进化引擎
- Step 1.5经验召回
- Step 8强制复盘
- experience-db/结构化经验库

## v4.0 — 2026-03-03
- P6验收层（审查团队7角色 + 审计团队7角色）
- 能力库扩展到9大类42角色

## v3.x — 2026-02-28
- 初始多团队架构
- 决策引擎+7种模式
- 基础能力库
