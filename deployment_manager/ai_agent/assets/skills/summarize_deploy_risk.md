# Skill: Summarize Deploy Risk

Trigger:
- When the structured summary JSON includes `context` or `project`.

Inputs:
- Structured summary JSON from the agent (context, project, plan mappings, diff summary, object changes).

Output:
- 4-7 bullet summary focused on deployment safety and risks.
- A clear verdict line: `Safety: safe`, `Safety: caution`, or `Safety: risky`.
- If `project.missing_in_deploy` is non-empty, call out the object types and counts.
- If `plan.new_copy_total` is non-zero, call out how many new copies and which object types.
- If `project.override_targets_missing_ids` is non-empty, call out overrides on targets with missing IDs.
- If `context.deploy_summary.unselected_hooks` is non-empty, mention that dependent hooks will not deploy.
- Highlight multi-target mappings from `project.multi_target_sources`.
- Highlight ID mismatches or unexpected target IDs in `plan.mappings` (source->target).
- Call out repeated changes that touch critical fields or appear across all objects.
- If `warnings.conflicts` is non-empty, flag that conflicts must be resolved before deploy.
- If `warnings.warnings` contains queue engine warnings, mention manual action required.

Notes:
- Prefer structured summary JSON over raw log excerpts.
- Focus on ID mapping risks, missing objects, and attribute overrides.
- Keep it short and action-oriented.
