# 🏭 OpenClaw Multi-Agent Team Framework

### An AI team factory for [OpenClaw](https://github.com/openclaw/openclaw).

**One person. Multiple AI teams. Every vertical you need.**

You don't get one AI assistant — you get a **factory that builds entire specialist teams**. Each team has its own analysts, creators, strategists, and decision-makers. They work in parallel, share a blackboard, and deliver structured results.

**Build once, reuse everywhere.** Copy a template → define roles → new team in minutes.

🛒 E-commerce team → market research + product scouting + pricing + content → Go/No-Go decision
🔬 R&D team → literature review + technology analysis + experiment design → research report
📝 Content team → audience research + copywriting + SEO + editing → publish-ready content
💰 Investment team → due diligence + risk modeling + portfolio analysis → investment memo
🎯 **Your team** → define any roles you need → your workflow, your rules

**All teams coexist in one workspace. Different tasks dispatch different teams. No conflicts.**

---

## Architecture

```
                    ┌─────────────┐
                    │  CONDUCTOR   │
                    │  (Orchestrator)│
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
| **CONDUCTOR** | The lead agent (you). Decomposes tasks, dispatches sub-agents, arbitrates conflicts |
| **Roles** | Specialized sub-agents with focused templates (market research, pricing, content, etc.) |
| **Blackboard** | Shared file-based state — agents read/write to coordinate without direct messaging |
| **Flywheel** | Closed-loop architecture — outputs feed back as inputs for continuous improvement |
| **TOOL-BOOTSTRAP** | Injected into every sub-agent to standardize tool usage and quality gates |

### Three Operating Modes (per team)

| Mode | Trigger | Flow |
|------|---------|------|
| **Full Pipeline** | "Evaluate category X" | CONDUCTOR → [parallel: Research + Scout] → [parallel: Content + Pricing] → Decision |
| **Event-Driven** | Data anomaly detected | Monitor → CONDUCTOR → targeted specialist → Decision |
| **Reactive** | Competitor move | CONDUCTOR → [parallel: Analyst + Pricing] → Quick Decision |

### Multi-Team Dispatch

When you have multiple teams, OpenClaw routes to the right one based on context:

```
You: "分析蓝牙耳机品类的市场机会"
  → OpenClaw reads ecommerce-team/ORCHESTRATOR.md
  → Dispatches RADAR + SCOUT in parallel
  → FORGE + BLADE
  → ORACLE delivers Go/No-Go

You: "帮我写3篇小红书种草文案"
  → OpenClaw reads content-team/ORCHESTRATOR.md
  → Dispatches Researcher + Writer in parallel
  → Editor reviews and polishes
  → Delivers final content

You: "调研协作机器人技术趋势"
  → OpenClaw reads research-team/ORCHESTRATOR.md
  → Dispatches Literature Reviewer + Technology Analyst
  → Delivers structured research report
```

Teams don't interfere with each other. Each has its own blackboard, its own output directory, its own roles.

## Quick Start

### 1. Install OpenClaw
```bash
npm install -g openclaw
```

### 2. Copy the example team to your workspace
```bash
cp -r examples/ecommerce-team ~/.openclaw/workspace/ecommerce-team
```

### 3. Customize templates
Edit the role templates in `templates/` to match your domain. The `{{TARGET}}` placeholder gets replaced at runtime.

### 4. Run
Tell your OpenClaw agent:
> "启动电商团队，评估品类：蓝牙耳机"

The CONDUCTOR will automatically:
1. Run tool health checks
2. Dispatch RADAR + SCOUT in parallel
3. Wait for results, arbitrate conflicts
4. Dispatch FORGE + BLADE in parallel
5. Run ORACLE for final decision
6. Present the decision to you

### 5. Build More Teams

```bash
# Copy the example as a starting point for a new vertical
cp -r examples/ecommerce-team ~/.openclaw/workspace/research-team

# Edit the role templates for your domain
# See docs/CUSTOMIZATION.md for the full guide
```

Repeat for as many verticals as you need. All teams live in your workspace, ready to be dispatched.

## Directory Structure

```
openclaw-multi-agent-team/
├── README.md                     # This file
├── LICENSE                       # MIT
├── framework/
│   ├── ARCHITECTURE.md           # Core architecture doc (domain-agnostic)
│   ├── ORCHESTRATOR.md           # CONDUCTOR execution protocol
│   ├── TOOL-BOOTSTRAP.md         # Sub-agent tool injection template
│   └── BLACKBOARD-SPEC.md        # Blackboard read/write rules
├── examples/
│   └── ecommerce-team/           # Full working example
│       ├── ORCHESTRATOR.md       # E-commerce specific orchestration
│       ├── TOOLKIT.md            # Tool availability status
│       ├── TOOL-BOOTSTRAP.md     # E-commerce tool bootstrap
│       ├── templates/
│       │   ├── 00-conductor.md   # Orchestrator protocol
│       │   ├── 01-radar.md       # Market Research agent
│       │   ├── 02-scout.md       # Product Scouting agent
│       │   ├── 03-forge.md       # Content Creation agent
│       │   ├── 04-blade.md       # Pricing Strategy agent
│       │   ├── 05-pulse.md       # Data Monitoring agent
│       │   └── 06-oracle.md      # Decision Making agent
│       ├── blackboard/
│       │   ├── TASKS.md
│       │   ├── DECISIONS.md
│       │   ├── MARKET-SIGNALS.md
│       │   ├── PRODUCT-DB.md
│       │   ├── COMPETITOR-MAP.md
│       │   ├── METRICS.md
│       │   └── ALERTS.md
│       └── output/               # Agent outputs go here
└── docs/
    ├── CUSTOMIZATION.md          # How to build your own team
    ├── ROLE-DESIGN.md            # Best practices for role templates
    └── TROUBLESHOOTING.md        # Common issues and fixes
