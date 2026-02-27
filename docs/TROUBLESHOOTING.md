# Troubleshooting

## Sub-Agent Gets Truncated Template

**Symptom**: Agent output is low quality, missing red-team checks, no confidence grading.

**Cause**: Task prompt too long, got truncated before the quality control sections.

**Fix**: 
- Don't remove quality sections to save tokens — they're mandatory
- If prompt is too long, summarize prior role outputs instead of including full text
- Check that TOOL-BOOTSTRAP + template + context fits within model context window

## Sub-Agent Times Out

**Symptom**: `runTimeoutSeconds` exceeded, partial or no output.

**Fix**:
- Increase `runTimeoutSeconds` (default 600s, try 900s for heavy research roles)
- Reduce the number of search rounds in the template
- Split the role into two lighter roles

## Conflicting Role Outputs

**Symptom**: Role A says "blue ocean" but Role B says "red ocean."

**This is expected!** Different roles have different perspectives. CONDUCTOR should:
1. Log the conflict in `DECISIONS.md`
2. Apply the arbitration protocol (quantified data > qualitative judgment)
3. Record the resolution with reasoning

## Agent Calls Prohibited Tools

**Symptom**: Agent tries to spawn sub-agents or call unavailable tools.

**Fix**: Ensure TOOL-BOOTSTRAP explicitly lists `⛔ Prohibited` tools. Agents need to be told what NOT to do.

## Empty Blackboard Files

**Symptom**: Roles can't find prior outputs.

**Fix**: 
- Check that CONDUCTOR writes prior role summaries to blackboard after each step
- Verify file paths in templates match actual blackboard directory structure
- Ensure Step 0 initialization creates all needed files

## Low Confidence Across All Reports

**Symptom**: Everything is tagged MEDIUM or LOW.

**This might be correct** — it means available data is limited. Options:
- Accept the uncertainty and note it in the decision
- Add more specific data sources to TOOL-BOOTSTRAP
- Consider whether the domain has enough public data for AI-driven research

## Agent Ignores Output Format

**Symptom**: Free-form text instead of structured markdown.

**Fix**: Make the output format more explicit in the template. Include the full markdown skeleton, not just a description. The more structure you provide, the more the agent follows it.
