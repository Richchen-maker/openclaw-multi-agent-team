# Blackboard Specification

> The blackboard is the shared state layer. All inter-agent communication goes through it.

## Directory Structure

```
blackboard/
├── TASKS.md          # Current task state machine
├── DECISIONS.md      # Confirmed decisions (append-only, immutable)
├── SIGNALS.md        # Domain signals from analyst roles
├── DATA.md           # Shared domain data (specs, costs, parameters)
├── COMPETITORS.md    # Competitive landscape mapping
├── METRICS.md        # Key metric snapshots
├── ALERTS.md         # Alert queue
└── TOOLKIT-STATUS.md # Tool availability (written by CONDUCTOR at Step 0)
```

## Access Control

| File | Write Access | Read Access |
|------|-------------|-------------|
| TASKS.md | CONDUCTOR only | All |
| DECISIONS.md | CONDUCTOR + Decision role | All |
| SIGNALS.md | Analyst roles | All |
| DATA.md | Analyst + Creator roles | All |
| COMPETITORS.md | Analyst roles | All |
| METRICS.md | Monitor roles | All |
| ALERTS.md | CONDUCTOR + Monitor roles | All |
| TOOLKIT-STATUS.md | CONDUCTOR only | All |

## Write Format

Every blackboard entry must include:

```markdown
## [ENTRY-ID] | [YYYY-MM-DD HH:MM]
- **Author**: [Role name]
- **Source**: [Tool/method used to obtain data]
- **Content**: [The actual data/decision/signal]
- **Confidence**: [HIGH/MEDIUM/LOW]
```

## Rules

1. **Append-only for DECISIONS.md** — never edit or delete confirmed decisions
2. **Timestamp everything** — no undated entries
3. **Source everything** — no unsourced data
4. **One writer per entry** — if two roles need to write related info, use separate entries
5. **Conflict flag** — if new data contradicts existing entries, add `[CONFLICT]` tag and let CONDUCTOR resolve
