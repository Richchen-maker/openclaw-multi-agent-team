# Building Your Own Team

This guide walks you through creating a custom multi-agent team for any domain.

## Step 1: Define Your Roles

Ask yourself: **What specialists would I hire if budget were unlimited?**

Examples by domain:

| Domain | Analyst Roles | Creator Roles | Monitor | Decision |
|--------|--------------|---------------|---------|----------|
| E-commerce | Market Researcher, Product Scout | Content Creator, Pricing Strategist | Data Analyst | Decision Oracle |
| Content Marketing | Audience Researcher, SEO Analyst | Writer, Designer, Editor | Performance Tracker | Editorial Director |
| Investment | Market Analyst, Due Diligence | Thesis Writer, Risk Modeler | Portfolio Monitor | Investment Committee |
| Research | Literature Reviewer, Data Collector | Hypothesis Generator, Report Writer | Experiment Monitor | Principal Investigator |

**Rule of thumb**: 2-3 analyst roles, 2-3 creator roles, 1 monitor, 1 decision maker.

## Step 2: Design the Dependency Graph

Which roles can run in parallel? Which depend on others?

```
Example: E-commerce Full Pipeline

[Parallel]  RADAR ─┐
                    ├── CONDUCTOR merges ──┐
[Parallel]  SCOUT ─┘                      │
                                           │
[Parallel]  FORGE ─┐   (depends on above) │
                    ├── CONDUCTOR merges ──┤
[Parallel]  BLADE ─┘                      │
                                           │
[Sequential] ORACLE ── (depends on all) ──┘
```

**Maximize parallelism**: If two roles don't read each other's output, run them simultaneously.

## Step 3: Write Role Templates

Each role template is a markdown file with this structure:

```markdown
# Role: [NAME] ([Description])

> You are [team name]'s [role description]. Your task is [mission].
> Target: {{TARGET}}
>
> ⚠️ Output rules: [reference TOOL-BOOTSTRAP rules]

## Your Mission
[What this role does, in 2-3 sentences]

## 📋 Input Validation
- [ ] Check for prerequisite outputs from prior roles
- [ ] Validate {{TARGET}} is specific enough
- [ ] Check DECISIONS.md for prior relevant decisions

## Execution Steps

### Phase 1: [Name] ([Weight]%)
1. [Specific search/analysis instructions]
2. [Tool commands with exact syntax]
3. [What to extract from results]

### Phase 2: [Name] ([Weight]%)
...

## Output Format
Write to: `./output/[filename].md`
[Exact markdown template for the output]

## 🔴 Red-Team Self-Check (mandatory before output)
1. [Skeptical question about own conclusions]
2. [Check for common biases]
3. [Verify data freshness and accuracy]

## 📊 Confidence Grading
| Level | Criteria |
|-------|----------|
| HIGH | ≥3 independent sources + <12 month data + quantified |
| MEDIUM | 2 sources + partially quantified + <30% inference |
| LOW | Single source or >12 month data or >50% inference |
```

### Template Tips
- Be **extremely specific** about tool commands — sub-agents can't guess
- Include **exact output format** — sub-agents need structure
- Red-team questions should challenge the role's most likely blind spots
- Weight percentages help the agent allocate effort

## Step 4: Set Up the Blackboard

Create markdown files for each shared state category your team needs:

```
blackboard/
├── TASKS.md          # Always needed — task state tracking
├── DECISIONS.md      # Always needed — decision log
├── [DOMAIN].md       # Domain-specific shared data
└── ALERTS.md         # If you have a monitor role
```

## Step 5: Configure the Orchestrator

Copy `framework/ORCHESTRATOR.md` and customize:
1. Update the dispatch decision tree for your domain's trigger phrases
2. Define your step sequence (which roles run when)
3. Set `runTimeoutSeconds` appropriate for your roles (600s = 10min is a good default)
4. Customize quality gate checks for your domain

## Step 6: Customize TOOL-BOOTSTRAP

Copy `framework/TOOL-BOOTSTRAP.md` and add:
1. Your specific available tools (API keys, MCP servers, etc.)
2. Domain-specific search strategies
3. Any tools that are unavailable (so agents don't waste time)

## Step 7: Test

1. Start with a simple target to validate the pipeline
2. Check that sub-agents receive the full template (not truncated)
3. Verify outputs match the expected format
4. Tune timeouts if agents run out of time

## Common Patterns

### Adding a New Role
1. Create `templates/XX-rolename.md` following the template structure
2. Add the role to your ORCHESTRATOR dispatch sequence
3. Add any new blackboard files the role needs
4. Update TOOL-BOOTSTRAP if the role needs special tools

### Removing a Role
1. Remove from ORCHESTRATOR dispatch sequence
2. Update any roles that depended on the removed role's output
3. Clean up unused blackboard files

### Changing the Dependency Graph
1. Update ORCHESTRATOR step definitions
2. Adjust which prior outputs get injected into each role's prompt
3. Test that parallel roles truly don't need each other's output
