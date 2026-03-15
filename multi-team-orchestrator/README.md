# Multi-Team Intelligent Orchestrator v5.3.1

## The Core Idea

Most AI agent frameworks give you one agent, or a chain of agents talking to each other. That works for simple tasks.

But real-world problems — market analysis, competitive intelligence, business planning, tech evaluation — require **multiple specialists working in parallel, cross-checking each other, with independent quality review**.

This orchestrator does exactly that:

1. **You describe the task** in natural language
2. **It figures out** what expertise is needed (pattern matching + complexity assessment)
3. **It assembles a team** from 60+ specialized roles
4. **Agents execute in parallel** — not waiting for each other
5. **Independent verification** catches errors, contradictions, and weak sources
6. **Independent review + audit** (14 roles total) validates quality before delivery
7. **The system learns** — every execution feeds back into the experience database

## Key Design Decisions

### Why DNA Genes?
Every task pattern (ecommerce, competitive, tech eval...) could drift into its own conventions. The 9 DNA genes are **architectural invariants** — no matter which pattern runs, data freshness tracking (Gene 7), confidence ratings (Gene 9), and real-time progress reporting (Gene 3) are guaranteed.

### Why TTL on Data?
AI agents love to cite stale data confidently. Gene 7 forces every data point to carry an expiry timestamp. A product price from 2 hours ago? Flagged. A market report from 6 months ago? Marked `[TTL_EXPIRED]`. The system doesn't silently use rotten data.

### Why Independent QA?
The agents that execute the task can't objectively judge their own work. The Review Team (7 roles: fact-check, logic, coverage, depth, bias, actionability, lead) and Audit Team (7 roles: security, data, source, delivery, compliance, reproducibility, lead) **never participated in execution**. They only evaluate.

### Why Self-Evolution?
Static frameworks plateau. The 6 self-evolution gears ensure the system improves with use:
- **Evolution Ledger**: Quantifies improvement trajectory
- **Cross-Pattern Learning**: Success in one domain benefits others
- **Knowledge Decay Engine**: Prevents knowledge bloat — old data gets compressed, not just piled up

### Why 3 Tiers?
Not every task needs 8 agents and a 14-person review panel:
- **Lite** (2-3 agents): Quick analysis, skip formal QA
- **Standard** (4-6 agents): Full pipeline with quality gate
- **Full** (6-8 agents): Add RED-TEAM adversarial challenge for high-stakes decisions

## File Map

| File | What's Inside |
|------|--------------|
| `SKILL.md` | The complete system: decision engine, 11-step pipeline, 60+ role definitions, 25 hard constraints |
| `references/pattern-*.md` | 5 domain-specific patterns with role prompts, red lines, and output templates |
| `references/team-review.md` | 7 review role prompt templates |
| `references/team-audit.md` | 7 audit role prompt templates |
| `references/cross-pattern-learning.md` | How insights transfer between patterns |
| `references/model-abstraction-protocol.md` | 4-layer model-agnostic design |
| `references/knowledge-decay-engine.md` | TTL rules, compression protocols, health metrics |
| `experience-db/*.md` | 12 template files — fill these as the system runs |
| `CHANGELOG.md` | Version history from v1.0 to v5.3.1 |

## Usage

This is an [OpenClaw](https://github.com/openclaw/openclaw) AgentSkill. Copy it to your skills directory:

```bash
cp -r multi-team-orchestrator/ ~/.openclaw/workspace/skills/multi-team-orchestrator/
```

The orchestrator activates when a task requires 2+ professional domains. You can also trigger it with keywords like "multi-team analysis", "comprehensive research", "deep analysis".

## What's Not Included

Some components are private and not included in this open-source release:
- **Pattern B** (Patent Mining) — proprietary methodology
- **Pattern R** (R&D Innovation) — proprietary methodology  
- **Pattern H** (Elite Intelligence) — full version with specialized roles
- **Security Architecture** — agent security protocols
- **Experience Data** — operational data from production runs (empty templates provided)

The open-source version includes the complete orchestration framework, 5 domain patterns, all quality assurance systems, and the full self-evolution engine. You can build and run effective multi-team orchestration with what's here.
