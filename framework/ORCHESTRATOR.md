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
