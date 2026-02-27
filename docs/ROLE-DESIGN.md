# Role Design Best Practices

## The 5 Non-Negotiable Sections

Every role template **must** have:

1. **Mission** — One paragraph explaining what this role does
2. **Input Validation** — Checklist of prerequisites before starting
3. **Execution Steps** — Specific tool commands and analysis procedures
4. **Output Format** — Exact markdown template for the output file
5. **Red-Team Self-Check** — 3-5 skeptical questions the agent must answer before submitting

## Writing Good Execution Steps

### Be Specific About Tools
❌ Bad: "Research the market size"
✅ Good: `web_search query="{{TARGET}} market size 2025 2026 CAGR" count=10`

### Specify What to Extract
❌ Bad: "Analyze the results"
✅ Good: "Extract: market size ($), CAGR (%), top 3 growth drivers, seasonality pattern"

### Include Fallback Strategies
```
1. Try: web_search query="exact keyword"
2. If no results: web_search query="synonym keyword"
3. If still nothing: web_fetch a known industry report URL
4. If all fail: mark as [DATA UNAVAILABLE] with LOW confidence
```

## Red-Team Questions by Role Type

### Analyst Roles
- Is the trend real demand or algorithm/media bubble?
- Is the data recent enough (≤12 months)?
- Am I only seeing survivors? What's the failure rate?
- Am I missing offline/alternative channel data?

### Creator Roles
- Are selling points based on real user feedback or my assumptions?
- Would this content look identical to top 3 competitors? (>60% overlap = no differentiation)
- Does the conversion path have clear logic: pain → solution → trust → action?

### Strategy Roles
- Did I account for hidden costs (returns, inventory, ad cost inflation)?
- Are my sales volume assumptions backed by data or gut feeling?
- Is the break-even realistic given the competitive landscape?

### Decision Roles
- Am I falling for confirmation bias — cherry-picking data that supports "Go"?
- Would I reach the same conclusion if I read the reports in reverse order?
- Are kill criteria too loose (never trigger) or too strict (always trigger)?

## Confidence Grading

Enforce consistent confidence tagging across all roles:

| Level | Standard |
|-------|----------|
| **HIGH** | ≥3 independent sources, cross-validated, <12 months old, quantified |
| **MEDIUM** | 2 sources, partially quantified, <30% inference |
| **LOW** | Single source, or >12 months old, or >50% inference |

## Common Mistakes

1. **Template too vague** → Agent doesn't know what tools to use or what to output
2. **No output format** → Agent produces unstructured text that other roles can't parse
3. **No red-team check** → Agent's first draft becomes final without scrutiny
4. **Missing input validation** → Agent starts work without checking prerequisites
5. **Overloaded role** → One role doing too many things → split into two
6. **No weight allocation** → Agent spends equal time on all phases instead of prioritizing
