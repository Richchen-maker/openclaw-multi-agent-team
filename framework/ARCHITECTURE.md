# Multi-Agent Team Architecture

> Generic framework for building specialized AI teams in OpenClaw.

---

## Design Philosophy

### Pipeline vs Flywheel

| Dimension | Pipeline | Flywheel |
|-----------|----------|----------|
| Topology | Linear (Phase 1→2→3) | **Closed-loop** (data-driven iteration) |
| Time Scale | One-shot execution | **Continuous operation**, periodic decisions |
| Input | Fixed specification | **Dynamic signals** |
| Output | Document (final state) | Actions (continuous optimization) |

**Choose Flywheel when your domain requires iteration.** Choose Pipeline for one-shot document generation.

---

## Flywheel Architecture

```
                    ┌─────────────┐
                    │  CONDUCTOR   │
                    │ (Orchestrator)│
                    └──────┬──────┘
                           │ dispatch / arbitrate
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │ Analysts  │  │ Creators  │  │ Monitors  │
    │ (Research)│→ │ (Content) │→ │  (Data)   │
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

---

## Role Types

Every team needs some combination of these archetypes:

### 1. CONDUCTOR (Orchestrator)
- **Not a sub-agent** — this is the lead agent (your main OpenClaw session)
- Decomposes tasks, dispatches sub-agents, arbitrates conflicts
- Owns quality gates and conflict resolution
- Only entity with write access to DECISIONS in the blackboard

### 2. Analyst Roles (Research & Intelligence)
- Gather signals, identify trends, assess feasibility
- Examples: Market Researcher, Competitive Analyst, Technical Assessor
- Output: Reports with confidence-graded findings

### 3. Creator Roles (Content & Strategy)
- Transform insights into actionable assets
- Examples: Content Creator, Pricing Strategist, Campaign Planner
- Output: Ready-to-execute plans and materials

### 4. Monitor Roles (Data & Alerting)
- Track metrics, detect anomalies, trigger responses
- Examples: Performance Monitor, Risk Tracker, Quality Auditor
- Output: Dashboards, alerts, attribution analysis

### 5. Decision Roles (Synthesis & Judgment)
- Integrate all inputs into final recommendations
- Examples: Decision Oracle, Strategic Advisor
- Output: Go/No-Go decisions with kill criteria

---

## Operating Modes

### Mode A: Full Pipeline
Best for: New initiatives, comprehensive evaluation

```
CONDUCTOR receives directive
    │
    ├── [Parallel] Analyst roles (research + intelligence)
    │         ↓ outputs merged
    │     CONDUCTOR arbitrates conflicts
    │         ↓
    ├── [Parallel] Creator roles (content + strategy)
    │         ↓ outputs merged
    │     CONDUCTOR reviews consistency
    │         ↓
    └── Decision role: final recommendation → user approval
              ↓ after execution
          Monitor role: continuous tracking → feedback loop
```

### Mode B: Event-Driven
Best for: Ongoing operations, anomaly response

```
Monitor detects anomaly
    │
    CONDUCTOR starts diagnosis:
    ├── Targeted analyst roles
    ├── Relevant creator roles
    │         ↓
    Decision role: attribution + recommendation → user
```

### Mode C: Reactive
Best for: Competitor moves, market shifts, urgent situations

```
Signal detected
    │
    CONDUCTOR triggers emergency response:
    ├── Analyst + Strategy roles (parallel)
    │         ↓
    Decision role: quick recommendation → user
