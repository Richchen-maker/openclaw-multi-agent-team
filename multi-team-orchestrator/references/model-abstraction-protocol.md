# 模型抽象协议（Model Abstraction Protocol — MAP）

> 核心目的：让多团队协作系统的核心逻辑与底层LLM解耦。
> 模型换代时只需修改适配层，不动业务逻辑。
> 这是系统抗颠覆能力的第一道防线。

---

## 架构分层

```
┌─────────────────────────────────┐
│  Layer 4: 业务逻辑层（不变层）    │  ← 决策引擎/模式识别/路由规则
│  Step流程/硬约束/评分标尺        │     换模型不动这层
├─────────────────────────────────┤
│  Layer 3: 角色语义层（缓变层）    │  ← 角色定义/能力边界/输出格式
│  42角色的"做什么"+"交付什么"     │     换模型微调这层
├─────────────────────────────────┤
│  Layer 2: Prompt语法层（快变层）  │  ← 具体prompt措辞/思维链格式
│  7要素标识/XML tag/token优化    │     换模型改这层
├─────────────────────────────────┤
│  Layer 1: 模型接口层（适配层）    │  ← API调用/参数/上下文管理
│  context window/token limit     │     换模型换这层
└─────────────────────────────────┘
```

---

## 各层换模型影响评估

| 层 | 文件 | 换模型工作量 | 说明 |
|----|------|-------------|------|
| L4 业务逻辑 | SKILL.md Step流程/硬约束/评分标尺 | **零** | 流程是流程，跟谁执行无关 |
| L3 角色语义 | references/pattern-*.md 角色定义 | **低** | 角色的"做什么"不变，可能微调"怎么说" |
| L2 Prompt语法 | references/pattern-*.md prompt模板 | **中** | 每个模型的prompt最佳实践不同，需要A/B测试 |
| L1 模型接口 | OpenClaw config / sessions_spawn | **换** | 纯配置变更，改model参数 |

### 关键结论
> **系统80%的价值在L3+L4层（不变+缓变），只有20%在L1+L2层（需适配）。**
> 这就是为什么换模型不会让系统崩溃——智慧在上层，不在下层。

---

## Prompt设计原则（模型无关化）

### 1. 结构化 > 自然语言
```
❌ "请你作为一个数据分析师，仔细分析以下数据..."
✅ ROLE: QUANT-ANALYST
   INPUT: {file_path}
   OUTPUT_FORMAT: {structured_template}
   CONSTRAINTS: [list]
   QUALITY_GATE: {criteria}
```
结构化prompt在任何模型上都能解析。自然语言风格因模型而异。

### 2. 输出格式用Schema约束
```
❌ "请输出一份详细报告"
✅ OUTPUT_SCHEMA:
   - executive_summary: string(200-500字)
   - findings: array[{topic, evidence, confidence(⭐1-5), source_url}]
   - recommendations: array[{action, priority(P0-P3), effort(days), impact}]
```

### 3. 评分标尺用数字不用形容词
```
❌ "请评估这份报告的质量是优秀、良好还是一般"
✅ SCORING: 1-10 scale
   1-3: 数据缺失/逻辑错误/不可用
   4-6: 基本完整但有明显改进空间
   7-8: 高质量，细节处可优化
   9-10: 卓越，可直接对外交付
```

### 4. 思维链用显式步骤而非隐式引导
```
❌ "让我们一步步思考..."
✅ REASONING_PROTOCOL:
   Step 1: 列出所有相关数据源
   Step 2: 对每个数据源评估可靠性(⭐1-5)
   Step 3: 交叉验证——至少2个独立源确认同一结论
   Step 4: 对不一致的数据标注矛盾并给出判断
```

---

## 模型切换SOP

### 触发条件
1. 新模型发布且性能/成本显著提升
2. 当前模型API变更或停服
3. 特定任务需要特定模型能力（如超长上下文/多模态）

### 切换步骤
1. **L1适配**（5分钟）：改config中model参数
2. **L2校准**（1-2小时）：用3个历史任务做A/B对比
   - 选1个Lite、1个Standard、1个Full任务
   - 同prompt跑新模型，对比输出质量
   - 记录差异到 `prompt-evolution.md`
3. **L2调优**（按需）：根据校准结果微调prompt语法
   - 常见调整：XML tag风格、思维链触发方式、输出长度控制
4. **L3验证**（30分钟）：确认角色语义理解无偏移
   - 重点检查：RED-TEAM攻击性、SYNTHESIZER交叉验证深度、审查团队评分一致性
5. **更新进化账本**：记录模型切换前后的AVG_QUALITY对比

### 回滚策略
- 保留旧模型配置7天
- AVG_QUALITY下降>10%立即回滚
- 单次任务FAIL且根因为模型理解偏差→回滚

---

## 模型无关的核心资产清单

以下资产在任何模型下都100%可复用：

| 资产 | 位置 | 说明 |
|------|------|------|
| 决策引擎流程 | SKILL.md Step 1-11 | 纯逻辑流，与模型无关 |
| 硬约束体系 | SKILL.md 三级约束 | 规则就是规则 |
| 失败案例库 | experience-db/failure-cases.md | 经验是跨模型的 |
| 方法论库 | experience-db/methodology-library.md | 方法论是跨模型的 |
| 路由经验 | experience-db/routing-patterns.md | 编制决策是跨模型的 |
| 进化账本 | experience-db/evolution-ledger.md | 度量是跨模型的 |
| DNA 9基因 | SKILL.md DNA底座 | 架构原则是跨模型的 |
| 评分标尺 | team-review.md / team-audit.md | 标准是跨模型的 |

**这些就是你说的"引擎"。模型只是燃料。**
