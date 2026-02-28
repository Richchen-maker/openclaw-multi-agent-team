# CONDUCTOR Execution Protocol

> The CONDUCTOR is the lead agent — your main OpenClaw session. This protocol defines how it dispatches and manages sub-agents.

---

## Multi-Team Mode

When multiple teams exist under `teams/`, CONDUCTOR operates as the **cross-team router and arbitrator**. See [TEAM-ROUTER.md](./TEAM-ROUTER.md) for the full protocol.

**CONDUCTOR's multi-team responsibilities:**

1. **Team Discovery**: Scan `teams/*/ORCHESTRATOR.md` frontmatter to build a team registry (triggers, priority, capabilities)
2. **Intent Routing**: Match user directives to the best team via keyword/intent scoring, or accept manual override ("启动XX团队")
3. **Cross-Team Orchestration**: For tasks spanning multiple teams, decide Serial vs Parallel mode and manage handoffs via `blackboard/CROSS-TEAM-HANDOFF.md`
4. **Conflict Prevention**: Ensure no two teams dispatch the same-named role concurrently on the same task
5. **Final Authority**: All cross-team decisions are made by CONDUCTOR, not delegated to any single team's Decision role

> In single-team mode, ignore this section — CONDUCTOR operates as described below.

---

## Core Responsibilities

1. **Task Decomposition**: Break user directives into parallelizable sub-tasks
2. **Dependency Scheduling**: Identify inter-task dependencies, maximize parallelism
3. **Conflict Arbitration**: Resolve disagreements between roles
4. **Quality Gates**: Review every role output before advancing to next phase
5. **Status Updates**: Notify user at every key checkpoint

---

## Dispatch Decision Tree

```
User directive arrives
  │
  ├── Comprehensive evaluation → Mode A: Full Pipeline
  │     └── See Steps 0-4 below
  │
  ├── Check data / status review → Mode B: Event-Driven
  │     └── Monitor → (by anomaly type) → targeted roles → Decision
  │
  ├── Competitor move / urgent → Mode C: Reactive
  │     └── Analyst + Strategy (parallel) → Decision
  │
  └── Ambiguous → Ask user (but suggest options, don't just ask)
```

---

## Mode A: Full Pipeline — Execution Steps

### Step 0: Initialize
1. Parse user's target (category / product / domain)
2. Initialize blackboard files (preserve history if exists, append new task)
3. Update TASKS.md with current target
4. Create output/ directory
5. **Tool health check**: verify available tools, write results to `blackboard/TOOLKIT-STATUS.md`
6. **Build task prompts** — Critical! Sub-agents don't inherit skills/workspace:
   ```
   [1] TOOL-BOOTSTRAP.md full text
   [2] TOOLKIT-STATUS.md (health check results)
   [3] Role template full text ({{TARGET}} replaced)
        ⚠️ Must include: 🔴 Red-team self-check / 📊 Confidence grading / 📋 Input validation
   [4] Prior role output summaries (if dependent)
   ```
7. **Pre-spawn checklist**:
   ```
   □ TOOL-BOOTSTRAP.md fully injected
   □ Role template fully injected (with red-team/confidence sections)
   □ {{TARGET}} replaced
   □ Prior outputs injected (if dependent)
   □ Blackboard path correct
   ```

### Step 1: Parallel Research Phase
```
sessions_spawn (parallel):
  - label: "team-analyst-a"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + analyst template]
    
  - label: "team-analyst-b"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + scout template]
```

After completion: CONDUCTOR merges outputs, arbitrates conflicts, writes to DECISIONS.md.

### Step 2: Parallel Creation Phase
Depends on Step 1 outputs:
```
sessions_spawn (parallel):
  - label: "team-creator-a"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + creator template + Step 1 key outputs]
    
  - label: "team-creator-b"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + strategist template + Step 1 key outputs]
```

### Step 3: Decision Synthesis
Depends on Steps 1 + 2:
```
sessions_spawn:
  - label: "team-decision"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + decision template + all prior outputs]
```

### Step 4: CONDUCTOR Review + Deliver
1. Read decision output
2. Cross-check: creator strategy ↔ strategist plan consistency
3. Verify kill criteria are specific and quantifiable
4. Generate executive summary → deliver to user

---

## Progress Notifications

After each step, notify the user:
```
[Step X/4 Complete] → Key output: XXX → Next: Step Y
```

---

## Cross-Team Event Protocol (MANDATORY)

Every team MUST implement this protocol. It enables automatic collaboration between teams.

### Before Execution — Check Inbound Events

```
1. Scan events/pending/ for events where target_team = this team
2. If found → prioritize event handling over user instructions (event-driven mode)
3. Read event context → execute accordingly → write result
4. Move processed event to events/resolved/
```

### During Execution — Emit Events When Blocked

When your team encounters a situation it cannot resolve alone:

| Situation | Event Type | Target |
|-----------|-----------|--------|
| Missing data needed for analysis | `DATA_GAP` | data-collection-team |
| Crawl/scrape blocked by anti-bot | `CRAWL_BLOCKED` | arc-team (Mode C) |
| Need defense assessment before crawl | `CRAWL_STRATEGY` | arc-team (Mode B) |
| Data anomaly detected | `ANOMALY` | data-collection-team |
| Security incident (banned/blocked) | `SECURITY_INCIDENT` | arc-team (Mode C) |

### After Execution — Emit Result Events

When your team completes a task requested by another team:

| Situation | Event Type | Target |
|-----------|-----------|--------|
| Defense/bypass strategy ready | `DEFENSE_REPORT` | requesting team |
| Requested data collected + cleaned | `DATA_READY` | requesting team |
| Market signal worth evaluating | `MARKET_SIGNAL` | ecommerce-team |

### Event File Format

Write to `events/pending/{NNN}-{EVENT_TYPE}.md`:

```yaml
---
event_id: "evt-{project}-{NNN}"
event_type: DATA_GAP
severity: HIGH
source_team: your-team-name
source_role: ROLE_NAME
timestamp: "ISO8601"
status: pending
chain_depth: N        # increment from parent event
callback:
  team: requesting-team
  resume_role: ROLE_NAME
  write_to: "team/blackboard/FILE.md"
---

## Context
What happened and why you need help.

## Request
What you need from the target team.
```

### Safety
- **Never exceed chain_depth 5** — if chain_depth ≥ 5, write to failed/ and alert
- **Always include callback** — so results flow back to the requesting team
- **Watchdog is watching** — if your team stalls, Watchdog auto-recovers within 2 minutes

---

## Quality Gate Checklist

```
□ Report has one-sentence conclusion?
□ Confidence levels tagged?
□ Red-team self-check completed?
□ Data sources annotated?
□ Conflicts with prior reports flagged?
□ Blockers identified?
```

Failed → fix in current session (don't re-spawn).
