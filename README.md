# 🏭 OpenClaw Multi-Agent Team Framework

**One framework. Unlimited teams. They work together.**

一套框架，造无数支团队。团队之间还能协作。

---

不是给你一个Agent。是给你一个**造Agent团队的工厂**。

你定义角色，你编排流程，你配武器库 —— 框架负责把它们变成一支能自主协作的团队。

**关键是：你可以造很多支团队，它们之间能互相协作，像一家真正的公司一样运转。**

电商团队发现数据缺口 → 自动触发数据采集团队补数据 → 采集被反爬拦截 → 自动触发安全团队突破 → 突破方案反哺回采集团队。

**一个人，指挥一家公司。**

电商选品？数据采集？安全攻防？法务审查？投研分析？内容生产？学术科研？
**都可以。只要你能定义角色和流程，这套架构就能把它跑起来。**

> 📖 **New here?** Start with the [Installation Guide (INSTALL.md)](INSTALL.md) — takes you from zero to running.

---

## Core: A Domain-Agnostic Team Orchestration Engine

This is not a tool for any specific vertical. It's a **universal multi-agent collaboration architecture**:

**① ORCHESTRATOR Protocol** — How to decompose tasks, what runs in parallel vs serial, how to arbitrate conflicts

**② Role Template System** — Each agent's mission, tool permissions, execution steps, output standards, red-team self-check

**③ Blackboard Collaboration** — Agents don't talk to each other. They coordinate through shared files. Zero coupling.

**④ Tool Bootstrap Layer** — Auto-checks weapon availability before agent launch. Missing tools get reported, not silently ignored.

**⑤ Quality Gates** — Every output must carry confidence levels + data sources + self-critique. Fails get rejected and reworked.

Take this architecture, fill in your own roles and tools, and you have a new team.

---

## 3 Open-Source Teams — Examples, Not the Product

| Example | Vertical | Roles | Arsenal Scale |
|---------|----------|-------|---------------|
| 🛒 **E-commerce Team** | Cross-border e-commerce | 6 roles (Research → Scouting → Pricing → Content → Decision) | Light — mostly search + analysis |
| 📡 **Data Collection Team** | General data engineering | 6 roles (Discovery → Crawling → Cleaning → Warehousing → Monitoring) | Medium — Python scripts + database |
| 🛡️ **ARC Team** (Anti-Risk Control) | Security research | 6 roles (Reverse → Fingerprint → Protocol → CAPTCHA → Vuln → Defense) | Heavy — 54 specialized security tools |

Three teams. Three completely different domains. **Same architecture underneath.**

They exist to show you: how to write role templates, how to design blackboards, how to configure tool chains, and how the orchestrator dispatches work.

**But the team you actually need? You build that yourself.**

---

## Architecture