```

---

## Blackboard System

All agents communicate through the blackboard — **never directly**.

```
blackboard/
├── TASKS.md          # Current task state machine
├── DECISIONS.md      # Confirmed decisions (append-only)
├── SIGNALS.md        # Analyst-written market/domain signals
├── DATA.md           # Shared domain data (specs, costs, params)
├── COMPETITORS.md    # Competitive landscape
├── METRICS.md        # Key metric snapshots
└── ALERTS.md         # Alert queue
```

### Write Rules
- Each agent writes only to its responsibility domain
- All writes must include: timestamp + data source annotation
- DECISIONS.md: only CONDUCTOR and Decision roles have write access
- Conflict detection: if two agents write to the same field, CONDUCTOR arbitrates

---

## Conflict Arbitration Protocol

When two agents disagree, CONDUCTOR resolves by priority:

1. **Quantified data** > qualitative judgment
2. **Recent data** (≤3 months) > historical data
3. **Official/platform data** > third-party reports > inference
4. **Multi-source consensus** > single source
5. **When uncertain** → conservative choice (lower risk)

All arbitration decisions are recorded in `DECISIONS.md` with reasoning.

---

## Quality Gates

Every sub-agent output must pass CONDUCTOR review:

```
□ One-sentence conclusion present?
□ Confidence levels tagged (HIGH/MEDIUM/LOW)?
□ Red-team self-check completed?
□ Data sources annotated?
□ Conflicts with prior reports identified?
□ Blockers flagged?
```

Failed → agent must fix in-session (no re-spawn needed).

---

## Sub-Agent Spawning Protocol

Critical: sub-agents **do not inherit** the lead agent's skills or workspace files. Every sub-agent task prompt must include:

```
[1] TOOL-BOOTSTRAP.md (full text — tool capabilities + output rules)
[2] Role template (full text — with {{TARGET}} replaced)
[3] Prior role outputs (summaries of dependent steps)
[4] Blackboard path for output
```

**Pre-spawn checklist:**
```
□ TOOL-BOOTSTRAP.md injected in full
□ Role template injected in full (including red-team / confidence sections)
□ {{TARGET}} placeholder replaced
□ Prior outputs injected (if dependencies exist)
□ Output file path specified
```

---

## Multi-Team Architecture

When the workspace contains multiple specialist teams, they coexist as independent flywheels sharing a single CONDUCTOR:

```
                         ┌──────────────────┐
                         │    CONDUCTOR      │
                         │ (Global Router &  │
                         │   Arbitrator)     │
                         └────────┬─────────┘
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
          ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
          │  Team A      │ │  Team B      │ │  Team C      │
          │ (ecommerce)  │ │ (content)    │ │ (investment) │
          │              │ │              │ │              │
          │ ┌─Analysts─┐ │ │ ┌─Creators─┐ │ │ ┌─Analysts┐ │
          │ │ Scouts    │ │ │ │ Writers  │ │ │ │ Analysts │ │
          │ │ Strategist│ │ │ │ Reviewer │ │ │ │ Drafter  │ │
          │ └───────────┘ │ │ └──────────┘ │ │ └──────────┘ │
          │  blackboard/  │ │  blackboard/  │ │  blackboard/  │
          └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
                  │                 │                 │
                  └────────────────┼────────────────┘
                                   ▼
                     ┌──────────────────────┐
                     │  CROSS-TEAM-HANDOFF   │
                     │  (shared blackboard)  │
                     └──────────────────────┘
```

**Key properties:**
- Each team is an **independent flywheel** with its own roles, blackboard, and ORCHESTRATOR.md
- CONDUCTOR is the **only shared component** — it routes, arbitrates, and manages cross-team handoffs
- Teams **never communicate directly** — all cross-team data flows through `blackboard/CROSS-TEAM-HANDOFF.md`
- Adding a new team = adding a directory with the right structure — zero changes to existing teams

See [TEAM-ROUTER.md](./TEAM-ROUTER.md) for routing rules, collaboration modes, and conflict resolution.

---

## Cross-Team Auto-Collaboration (MANDATORY)

> **Every team built with this framework MUST integrate the Event Bus + Watchdog system.**
> This is not optional — it is the core capability that makes multi-team collaboration work.

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      WATCHDOG                            │
│          (Every 2min: detect stalls, auto-recover)       │
│                                                          │
│  Checks: STALE_PENDING | STALE_PROCESSING | CHAIN_BROKEN │
│          FORMAT_ERROR  | BUS_DOWN                        │
│  Recovery: auto-dispatch | auto-retry | re-emit          │
│  Alert: CRITICAL → notify user | WARNING → log only     │
└──────────────────────┬───────────────────────────────────┘
                       │ monitors
┌──────────────────────▼───────────────────────────────────┐
│                    EVENT BUS                              │
│           (Scan → Route → Dispatch → Resolve)            │
│                                                          │
│  Events:  DATA_GAP | CRAWL_BLOCKED | DEFENSE_REPORT      │
│           DATA_READY | ANOMALY | MARKET_SIGNAL           │
│           CRAWL_STRATEGY | SECURITY_INCIDENT             │
│                                                          │
│  Lifecycle: pending/ → processing/ → resolved/ | failed/ │
│  Safety: chain_depth ≤ 5 | dedup 60min | timeout 30min  │
└──────────────────────┬───────────────────────────────────┘
                       │ routes events between
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Team A  │   │ Team B  │   │ Team C  │
   │         │──→│         │──→│         │
   │         │←──│         │←──│         │
   └─────────┘   └─────────┘   └─────────┘
```

