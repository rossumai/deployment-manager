# Skill: Compare Project Tree

Trigger:
- When the structured summary JSON includes `project.source_name_index`, `project.target_name_index`, or `mapping.id_discrepancies`.

Inputs:
- Structured summary JSON fields: `project.source_name_index`, `project.target_name_index`, `plan.mappings`, `mapping.id_discrepancies`.

Output:
- 2-4 bullet summary focused on ID/name mismatches and missing objects in the local tree.
- Call out any entries in `mapping.id_discrepancies` with their object type and IDs.
- Treat `reason: name_collision` as high risk (target name matches a different source object).
- If `mapping.id_discrepancies` is empty, state "No ID/name mismatches detected in local tree.".
- If `project.source_name_index` or `project.target_name_index` are missing for any mapped object types, warn that local metadata is incomplete.

Notes:
- Prefer `mapping.id_discrepancies` to avoid dumping full object JSON.
- Keep it short and action-oriented; avoid repeating details already covered in other skills.
