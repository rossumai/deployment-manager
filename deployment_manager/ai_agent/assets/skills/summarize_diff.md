# Skill: Summarize Diff Output

Trigger:
- When the log includes lines starting with "diff --git", "+++", "---", "@@" or contains "Changes:".

Inputs:
- Recent log excerpt that includes the diff.

Output:
- 3-6 bullet summary of the diff.
- Note added/removed files.
- Call out deletions or conflict markers.

Notes:
- Keep it short and action-oriented.
- If no diff is present, say "No diff detected".