```
                    ┌─────────────┐
                    │  CONDUCTOR   │
                    │ (Orchestrator)│
                    └──────┬──────┘
                           │ dispatch / arbitrate
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │  Role A   │  │  Role B   │  │  Role C   │
    │ (Analyst) │→ │ (Creator) │→ │ (Monitor) │
    └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  ┌─────────────┐
                  │  BLACKBOARD  │
                  │ (Shared State)│
                  └─────────────┘
                         ▲
                    Feedback Loop ↺
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **CONDUCTOR** | The lead agent. Decomposes tasks, dispatches sub-agents, arbitrates conflicts |
| **Roles** | Specialized sub-agents with focused templates |
| **Blackboard** | Shared file-based state — agents read/write to coordinate without direct messaging |
| **Flywheel** | Closed-loop — outputs feed back as inputs for continuous improvement |
| **TOOL-BOOTSTRAP** | Injected into every sub-agent to standardize tool usage and quality gates |

### Three Operating Modes (per team)

| Mode | Trigger | Flow |
|------|---------|------|
| **Full Pipeline** | "Run team on target X" | CONDUCTOR → parallel dispatch → sequential stages → final decision |
| **Event-Driven** | Anomaly detected | Monitor → CONDUCTOR → targeted specialist → decision |
| **Reactive** | External trigger | CONDUCTOR → parallel analysts → quick decision |

---

## Build Your Own Team — 4 Steps

```
1. Define Roles    — What specialists does your domain need? How many? Who leads?
2. Design Workflow — What's parallel? What's serial? Whose output feeds whom?
3. Deploy Arsenal  — What tools do your roles need? APIs? CLIs? Browsers? Databases?
4. Design Blackboard — What state do roles share? Tasks? Data? Decisions?
```

Copy an example team, edit the templates, swap the tools — you have a brand new team.

```bash
cp -r examples/ecommerce-team ~/.openclaw/workspace/my-research-team
# Edit templates/ for your domain
# Edit ORCHESTRATOR.md for your workflow
# See docs/CUSTOMIZATION.md for the full guide
```

---

## Included Team Details

### 🛒 E-commerce Team (6 roles)

| Role | Codename | Mission |
|------|----------|---------|
| Lead | **CONDUCTOR** | Task decomposition, dispatch, conflict arbitration |
| Market Research | **RADAR** | Category trends, market size, growth signals |
| Product Scouting | **SCOUT** | Supplier discovery, product evaluation, scoring |
| Content Creation | **FORGE** | Listing copy, A+ content, SEO optimization |
| Pricing Strategy | **BLADE** | Competitive pricing, margin modeling |
| Data Monitoring | **PULSE** | Real-time alerts, anomaly detection |
| Decision Making | **ORACLE** | Go/No-Go with kill criteria and stop-loss |

### 📡 Data Collection Team (6 roles)

| Role | Codename | Mission |
|------|----------|---------|
| Lead | **DISPATCHER** | Task routing, pipeline orchestration |
| Source Mapper | **MAPPER** | Data source discovery, feasibility analysis |
| Web Spider | **SPIDER** | Structured crawling, anti-ban handling |
| Data Refiner | **REFINER** | Cleaning, dedup, normalization |
| Data Warehouse | **WAREHOUSE** | Storage, indexing, versioning (SQLite + JSON) |
| Sentinel | **SENTINEL** | Monitoring, alerting on source changes |

### 🛡️ ARC Team — Anti-Risk Control (6 roles)

| Role | Codename | Mission |
|------|----------|---------|
| Lead | **COMMANDER** | Mission planning, cross-role coordination |
| Reverse Engineer | **REVERSER** | API reverse engineering, binary analysis |
| Fingerprint Engineer | **PHANTOM** | TLS spoofing, browser stealth, proxy management |
| Protocol Attacker | **STRIKER** | Fuzzing, rate testing, protocol probing |
| Risk Control Evader | **MIMIC** | CAPTCHA solving (5-engine), behavior simulation |
| Vulnerability Hunter | **HUNTER** | Vuln scanning, subdomain enum, XSS/SQLi |
| Defense Analyst | **SHIELD** | WAF identification, defense-level assessment (L1-L5) |

> ⚠️ **ARC Team is for defense research only.** See `TOOL-BOOTSTRAP.md` for iron rules.

### Cross-Team Collaboration — This Is the Real Power

Teams don't live in silos. They form a **company-level workflow**:

```
🛒 E-commerce spots data gap
    ↓
📡 Data Collection auto-dispatches crawl task
    ↓ blocked by anti-bot
🛡️ ARC assesses defense, provides bypass strategy
    ↓ strategy fed back
📡 Data Collection retries with new approach → data acquired
    ↓
🛒 E-commerce completes analysis with fresh data → Go/No-Go decision
```

You're not running isolated agents. You're running **an organization**.

Build as many teams as you need. Connect them through the [Event Bus](framework/EVENT-BUS.md). One person, one framework, unlimited teams — operating like a full company.

**Full chain runs with zero human intervention. You only said one sentence.**

---

## How It Works in Practice

Send a message from your phone. Team runs automatically:

```
You (Telegram/Discord/Slack): "启动XX团队，目标：YYY"