### Integration Requirements for New Teams

When creating a new team, you MUST:

1. **Register event routes** — Add your team's event types to `framework/eventbus/router.py` or `eventbus.yaml`
2. **Inject event awareness into ORCHESTRATOR.md** — Every team's orchestrator must include:
   ```markdown
   ## Cross-Team Event Protocol
   
   When executing tasks, if you encounter situations beyond this team's capability:
   1. Data missing → write DATA_GAP event to events/pending/
   2. Crawl blocked → write CRAWL_BLOCKED event
   3. Task complete with results for another team → write DATA_READY event
   
   Before execution, check events/pending/ for events targeting this team.
   Event file format: see framework/EVENT-BUS.md
   ```
3. **Define callback handlers** — Specify how your team receives results from other teams (which role resumes, where data is written)
4. **Test the chain** — Before deploying, verify: emit event → Event Bus routes → your team receives → your team responds

### Directory Structure (Required)

```
workspace/
├── events/                    # MANDATORY — shared across all teams
│   ├── pending/               # New events waiting for dispatch
│   ├── processing/            # Events being handled by a team
│   ├── resolved/              # Completed events
│   └── failed/                # Failed events (needs attention)
├── eventbus -> framework/eventbus/  # Symlink for CLI access
├── run-eventbus.sh            # One-click Event Bus launcher
├── team-alpha/                # Your teams
├── team-beta/
└── framework/
    └── eventbus/              # Runtime code
        ├── bus.py             # Core: scan → route → dispatch
        ├── watchdog.py        # Monitoring + auto-recovery
        ├── event.py           # Event data model
        ├── router.py          # Routing table
        ├── dispatcher.py      # Team dispatch
        ├── cli.py             # CLI interface
        └── config.py          # Configuration
```

### Monitoring (Required for Production)

Set up two monitoring layers:

1. **EventBus Watchdog cron** — Every 2 minutes, runs `python -m eventbus watchdog --fix`
   - Auto-recovers stale events
   - Alerts on chain breakage
   - Notifies user on CRITICAL issues

2. **System patrol cron** — Every 2 hours, checks overall system health
   - Verifies Watchdog cron is running
   - Checks disk/memory/CPU
   - Reports untracked workspace files

### Event Chain Safety Rules

| Rule | Value | Purpose |
|------|-------|---------|
| Max chain depth | 5 | Prevent infinite loops (A→B→C→A→B...) |
| Dedup window | 60 min | Same source+type won't re-trigger |
| Pending timeout | 5 min | Watchdog auto-dispatches if Event Bus missed it |
| Processing timeout | 30 min | Watchdog moves to failed + retries |
| CRITICAL events | Always notify user | Human in the loop for emergencies |

---

## Extending the Framework

1. **Multi-domain**: Parameterize role templates by domain (ecommerce/research/content)
2. **Cron integration**: Monitor roles can run on schedule for automated data collection
3. **Memory system**: Write decision loop results to memory for cross-session context
4. **Multi-project**: Partition blackboard by project/SKU for parallel management
5. **User dashboard**: Decision role can push periodic summaries to chat
6. **Cross-team collaboration**: Event Bus + Watchdog for automatic multi-team workflows (see above)