```

## Build Your Own Team

See [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for a step-by-step guide. The TL;DR:

1. **Define your roles** — What specialists does your domain need?
2. **Design the flywheel** — What's the dependency graph? What can run in parallel?
3. **Write role templates** — Each role gets a markdown file with: mission, execution steps, output format, red-team self-check, confidence grading
4. **Set up the blackboard** — What shared state do roles need to coordinate?
5. **Configure the orchestrator** — Define dispatch order, conflict resolution rules, quality gates

## Key Design Principles

1. **Blackboard, not direct messaging** — Agents coordinate through shared files, not by talking to each other
2. **Parallel by default** — Independent tasks always run simultaneously
3. **Red-team everything** — Every role template includes mandatory self-critique before output
4. **Confidence grading** — All claims must be tagged HIGH/MEDIUM/LOW with clear criteria
5. **Kill criteria** — Every Go decision must have quantifiable stop-loss conditions
6. **Data over opinion** — Quantified data beats qualitative judgment in conflict resolution
7. **Source everything** — No data point without attribution (tool + query + date)

## Quality Gates (built-in)

Every sub-agent output is checked by CONDUCTOR for:
- [ ] One-sentence conclusion present?
- [ ] Confidence levels tagged?
- [ ] Red-team self-check completed?
- [ ] Data sources annotated?
- [ ] Conflicts with prior reports flagged?
- [ ] Blockers identified?

Failed checks → output rejected, agent must fix.

## Prerequisites & Installation

### System Requirements

| Dependency | Minimum Version | Check Command | Install |
|-----------|----------------|---------------|---------|
| **Node.js** | v18+ (v20+ recommended) | `node -v` | [nodejs.org](https://nodejs.org/) or `brew install node` |
| **npm** | v9+ | `npm -v` | Comes with Node.js |
| **Git** | v2.30+ | `git --version` | [git-scm.com](https://git-scm.com/) or `brew install git` |

### Supported Platforms

- ✅ macOS (Intel & Apple Silicon)
- ✅ Linux (x86_64, arm64)
- ✅ Windows (via WSL2 recommended)

### Step 1: Install OpenClaw

```bash
npm install -g openclaw
openclaw --version   # verify: should be v0.9+
```

If you haven't configured OpenClaw yet, run the setup wizard:
```bash
openclaw setup
```

This will guide you through:
- Choosing your LLM provider (Anthropic, OpenAI, etc.)
- Setting your API key
- Configuring your workspace directory

### Step 2: Verify LLM & Tools

This framework requires an LLM with **tool use** (function calling) support:

| Provider | Supported Models | Recommended |
|----------|-----------------|-------------|
| Anthropic | Claude Opus, Sonnet, Haiku | ✅ Claude Sonnet 4 (best cost/performance) |
| OpenAI | GPT-4o, GPT-4.1 | ✅ GPT-4o |
| Google | Gemini 2.5 Pro | ✅ Gemini 2.5 Pro |

Verify your tools are working:
```bash
# OpenClaw should have these built-in:
# - web_search (Brave Search API — requires free API key)
# - web_fetch (no key required)
# - exec (shell commands)
# - read/write/edit (file operations)
# - sessions_spawn (sub-agent dispatch — core to this framework)
```

> **⚠️ web_search requires a Brave Search API key.** Get one free at [brave.com/search/api](https://brave.com/search/api/). Without it, research agents (RADAR, SCOUT) will have degraded performance.

### Step 3: Clone & Deploy

```bash
# Clone the repo
git clone https://github.com/Richchen-maker/openclaw-multi-agent-team.git

# Copy the example team into your OpenClaw workspace
cp -r openclaw-multi-agent-team/examples/ecommerce-team ~/.openclaw/workspace/ecommerce-team
```

### Step 4: Verify Installation

Tell your OpenClaw agent:
> "读取 ecommerce-team/ORCHESTRATOR.md，确认框架就绪"

If the agent can read the file and list available tools, you're good to go.

### Optional: Enhanced Tools

These are **not required** but improve specific roles:

| Tool | Benefits | Install |
|------|----------|---------|
| [Brave Search API](https://brave.com/search/api/) | Required for web_search | Free tier: 2,000 queries/month |
| [cn-ecommerce-search](https://clawhub.com) | Chinese e-commerce platform search (Taobao, JD, 1688, PDD) | `clawhub install cn-ecommerce-search` |
| Browser tool | Competitor page analysis, screenshot capture | Included with OpenClaw (needs Chrome/Chromium) |

### Troubleshooting Installation

| Problem | Solution |
|---------|----------|
| `openclaw: command not found` | Run `npm install -g openclaw` or check your PATH includes npm global bin |
| `node: command not found` | Install Node.js v18+ from [nodejs.org](https://nodejs.org/) |
| Sub-agents can't search the web | Set up Brave Search API key in OpenClaw config |
| Permission denied on install | Use `sudo npm install -g openclaw` or fix npm permissions ([guide](https://docs.npmjs.com/resolving-eacces-permissions-errors-when-installing-packages-globally)) |
| Windows: path issues | Use WSL2 for best compatibility: `wsl --install` |

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for runtime issues.

## Contributing

PRs welcome! Especially:
- New team examples (research, content, investment, etc.)
- Improvements to the framework architecture
- Better role templates
- Translations

## License

MIT — use it however you want.

---

Built with 🐊 by the OpenClaw community.