→ CONDUCTOR decomposes the task
→ Multiple agents launch in parallel
→ Blackboard collaboration, results aggregated
→ 15 min later, full report pushed to your phone
```

You're not at the computer. The team is working.

---

## Directory Structure

```
openclaw-multi-agent-team/
├── README.md
├── INSTALL.md                    # From-zero deployment guide
├── LICENSE                       # MIT
├── framework/
│   ├── ARCHITECTURE.md           # Core architecture (domain-agnostic)
│   ├── ORCHESTRATOR.md           # CONDUCTOR execution protocol
│   ├── TOOL-BOOTSTRAP.md         # Sub-agent tool injection template
│   ├── BLACKBOARD-SPEC.md        # Blackboard read/write rules
│   └── TEAM-ROUTER.md            # Multi-team dispatch routing
├── examples/
│   ├── ecommerce-team/           # 🛒 6 roles, light arsenal
│   ├── data-collection-team/     # 📡 6 roles, Python scripts + DB
│   ├── arc-team/                 # 🛡️ 6 roles, 54-weapon arsenal
│   └── content-team/             # 📝 4 roles, writing pipeline
└── docs/
    ├── CUSTOMIZATION.md          # How to build your own team
    ├── ROLE-DESIGN.md            # Best practices for role templates
    └── TROUBLESHOOTING.md        # Common issues and fixes
```

---

## Runtime Features (Production-Grade)

Event Bus Runtime — 跨团队自动协作引擎，21个Python模块，4500+ lines：

- ✅ **Event Bus Runtime** — scan → route → dispatch 核心循环
- ✅ **CronDispatcher** — 写DispatchRequest → Watchdog cron消费，解耦执行
- ✅ **Dynamic Capability Registry** — `capabilities.yaml` 声明即接入，零代码路由
- ✅ **DataBus** — Schema-validated data references（内置4种Schema）
- ✅ **Priority Queue** — CRITICAL事件优先dispatch
- ✅ **Memory Bridge** — 跨团队知识共享（knowledge/{domain}/{topic}.md）
- ✅ **Cost Controller** — Per-chain token预算，severity→model映射
- ✅ **Chain Visualization** — `trace` 命令树形展示事件链路
- ✅ **Team Self-Evolution** — 模式提取 + shortcut匹配，同类事件跳步执行
- ✅ **Parallel Chain Scheduler** — 多链路并发，团队锁防冲突
- ✅ **Watchdog V3** — 5种健康检查 + 智能恢复 + cron dispatch

```bash
# 快速体验
cd openclaw-multi-agent-team
PYTHONPATH=framework python3 -m eventbus status
PYTHONPATH=framework python3 -m eventbus registry --scan
```

详见 [Event Bus详解](framework/EVENT-BUS.md) | [跨团队协作指南](docs/CROSS-TEAM-GUIDE.md)

---

## Quick Start

### 1. Install OpenClaw

```bash
npm install -g openclaw
openclaw setup
```

### 2. Clone & Deploy

```bash
git clone https://github.com/Richchen-maker/openclaw-multi-agent-team.git
cp -r openclaw-multi-agent-team/examples/ecommerce-team ~/.openclaw/workspace/
cp -r openclaw-multi-agent-team/framework ~/.openclaw/workspace/
openclaw gateway start
```

### 3. Run

Tell your agent:
> "启动电商团队，评估品类：蓝牙耳机"

See [INSTALL.md](INSTALL.md) for the full from-zero guide (all teams + all dependencies).

---

## Design Principles

1. **Blackboard, not direct messaging** — Agents coordinate through shared files
2. **Parallel by default** — Independent tasks always run simultaneously
3. **Red-team everything** — Every role template includes mandatory self-critique
4. **Confidence grading** — All claims tagged HIGH/MEDIUM/LOW
5. **Kill criteria** — Every Go decision has quantifiable stop-loss
6. **Data over opinion** — Quantified data wins in conflict resolution
7. **Source everything** — No data point without attribution

---

## Tech Stack

- Runtime: [OpenClaw](https://github.com/openclaw/openclaw) (open source)
- LLM: Claude / GPT / Gemini (any provider)
- Architecture: Sub-agent, independent sessions per role
- Remote: Telegram / Discord / Slack / Feishu
- Platforms: macOS / Linux / Windows (WSL2)
- License: MIT — use it however you want

---

## Contributing

PRs welcome! Especially:
- **New team examples** — show us your vertical
- Framework architecture improvements
- Better role templates
- Translations

---

**⭐ Star if you think one person deserves a whole team.**

Built with 🐊 for the OpenClaw community.
