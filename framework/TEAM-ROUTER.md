# Multi-Team Router Protocol

> 当 workspace 下存在多个 team 目录时，CONDUCTOR 通过本协议将用户指令路由到正确的团队执行。

---

## Core Concept

```
workspace/
├── framework/           # 通用框架（本目录）
├── teams/
│   ├── ecommerce/       # 电商选品团队
│   │   ├── ORCHESTRATOR.md   # 头部含 trigger keywords
│   │   ├── roles/
│   │   └── blackboard/
│   ├── content/         # 内容创作团队
│   │   ├── ORCHESTRATOR.md
│   │   ├── roles/
│   │   └── blackboard/
│   └── investment/      # 投研尽调团队
│       ├── ORCHESTRATOR.md
│       ├── roles/
│       └── blackboard/
└── CONDUCTOR.md         # 全局调度入口
```

- 每个 team 是独立的 specialist 团队，拥有自己的角色模板、blackboard、执行协议
- 每个 team 的 `ORCHESTRATOR.md` 头部必须声明 trigger keywords 和 team description
- CONDUCTOR 是唯一的全局调度者，跨团队共享

---

## ORCHESTRATOR.md Header Spec

每个 team 的 ORCHESTRATOR.md 必须以如下 YAML frontmatter 开头：

```yaml
---
team: ecommerce
description: "电商选品、竞品分析、定价策略"
triggers:
  keywords: [选品, 电商, SKU, 竞品, 定价, 上架, listing]
  intents: [product_research, competitor_analysis, pricing]
priority: 10          # 冲突时高优先级团队先匹配
---
```

---

## Routing Mechanism

```
User directive arrives
    │
    ├─ [1] Manual Override Check
    │     用户说"启动XX团队" / "用content团队" → 直接路由，跳过匹配
    │
    ├─ [2] Auto Match
    │     CONDUCTOR 扫描所有 teams/*/ORCHESTRATOR.md 的 triggers
    │     │
    │     ├─ Keyword Match: 指令中出现 trigger keyword → +1 score per hit
    │     ├─ Intent Match: 语义意图匹配 triggers.intents → +3 score per hit
    │     ├─ Priority Tiebreak: 同分时按 priority 字段降序
    │     │
    │     ├─ Single winner → 路由到该团队
    │     ├─ Multiple matches (任务跨域) → 进入 Multi-Team Collaboration
    │     └─ No match → CONDUCTOR 直接处理（不依赖团队）
    │
    └─ [3] Dispatch
          加载目标团队的 ORCHESTRATOR.md → 按其协议执行
```

### Manual Override Examples

| 用户指令 | 路由结果 |
|---------|---------|
| "启动电商团队，分析蓝牙耳机" | → ecommerce team |
| "用content团队写一篇推广文案" | → content team |
| "investment团队尽调这家公司" | → investment team |

---

## Multi-Team Collaboration

一个任务可能需要多个团队协作。两种模式：

### Serial (串联)

```
Team A executes → output to shared blackboard → Team B reads and continues
```

CONDUCTOR 负责：
1. 先 dispatch Team A，等待完成
2. 将 A 的关键输出写入 `blackboard/CROSS-TEAM-HANDOFF.md`
3. Dispatch Team B，注入 A 的输出作为上下文

### Parallel (并联)

```
Team A ──┐
         ├──→ CONDUCTOR merges → final output
Team B ──┘
```

CONDUCTOR 负责：
1. 同时 dispatch Team A 和 Team B
2. 收集两个团队的输出
3. 合并、仲裁冲突、生成最终结果

### Choosing Mode

| 条件 | 模式 |
|------|------|
| B 依赖 A 的输出 | Serial |
| A 和 B 独立工作 | Parallel |
| 不确定 | Default to Serial（更安全） |

---

## Conflict Rules

1. **同名角色禁止跨团队并发**：如果 ecommerce 和 content 团队都有 `analyst` 角色，同一任务中不能同时 dispatch 两个 analyst — CONDUCTOR 必须选一个或串联执行
2. **Blackboard 隔离**：每个团队写自己的 `teams/<name>/blackboard/`，跨团队数据通过 `blackboard/CROSS-TEAM-HANDOFF.md` 传递
3. **Decision 权归属**：最终决策始终由 CONDUCTOR 做出，不由任何单个团队的 Decision 角色决定
4. **资源竞争**：并发 sub-agent 数量上限由系统决定，CONDUCTOR 按 priority 排序调度

---

## Example Scenario: 电商选品 → 内容推广

```
用户: "帮我选一款蓝牙耳机，选好之后写推广文案"

CONDUCTOR 解析:
  - "选品/蓝牙耳机" → ecommerce team (keyword match)
  - "推广文案" → content team (keyword match)
  - 依赖关系: content 需要 ecommerce 的选品结果 → Serial mode

Execution:
  [Phase 1] Dispatch ecommerce team
    → Analyst: 市场调研
    → Scout: 竞品扫描
    → Decision: 推荐 Top 3 SKU
    → Output: teams/ecommerce/blackboard/DECISIONS.md

  [Handoff] CONDUCTOR 提取选品结果 → blackboard/CROSS-TEAM-HANDOFF.md

  [Phase 2] Dispatch content team
    → Context: 注入选品结果（产品名、卖点、定价、目标人群）
    → Creator: 生成推广文案
    → Reviewer: 质量审核
    → Output: teams/content/blackboard/DELIVERABLES.md

  [Final] CONDUCTOR 汇总 → 交付用户
```

---

## Adding a New Team

1. 创建 `teams/<name>/` 目录结构（ORCHESTRATOR.md + roles/ + blackboard/）
2. ORCHESTRATOR.md 头部写好 triggers frontmatter
3. 定义角色模板放入 `roles/`
4. Done — CONDUCTOR 下次扫描时自动发现新团队
