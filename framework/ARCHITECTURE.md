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

## Extending the Framework

1. **Multi-domain**: Parameterize role templates by domain (ecommerce/research/content)
2. **Cron integration**: Monitor roles can run on schedule for automated data collection
3. **Memory system**: Write decision loop results to memory for cross-session context
4. **Multi-project**: Partition blackboard by project/SKU for parallel management
5. **User dashboard**: Decision role can push periodic summaries to chat
