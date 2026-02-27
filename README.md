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
| **Node.js** | **v22.12.0+** (required) | `node -v` | [nodejs.org](https://nodejs.org/) or `brew install node` |
| **npm** | v10+ | `npm -v` | Comes with Node.js |
| **Git** | v2.30+ | `git --version` | [git-scm.com](https://git-scm.com/) or `brew install git` |

### Supported Platforms

- ✅ macOS (Intel & Apple Silicon)
- ✅ Linux (x86_64, arm64)
- ✅ Windows (via WSL2 recommended)

### Step 1: System Dependencies (terminal commands)

On a fresh machine, you need **3 things** installed before anything else: **Node.js**, **npm**, and **Git**.

**macOS:**
```bash
# 1. Install Homebrew (macOS package manager — skip if already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Node.js (v22.12+ REQUIRED — OpenClaw won't run on older versions)
brew install node

# 3. Install Git (for cloning repos)
brew install git

# 4. Verify everything is installed
node -v        # MUST show v22.12.0 or higher
npm -v         # should show v10+
git --version  # any recent version is fine
```

**Linux (Ubuntu/Debian):**
```bash
# Node.js v22+ (NOT the default apt version — that's too old)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs git

# Verify
node -v   # MUST show v22.12.0+
```

**Windows:**
```bash
# Option A: Install WSL2 (recommended — gives you a Linux terminal)
wsl --install
# Then inside WSL, follow Linux steps above

# Option B: Native Windows
# Download Node.js v22+ from https://nodejs.org/
# Download Git from https://git-scm.com/
```

> ⚠️ **Node.js version matters!** OpenClaw requires **v22.12.0 or higher**. If `node -v` shows anything below v22, you must upgrade. Run `brew upgrade node` (macOS) or reinstall from [nodejs.org](https://nodejs.org/).

### Step 2: Install OpenClaw + ClawHub

```bash
# Install OpenClaw (the AI agent runtime)
npm install -g openclaw

# Install ClawHub (skill marketplace CLI)
npm install -g clawhub

# Install mcporter (MCP server management — needed for translate etc.)
npm install -g mcporter

# Verify
openclaw --version   # should be v0.9+
clawhub --version
mcporter --version
```

### Step 3: Get an LLM API Key

This framework runs AI agents that need a large language model. You need **one** of these API keys:

| Provider | Get API Key | Cost |
|----------|------------|------|
| **Anthropic** (recommended) | [console.anthropic.com](https://console.anthropic.com/) | Pay-per-use (~$3-15/team run with Claude Sonnet) |
| OpenAI | [platform.openai.com](https://platform.openai.com/) | Pay-per-use |
| Google | [aistudio.google.com](https://aistudio.google.com/) | Free tier available |

> 💡 **Which model?** Claude Sonnet 4 is the best balance of cost and quality for this framework. Claude Opus is more powerful but ~5x the cost. GPT-4o also works well.

### Step 4: Run OpenClaw Setup Wizard

```bash
openclaw setup
```

This interactive wizard guides you through:
- Choosing your LLM provider and entering your API key
- Configuring your workspace directory (`~/.openclaw/workspace/`)
- Setting up a messaging channel (Telegram, Discord, etc. — optional but recommended)

After setup, start OpenClaw:
```bash
openclaw gateway start
```

### Step 5: Configure Search API Keys

Research agents need web search to function. **Without these, agents produce empty results.**

```bash
# Brave Search API (required — powers web_search)
# Get free key at: https://brave.com/search/api/ (2,000 queries/month free)
openclaw config set braveApiKey YOUR_BRAVE_KEY_HERE

# Tavily API (required for deep research — RADAR/SCOUT use this)
# Get free key at: https://tavily.com (1,000 queries/month free)
# Add to your shell config:
echo 'export TAVILY_API_KEY="tvly-YOUR_KEY_HERE"' >> ~/.zshrc
source ~/.zshrc
```

### Step 6: Install Skills from ClawHub

```bash
# For e-commerce team:
clawhub install cn-ecommerce-search    # Search Taobao/JD/1688/PDD/Douyin
clawhub install tavily-search          # AI-powered deep research

# For content team:
clawhub install summarize              # Summarize URLs, PDFs, videos
clawhub install humanizer-zh           # Remove AI writing patterns from Chinese text

# Verify installed skills:
ls ~/.openclaw/workspace/skills/
```

### Step 7: Clone & Deploy This Framework

```bash
# Clone the repo
git clone https://github.com/Richchen-maker/openclaw-multi-agent-team.git

# Copy whichever team you want into your OpenClaw workspace
cp -r openclaw-multi-agent-team/examples/ecommerce-team ~/.openclaw/workspace/ecommerce-team
cp -r openclaw-multi-agent-team/examples/content-team ~/.openclaw/workspace/content-team

# Copy the framework docs (needed for multi-team routing)
cp -r openclaw-multi-agent-team/framework ~/.openclaw/workspace/framework
```

### Step 8: Verify Everything Works

Start OpenClaw and tell it:
> "读取 ecommerce-team/ORCHESTRATOR.md，确认框架就绪"

If the agent can read the file and list available tools, you're ready to go. Try:
> "启动电商团队，评估品类：蓝牙耳机"

### Optional: Extra Tools

| Tool | Benefits | Install |
|------|----------|---------|
| [Playwright](https://playwright.dev/) | Browser automation for competitor analysis | `npm install -g playwright` |
| Chrome/Chromium | Browser tool page analysis | [Download](https://www.google.com/chrome/) |
| [Feishu integration](https://docs.openclaw.ai) | Output reports to Feishu docs | Configure in OpenClaw settings |

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
