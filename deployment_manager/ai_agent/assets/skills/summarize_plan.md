# Skill: Summarize Deploy Plan

Trigger:
- When the log contains "Plan visualization" or a deploy plan summary.

Inputs:
- Recent log excerpt.
- Deploy file path when available.
- Structured summary JSON from the agent (plan counts, mappings, diff counts, repeated changes).

Output:
- 3-5 bullet summary of planned changes.
- Call out conflicts or prompts needing user input.

Notes:
- Avoid rewriting full logs.
- Use the plan counts and mappings from the JSON to describe scope.
- Highlight any errors or missing credentials.
