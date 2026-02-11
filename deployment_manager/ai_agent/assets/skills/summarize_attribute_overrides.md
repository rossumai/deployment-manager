# Skill: Summarize Attribute Overrides

Trigger:
- When structured summary JSON contains `project.override_targets_missing_ids` or `context.deploy_summary`.

Inputs:
- Structured summary JSON from the agent (context, project, plan mappings, diff summary).

Output:
- 2-3 bullet summary of attribute overrides and their risk.
- Flag overrides on targets with missing IDs (new objects).
- Mention overrides that appear to be unused in diffs.
- If overrides are absent, state "No attribute overrides detected."

Notes:
- Prefer structured summary JSON; do not rely on raw logs.
- Keep it short and action-oriented; avoid repeating any risk already called out.
