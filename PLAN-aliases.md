# Plan: alias-based naming, code files, implicit merge and bidirectional deploy

Status: plan only, nothing implemented yet. This is a breaking release: the `Name_[id]` layout and multi-target deploys are not supported.

Sample files for every feature: [PLAN-samples.md](PLAN-samples.md).

## 1. Goals

- Every object gets a unique, user-friendly alias (slug). It is used as the object's path and as the way other objects reference it in JSON.
- Remote names are not unique; aliases are, per subdir and type.
- Pull, push and deploy translate aliases to IDs/URLs and back at the API boundary.
- Code (formulas, hook code, rule conditions) lives in its own `.py` / `.js` files, versioned next to the JSON for readable diffs, and is folded into the JSON on push.
- Pull merges remote changes into local edits without prompting, unless there is a real conflict.
- Deploy works in both directions (dev → prod and prod → dev):
  - with a deploy file (created by the wizard as today), the same file in either direction;
  - or without one, in which case everything in the source is deployed.
- The deploy plan shows only slugs and only changes, and deploy sends exactly what the plan shows.

## 2. Decisions

| Topic | Decision |
|---|---|
| Legacy layout | Not supported. prd2 refuses to run on directories with `*_[<id>]` paths. No migration command; existing projects re-init and pull. |
| Alias scope | Unique per (subdir, type). The same alias in two subdirs means "the same logical object". |
| Object identity | Each object JSON keeps its own `id` and `url`. No separate mapping file; the alias/ID/name index is built in memory by scanning. |
| Extra files and folders | Ignored. prd2 only reads files at known layout positions that look like objects, deletes only files it synced, and a problem in one file skips only that object (section 4). |
| Local state | `<org>/.prd_state/<type>/<id>.json`, git-ignored: the full last-synced remote object plus code-file bases. Replaces `non_versioned_object_attributes.json`. |
| Code files | Formulas, hook code and rule `trigger_condition` are extracted to their own files. Both the code file and the JSON are versioned, for readable code diffs in commits. |
| References | `prd://<type>/<alias>` tokens in JSON. Code is never tokenized. |
| Plain-number IDs on deploy | Replaced in code, `settings` and `metadata` using the alias index. The plan shows them as slugs. IDs whose type can't be determined are asked once, before the plan. |
| Changes made in the destination | Merged automatically: a field changed only in the destination since the last deploy stays there and is rebased into the source files (local only), and the plan reports it. `--no-rebase` overwrites instead. |
| Deploy questions | At most two: an ambiguous plain-number ID (once, then pinned) and "Apply this deploy?" (`-y` skips it). Everything else is shown in the plan or decided by defaults. |
| IDs in the deploy plan | Never shown. Objects and references appear as slugs. |
| Pull | Implicit three-way merge of every attribute against the last-synced remote object. |
| Multi-target deploy | Dropped. Each object has exactly one counterpart: the object with the same alias in the target dir. |
| Deploy file | Same structure and wizard as today (`deploy template create`). Objects are referenced by alias, and `attribute_override` (regex form included) sits directly on the object. One file works in both directions. |
| Deploy without a file | `prd2 deploy run --from <dir> --to <dir>`, in either direction: everything in the source dir is deployed as it is, without overrides. |
| Variables | Defined once per subdir in `prd_config.yaml` (`variables:` under the subdirectory) and shared by every deploy file. `${vars.NAME}` is the destination's value and `${source.NAME}` the source's; `${env.NAME}` reads an OS environment variable. A deploy file can override values for itself; `--var NAME=value` overrides one for a run. |
| Token owner | Read from the destination's `token_owner_id` variable. If it's missing, deploy creates a technical admin user with a generated password that is never stored, and saves the user's ID as that variable. |
| Integration credentials | Supported like any other object (section 11): pulled, pushed and deployed with overrides, and referenced from hooks by alias. Secret values come from the environment's secrets file. |
| Reverse direction | The same deploy file with `--from` / `--to` swapped. Override values reference per-dir `variables`, and each run uses the destination's values. `deploy template reverse` and `reverse_mapping_after_deploy` are dropped. |
| Organization object | Deployed only with `patch_target_org: true`; a missing key now means `false`. Without a deploy file: `--include-organization`. |
| Deploy state | One per deploy file, shared by both directions. Without a deploy file, one per dir pair, also shared. |
| Deploy plan | `--changes-only` is the default. |

## 3. Aliases

### Format and scope
- Format: `[a-z0-9][a-z0-9_-]*`. Lowercase only, which is safe on case-insensitive file systems.
- Unique per (subdir, type).
- Schema and inbox reuse their queue's alias.
- Nested types are scoped to their parent, and their alias includes the parent: `invoices-cz/rejection` (email template), `ap-engine/invoice-id` (engine field).

### Filesystem layout
```
<org>/
  organization.json
  .prd_state/                         # git-ignored, see section 5
  <subdir>/
    workspaces/<ws>/workspace.json
    workspaces/<ws>/queues/<queue>/queue.json
    workspaces/<ws>/queues/<queue>/schema.json
    workspaces/<ws>/queues/<queue>/inbox.json
    workspaces/<ws>/queues/<queue>/formulas/<schema_id>.py
    workspaces/<ws>/queues/<queue>/email_templates/<et>.json
    hooks/<hook>.json
    hooks/<hook>.py | .js
    rules/<rule>.json
    rules/<rule>.py
    labels/<label>.json
    engines/<engine>/engine.json
    engines/<engine>/engine_fields/<field>.json
    integration_credentials/<credential>.json
```

### Alias allocation (pull)
- An object already on disk (matched by `id`) keeps its alias. A rename in Rossum only changes `name` in the JSON. The file does not move and git history stays continuous.
- A new object gets a slug of its name: diacritics stripped, lowercase, non-alphanumerics replaced by `-` and collapsed, ends trimmed. An empty result falls back to the singular type name.
- **Environment marker stripped first:** if the name starts or ends with the subdir's name as a separate word (with or without brackets or a separator), that word is left out of the slug.
  - In subdir `dev`: `Invoices CZ (DEV)`, `Invoices CZ [DEV]`, `Invoices CZ - DEV` and `DEV Invoices CZ` all give `invoices-cz`.
  - In subdir `prod`, `Invoices CZ` also gives `invoices-cz`.
  - So the same object usually gets the same alias in every environment. Only the alias is affected, never the name.
- Collision within the scope:
  1. prefix the parent alias (`cz-invoices`);
  2. then append `-2`, `-3`, … in ascending ID order.

  This keeps aliases identical across clones.
- Aliases are sticky: prd2 never changes an existing alias automatically.

### Renaming
- `prd2 alias mv <type>/<old> <new>` moves the file or folder and rewrites every token in the org dir, in deploy files and in deploy state.
- A plain `git mv` is detected by push as a rename (same `id`, see section 9). Tokens still pointing at the old alias fail validation, with a hint to use `prd2 alias mv`.
- If two environments still ended up with different aliases for the same object, a one-time `prd2 alias mv` in one of them aligns them (see section 10).

## 4. Identity and the in-memory index

- Each object JSON contains `id` and `url` exactly as Rossum returns them.
- At command start prd2 walks every subdir of the org dir (see "Which files are objects" below) and builds `AliasIndex`, mapping `(type, id)` to `(subdir, alias, path, name)`. It is extended in memory with aliases assigned during the run and IDs created during the run.
- **Checks during the scan.** Each problem skips only the affected object, is reported, and the command continues:
  - an alias used twice within (subdir, type), e.g. two `queues/invoices` folders in different workspaces;
  - an `id` in two files (see "Copies" below);
  - an alias that doesn't match the format;
  - a JSON that doesn't parse.
- `prd2 alias list [<dir>]` prints the alias / type / ID / name table. Nothing like it is stored.

### Which files are objects
Users and tools (Claude, editors, scripts) create ad-hoc folders and files in the project. prd2 must ignore them: never read, change, move or delete them, and never fail because of them.

- **Known layout only.** prd2 walks the layout from section 3 instead of globbing `**/*.json` (today's `find_all_object_paths`). It looks only at:
  - in the project root: `prd_config.yaml`, `credentials.yaml`, the configured org dirs, `deploy_files/`, `deploy_states/`, `deploy_secrets/`;
  - in an org dir: `organization.json`, `credentials.yaml`, `.prd_state/`, the configured subdirs;
  - in a subdir: `workspaces/<alias>/workspace.json`, `workspaces/<alias>/queues/<alias>/{queue,schema,inbox}.json`, `…/formulas/<schema_id>.py`, `…/email_templates/<alias>.json`, `hooks/<alias>.json` (+ `.py` / `.js`), `rules/<alias>.json` (+ `.py`), `labels/<alias>.json`, `engines/<alias>/engine.json`, `engines/<alias>/engine_fields/<alias>.json`, `integration_credentials/<alias>.json`, and the pulled-only `workflows/`.

  Everything else is not looked at: `.claude/`, `notes/`, `scratch/`, `.venv/`, `node_modules/`, `__pycache__/`, `*.md` files, or a JSON in `workspaces/ap-cz/analysis/`. A folder without its object file (e.g. `workspaces/drafts/` with no `workspace.json`) isn't an object either.
- **Alias names.** A path segment that should be an alias must match the alias format. Names starting with `.` or `_`, or containing uppercase letters or dots, are never objects.
- **A JSON at a known position must look like that object:**
  - with `id` / `url`: the `url` must point to that type (`…/hooks/…` for a file in `hooks/`);
  - without `id` (a new object): it must have the type's required create fields (section 9). Otherwise it is ignored, with a line in the push summary, e.g. "ignored hooks/payload.json: not a hook (missing events, queues, config)";
  - creates still need confirmation before they run, so nothing a tool wrote is created silently.
- **Code files belong to a known object:**
  - `hooks/<alias>.py` / `.js` is read only when `hooks/<alias>.json` is a code hook;
  - `rules/<alias>.py` only together with `rules/<alias>.json`;
  - `formulas/<schema_id>.py` only for a formula field of that schema.

  Other files (`hooks/test_mdh_vendors.py`, `formulas/helpers.py`) are ignored with a notice, not treated as errors.
- **Copies.** A second file with the same `id`, e.g. `hooks/mdh-vendors-backup.json` copied by a tool:
  - the file at the base's recorded `path` (section 5) is the object; the copy is ignored and reported;
  - with no base to decide, both are reported and that object is skipped for the run.
- **Reporting:** files outside the type folders are ignored silently. Suspicious files inside them (look like objects but aren't, copies, orphan code files) are summarised in one line per command; `--verbose` lists them.

### What prd2 deletes or moves
- **Files:** only files at known positions that prd2 synced, i.e. the object has a `.prd_state` base. Never a file it didn't write.
- **Folders:** only when they become empty because prd2 removed its own files from them. This replaces today's `delete_empty_folders`, which removes every empty folder under `workspaces/`, and `delete_empty_formula_dir`, which deletes a queue folder holding only `formulas/`.
- **Folders with extra files:** when a queue or workspace is removed in Rossum but its folder also holds other files, prd2 removes its own files, leaves the folder and the extra files, and prints a notice.
- **Moves and renames** (a queue moved to another workspace, `prd2 alias mv`) move the whole folder, extra files included.
- **Git:** the `modified_by` clean filter in `.gitattributes` is limited to object positions (`*/workspaces/**/*.json`, `*/hooks/*.json`, …) instead of `*.json`, so tools' own JSON files pass through git untouched.

## 5. Local state: `.prd_state`

Git-ignored state, one file per object:

```
<org>/.prd_state/<type>/<id>.json
{
  "base": { ...the complete remote object as last synced: every attribute, raw API form... },
  "path": "sandbox-org/dev/hooks/mdh-vendors.json",
  "code_files": { "hooks/mdh-vendors.py": "<text prd2 last wrote to that file>" }
}
```

- **`base`** is the full remote object, so **every attribute** takes part in the pull merge (section 8) and in push's change detection (section 9), not just code. Pull, push and deploy all update it:
  - pull stores the remote object;
  - push stores the API response;
  - deploy stores its responses in the target org's state.
- **`code_files`** has nothing to do with the pull merge. It is only the base for keeping each code file in sync with its JSON field (section 6). It tells which of the two was edited by hand when they differ.
- **`modified_at`** for push's timestamp check is read from `base.modified_at`. There is no separate store.
- **`path`:** where the object's file was at the last sync, updated on every sync. It is not used for identity. Push uses it to put a deleted object in its subdir and to recognise moves.
- **Raw API form:** the object is stored as Rossum returns it; only `path` changes when an alias is renamed.
- **One file per object:** the global `NON_VERSIONED_ATTRIBUTES_FILE_LOCK` in [read_write.py](deployment_manager/common/read_write.py) goes away.
- **No state** (fresh clone, new object): the file's git HEAD version is used as the base.
- **Why not git HEAD as the base:** HEAD is the last commit, not the last sync. Example: you pull without committing and then change a field back. A HEAD-based merge sees no local change and quietly re-applies the remote value.

## 6. Code files

| Object | JSON field | Code file |
|---|---|---|
| Schema | each datapoint's `formula` | `queues/<queue>/formulas/<schema_id>.py` |
| Hook | `config.code` (not for `extension_source == rossum_store`) | `hooks/<alias>.py` or `.js`, depending on `config.runtime` |
| Rule | `trigger_condition` | `rules/<alias>.py` (new) |

- **Both are versioned:** the code file and the JSON field, as today for formulas and hooks. Commits then show code changes as readable diffs rather than only as the one-line JSON string. A code change therefore appears in both files of a commit.
- **`.gitignore`:** `prd2 init` adds `**/.prd_state/` (section 5) and `.DS_Store`. The latter is a pattern without a slash, so it matches macOS Finder files at any level of the project. Code files are not ignored.
- **One table-driven code-file engine** replaces the separate formula and hook handling in [dependencies.py](deployment_manager/commands/upload/dependencies.py), [saver.py](deployment_manager/commands/download/saver.py) and [read_write.py](deployment_manager/common/read_write.py). Adding another code field later is one row in the table.
- **Expand** (JSON → file) runs after every write, so prd2 always leaves the two identical.
- **Fold** (file → JSON) runs at the start of every pull, push and deploy, before change detection, so a `.py` edit is part of the JSON being compared. Today push derives the JSON change from the `.py` change after reading git status ([upload/directory.py:129-136](deployment_manager/commands/upload/directory.py:129)).
- **Check for each code file:** if the file and the JSON field differ, one of them was edited by hand since prd2 last wrote them. The base (the text in `.prd_state` `code_files`) tells which one:

| File vs base | JSON field vs base | Action |
|---|---|---|
| same | same | nothing |
| same | changed (JSON edited by hand) | rewrite the file from the JSON |
| changed | same | fold the file into the JSON |
| changed | changed | line merge with `git merge-file`; if they overlap, conflict markers go into the file |
| missing | – | write the file from the JSON, record the base |

- **Git merges** apply to both files. A merge conflict in a code file is resolved in the `.py`, and the fold then carries it into the JSON. Push and deploy refuse any code file, or any JSON, that still contains conflict markers.
- **Deleting code:** deleting a code file only brings it back on the next run. A formula is removed in `schema.json`; hook or rule code is removed in its JSON.
- **Unknown formula file:** a formula file whose `schema_id` doesn't exist in the schema is ignored with a notice (section 4).
- **New rule created locally:** `rules/<alias>.json` without `trigger_condition`, plus `rules/<alias>.py`. The fold fills the field in.

## 7. Reference tokens

### Syntax

| Remote value | Local token |
|---|---|
| `https://acme.rossum.app/api/v1/queues/123` | `prd://queues/invoices-cz` |
| `123` (int) | `prd://queues/invoices-cz#id` |
| `"123"` (string) | `prd://queues/invoices-cz#id-str` |
| URL with suffix `.../queues/123/export?format=xml` | `prd://queues/invoices-cz/export?format=xml` |
| object in another subdir of the same org | `prd://queues/invoices-cz@uat` |
| nested type | `prd://email_templates/invoices-cz/rejection` |
| organization | `prd://organization` |

- The type segment is the Rossum resource name, the same as the URL path and `Resource` values.
- The token's base URL comes from the org dir's `api_base`, so JSON files don't depend on any environment's URL.
- A `#id` token that forms the whole JSON string becomes an integer when resolved. Inside a longer string it becomes digits.

### What is converted
- **Always: structural fields**, from one `REFERENCE_FIELDS` table that pull, push and deploy all use:

| Type | Fields |
|---|---|
| workspace | `organization`, `queues[]` (read-only) |
| queue | `workspace`, `schema`, `inbox` (read-only), `hooks[]`, `webhooks[]`, `engine`, `dedicated_engine`, `generic_engine`, `rules[]` (read-only) |
| schema | `queues[]` (read-only) |
| inbox | `queues[]` |
| hook | `queues[]`, `run_after[]`, `integration_credentials[]` |
| integration_credential | `organization`, `hooks[]` (read-only) |
| rule | `queues[]`, `actions[].payload.labels[]`, `actions[].payload.email_template`, `actions[].payload.queue` (`change_queue`) |
| email_template | `queue` |
| engine | `training_queues[]` |
| engine_field | `engine` |
| organization | `workspaces[]` (read-only) |

- **Always: Rossum URLs anywhere in `settings`/`metadata`.** They are unambiguous.
- **Bare IDs in free-form settings: only when** the key name implies the type and that ID exists in the index for that type. This reuses `_reference_type_from_key` ([reference_replacer.py:89](deployment_manager/commands/deploy/subcommands/run/deploy_objects/reference_replacer.py:89)), moved to a common module. Anything ambiguous stays raw and is listed in the pull summary.
- **Never:**
  - code (formulas, hook code, rule conditions); deploy still replaces plain-number IDs there (section 10);
  - users / `token_owner`, `hook_template`, connectors, workflows;
  - anything not in the index.

  These stay raw, and resolving tokens passes non-token values through untouched.
- A token written by hand is kept by pull as long as it resolves to the remote value (section 8).

### Ordering of reference lists
Rossum returns some reference lists in no stable order. Today's fix (`DEPLOY_SORT_LIST_KEYS` and `sort_object_list_attributes`, commits `2791e4e` and `d3db460`) sorts them so a different remote order never shows as a diff. With tokens, the same guarantee holds:

- **Unordered lists are sorted by alias** whenever prd2 writes a file: pull, push write-back, deploy writing into the destination dir, rebase, and `prd2 alias mv`.
  - The sort runs after encoding, so the order is by alias (readable, and the same in every environment), not by numeric ID. Today's sort runs on raw URLs.
  - Sort key: tokens by type, alias and `@subdir`, then anything left raw (objects outside the project) by its text. This is plain string ordering, so it is identical on every machine.
- **Which lists:** `DEPLOY_SORT_LIST_KEYS` becomes an `unordered` flag in the `REFERENCE_FIELDS` table, so tokenizing and sorting use one definition:
  - `hook.queues`, `hook.run_after`, `hook.integration_credentials`;
  - `queue.hooks`, `queue.webhooks`;
  - `workspace.queues`, `organization.workspaces`, `organization.users`, `schema.queues`, `inbox.queues`, `rule.queues`, `engine.training_queues`, `email_template.triggers`, `integration_credential.hooks`;
  - `rule.actions[].payload.labels` (new; the sort learns paths inside lists).
- **Never sorted**, because the order may matter or was authored: `queue.rules`, `hook.events`, `rule.actions`, schema `content`, and every list inside `settings` / `metadata` (e.g. `queue_ids`).
- **Comparisons treat unordered lists as sets:** the pull merge (set merge), push change detection, the deploy plan diff and the deploy-state comparison. A remote that returns `queue.hooks` in a different order is never a change, a conflict or a plan diff. Deploy state stores these lists sorted.
- **Payloads** send them in the sorted order; the API doesn't depend on it.
- **`prd2 alias mv`** re-sorts the lists it rewrites. That is the only way an entry moves within such a list, and the move is part of the rename commit.

### Invariant
`decode(encode(remote)) == remote` for every object, with unordered reference lists compared as sets. Pull and push alone never change anything in Rossum.

## 8. Pull

### Steps
1. Download all objects (unchanged).
2. Build the index from disk and assign aliases to new remote objects (section 3).
3. For each object:
   1. fold code files into the local JSON;
   2. convert the remote object (R) and the base (B) to tokens with the current index, so local (L), R and B have the same shape;
   3. merge every attribute;
   4. write;
   5. expand code files;
   6. set the base to R.
4. Remove objects that disappeared, and move folders whose parent changed (e.g. a queue moved to another workspace). The alias stays.

Local changes are detected by comparing against the base, not against git status. This replaces the "Should the remote version overwrite the local one? (y/n/yy)" prompt in `should_write_object` ([download/helpers.py:40](deployment_manager/commands/download/helpers.py:40)) and the formula branch of `replace_code_paths`.

### Example: merge without conflict
```
base (B):   {"name": "MDH",         "events": ["annotation_content.initialize"],                              "settings": {"timeout": 30, "dataset": "vendors"}}
local (L):  {"name": "MDH",         "events": ["annotation_content.initialize"],                              "settings": {"timeout": 60, "dataset": "vendors"}}
remote (R): {"name": "MDH vendors", "events": ["annotation_content.initialize", "annotation_content.updated"], "settings": {"timeout": 30, "dataset": "vendors_v2"}}
merged:     {"name": "MDH vendors", "events": ["annotation_content.initialize", "annotation_content.updated"], "settings": {"timeout": 60, "dataset": "vendors_v2"}}
```
`name`, `events` and `settings.dataset` changed only remotely, so they are taken from R. `settings.timeout` changed only locally, so it is kept. Written silently, with a one-line summary.

### Field rules
- **Fields Rossum maintains: always taken from remote.** They never conflict, are never shown in conflicts, and are ignored when deciding whether L changed. Additions and removals made remotely are written into the local file.
  - `id`, `url`, `modified_at`, `modified_by`, `created_at`, `created_by`
  - Read-only back-references: `workspace.queues`, `organization.workspaces`, `queue.inbox`, `queue.rules`, `schema.queues`, `integration_credential.hooks` (exact list to be checked against the API, see section 17).
  - If such a field was edited locally, pull prints that the edit was overwritten. Push also warns on local edits to these fields and points to the side that owns the relation:

| Read-only side | Change it via |
|---|---|
| `workspace.queues` | `queue.workspace` (or move the queue folder) |
| `organization.workspaces` | `workspace.organization` |
| `queue.inbox` | `inbox.queues` |
| `queue.rules` | `rule.queues` |
| `schema.queues` | `queue.schema` |
| `integration_credential.hooks` | `hook.integration_credentials` |

- **Dicts:** merged key by key, recursively.
- **Unordered reference lists** (`DEPLOY_SORT_LIST_KEYS` in [consts.py](deployment_manager/utils/consts.py): `queue.hooks`, `queue.webhooks`, `hook.queues`, `hook.run_after`, `rule.queues`, …): set merge. The result is the base plus both sides' additions minus both sides' removals. Never a conflict, and written sorted by alias (section 7). This covers relations writable from both sides (`queue.hooks` ↔ `hook.queues`).
- **Lists of objects with stable keys** (schema nodes by `id`, enum `options` by `value`, rule `actions` by `id`):
  - elements are matched by key and merged field by field;
  - a reordering is taken from whichever side reordered;
  - it is a conflict only if both sides reordered differently.
- **Code fields** (`formula`, `config.code`, `trigger_condition`): line-level merge with `git merge-file`. Overlapping edits leave conflict markers in the code file.
- **Everything else** (scalars and other lists, compared as whole values):
  - only one side changed → take that side;
  - both changed to the same value → fine;
  - both changed to different values → conflict.

### Whole-object cases

| Local | Remote | Result |
|---|---|---|
| unchanged | changed | take remote silently |
| changed | unchanged | keep local, refresh the Rossum-maintained fields |
| changed | changed | field merge; if clean, write silently and print a one-line summary |
| deleted | unchanged | stay deleted (push will delete it remotely) |
| deleted | changed | prompt: restore it, or keep it deleted |
| changed | deleted remotely | prompt: drop it, or keep it as new (strip `id`, push creates it) |
| new (no `id`) | – | untouched |
| – | new remote object | write |

### Conflicts
- **Interactive:** prompt per field, showing local vs remote, with `l/r/ll/rr` (the doubled letter applies to all remaining fields). `--prefer=local|remote` skips the prompt.
- **Non-interactive, no `--prefer`:** leave the file and base untouched, list the conflicts, exit non-zero.
- After resolution the base is set to R. Its `modified_at` matches remote, so the next push passes the timestamp check and sends local edits on top of the remote ones.

## 9. Push

### What counts as a change
Push no longer asks git. It compares every object file in the selected subdirs with its base in `.prd_state`, the remote object as last synced (section 5). The comparison uses the decoded object (tokens resolved) and ignores the fields Rossum maintains and the order of unordered reference lists (section 7).

| Situation | Operation |
|---|---|
| File with `id`, differs from its base | UPDATE |
| File with `id`, equal to its base | nothing |
| File without `id` | CREATE; the response's `id`/`url` are written back into the same file, no rename |
| Base exists, but no file has that `id` any more | DELETE (subdir from the base's recorded `path`) |
| The `id` is now in a file at a different path | alias rename or folder move: no API call unless the content also changed |

Compared with git status this:
- **includes committed but unpushed changes:** edit, commit, then push still pushes them;
- **ignores changes that came from Rossum:** an uncommitted pull is not pushed back;
- **ignores formatting:** reordered keys or whitespace-only edits aren't changes;
- **works without a commit or stage step at all.**

`--indexed-only` stays as a filter: only objects whose files are staged in git are considered. `--all` still pushes every object, changed or not.

### Remote changed since the base
Before each UPDATE or DELETE, push fetches the remote object, as today's timestamp check already does.
- **Remote equal to the base:** push as planned.
- **Remote differs (someone changed it in Rossum, or a teammate pushed):** push first merges, with the same rules as the pull merge (section 8):
  - a clean merge → the merged object is pushed, and written to the local file;
  - the merged result equals the remote → nothing to push; the local file and base are refreshed;
  - a conflict → that object is asked per field (`l/r/ll/rr`), as in pull, or settled with `--prefer=local|remote`. Without a terminal it is skipped and reported.
- **`--force`** (as today) skips the merge and overwrites the remote with the local version.

A common case this covers: a teammate pushes and commits, and you git-pull their commit. Your files now differ from your older base. The merge finds local = remote, so nothing is pushed twice; only your base is refreshed.

### Missing base
For objects that have no `.prd_state` entry yet (fresh clone), the file's git HEAD version is the base, as in pull. Outside a git repository, the remote object is fetched and the file is treated as changed only if it differs.

### Other rules
- **Before detection:** fold code files (section 6), so `.py` edits are part of the JSON being compared.
- **Cycles** (queue↔hooks, queue↔schema, queue↔inbox): create first without the references that can't be resolved yet, then PATCH them in a second pass.
- **Validation before the plan:**
  - every token resolves (otherwise error with file and JSON path);
  - aliases are unique and match the format;
  - no code file contains conflict markers;
  - warn on local edits to read-only fields.
- **Write-back:** convert the API response back to tokens before writing it ([upload/directory.py:372](deployment_manager/commands/upload/directory.py:372) writes the raw response today), and update `.prd_state`.
- **Plan:** the push plan (`render_plan`) labels objects by alias. As today, CREATE or DELETE operations need confirmation (`--yes` skips it).

## 10. Deploy

### Running a deploy
```
prd2 deploy run deploy_files/dev-prod.yaml                                            # source_dir → target_dir
prd2 deploy run deploy_files/dev-prod.yaml --from prod-org/prod --to sandbox-org/dev  # the same file, the other way
prd2 deploy run --from sandbox-org/dev --to prod-org/prod                             # no deploy file: everything in the source dir
prd2 deploy run --from prod-org/prod --to sandbox-org/dev                             # also in the other direction
```
- **One deploy file connects two dirs and works in both directions.**
  - Without `--from` / `--to` it runs from `source_dir` to `target_dir`.
  - With the two swapped, it runs the other way.
  - Any other dirs are an error.
- There is no reverse file and no `deploy template reverse` command.
- **Terms used below:**
  - "source" and "destination" mean the two sides of one run;
  - `source_dir` / `target_dir` mean the keys in the deploy file;
  - "forward" is `source_dir → target_dir`, "reverse" is the other way.

### Deploy file
The same structure and the same wizard as today (`prd2 deploy template create` / `update`). What changes:

| Today | New |
|---|---|
| `id` + `name` per object | `alias` |
| `targets: [{id, attribute_override}, …]` | one counterpart, the same alias in the other dir, so `attribute_override` sits directly on the object |
| one direction per file; `deploy template reverse` / `reverse_mapping_after_deploy` create a flipped file | one file for both directions; both are dropped |
| override values written for the one target | override values reference variables defined per subdir in `prd_config.yaml`; each run uses the destination's values (below) |
| `token_owner_id`, `secrets_file` for the one target | taken from the destination's variables; the wizard no longer writes these keys |
| `deployed_org_id`, `last_deployed_at` in the file | in the deploy state, per destination dir |
| `unselected_hooks` with IDs | with aliases |
| `$prd_ref` keyword (unused) | tokens in override values, resolved against the destination |
| – | `id_refs` / `not_ids` pins for plain-number IDs (below) |
| missing `patch_target_org` means `true` | missing means `false`, matching what the wizard writes |

Everything else stays:
- the top-level keys `source_dir`, `target_dir`, `source_url`, `target_url`, `deploy_state_file`, `patch_target_org`. `token_owner_id` and `secrets_file` are still accepted, as overrides of the variables;
- the object lists (`workspaces`, `queues` with `schema`/`inbox`, `hooks`, `rules`, `labels`, `email_templates`, `engines`), plus the new `integration_credentials`;
- the object flags (`keep_hook_dependencies_without_equivalent`, `ignore_deploy_warnings`, `overwrite_ignored_fields`);
- `attribute_override`, including the regex form (`pattern/#/value`).

What the options that stay do (in both directions):

| Option | Level | Meaning |
|---|---|---|
| `patch_target_org` | file | Also deploy the source `organization.json` onto the destination org (`ui_settings`, `metadata`; the destination org keeps its name). Default `false`, also when the key is missing; today a missing key means `true` (`DeployOrchestrator.patch_target_org`). |
| `keep_hook_dependencies_without_equivalent` | queue | Same-org only (an error otherwise). A hook attached to the queue that isn't in the deploy and has no counterpart in the destination dir stays attached to the destination queue. This is for a hook shared by both subdirs. By default it is dropped from the destination queue's `hooks`. |
| `ignore_deploy_warnings` | queue | Silences that queue's pre-deploy warnings: an attached hook that isn't in the deploy, and, cross-org, `workflows`, an engine that isn't in the deploy, or a `dedicated_engine` / `generic_engine`. Set by hand. The warnings themselves are printed in the plan, never asked. |
| `overwrite_ignored_fields` | queue, schema | Deploy the fields that are normally kept from the destination: queue `automation_enabled`, `automation_level`, `default_score_threshold`, `settings.columns`, `settings.annotation_list_table`; schema `score_threshold`. |

### Variables: defined per environment in `prd_config.yaml`
Environment properties don't change between deploy files, so variables live once per subdir in `prd_config.yaml`, next to the directory they describe. Every deploy file, deploys without a file, and push all use them.

```yaml
# prd_config.yaml
directories:
  sandbox-org:
    org_id: '251437'
    api_base: https://acme-test.rossum.app/api/v1
    subdirectories:
      dev:
        regex: ''
        variables:
          token_owner_id: 12345
          secrets_file: deploy_secrets/dev.json
          name_suffix: " (DEV)"
          inbox_prefix: ap-cz-dev
          sap_endpoint: ${env.SAP_TEST_ENDPOINT}
  prod-org:
    org_id: '255590'
    api_base: https://acme.rossum.app/api/v1
    subdirectories:
      prod:
        regex: ''
        variables:
          token_owner_id: 98765
          secrets_file: deploy_secrets/prod.json
          name_suffix: ""
          inbox_prefix: ap-cz
          sap_endpoint: ${env.SAP_PROD_ENDPOINT}
```

```yaml
# deploy_files/dev-prod.yaml (excerpt)
queues:
  - alias: invoices-cz
    attribute_override:
      name: '${source.name_suffix}$/#/${vars.name_suffix}'   # dev → prod: "Invoices CZ (DEV)" → "Invoices CZ"; prod → dev: back
    inbox:
      attribute_override:
        email_prefix: ${vars.inbox_prefix}
hooks:
  - alias: export-to-sap
    attribute_override:
      settings.endpoint: ${vars.sap_endpoint}
```

- **Definition:** `variables` under a subdirectory in `prd_config.yaml`. A value can be any YAML value (string, number, boolean, list, object). `prd2 init` keeps the block when it rewrites the file; it already loads `prd_config.yaml` with a round-trip YAML parser.
- **Values for one deploy file only:** a deploy file may have its own `variables` block, keyed by dir in the same shape. Precedence: `--var` > the deploy file > `prd_config.yaml`.
- **References:**
  - `${vars.NAME}`: the **destination's** value. A dev → prod run takes it from `prod-org` / `prod`'s block, a prod → dev run from `sandbox-org` / `dev`'s.
  - `${source.NAME}`: the source's value. It is mainly for the pattern part of a regex override, as in `name` above: the override strips the source's suffix and adds the destination's, so the same override works in both directions.
  - `${env.NAME}`: an OS environment variable read at run time, for CI or for values that shouldn't be committed. It also works inside `variables` and in the secrets files.
- **Reserved names:** `token_owner_id` and `secrets_file` are read automatically from the destination's variables, so deploy files don't need those keys. A deploy file that sets them explicitly overrides the variables. See "Token owner" below and section 11 for secrets.
- **One override for both directions:** every `attribute_override` applies on every run. Values that differ per environment reference variables; a literal value (no variable) is sent to both destinations.
- **Where references work:**
  - override values, in both parts of a regex override (inserted values are regex-escaped);
  - top-level settings (`target_url`, …);
  - inside tokens (`prd://queues/${vars.fallback_queue}`).

  Not in aliases or keys.
- **Types:** a reference that is the whole value keeps the variable's type, so `enabled: ${vars.dup_rule_enabled}` sends `false`, not `"false"`. Inside a longer string it is inserted as text.
- **Only `${vars.…}`, `${source.…}` and `${env.…}` are replaced.** Any other `${…}`, such as NetSuite's `${window_start}` in hook settings, is left as it is. `$${vars.x}` writes a literal `${vars.x}`.
- **`--var NAME=value`** on `prd2 deploy run` overrides the destination's value for one run.
- **Errors:** a referenced variable that is missing for either dir of the run, or a missing environment variable, is an error before planning. The message names the variable and the dir.
- **Plan:** it shows resolved values, so changing a variable shows up as a change.
- **Writing back:** prd2 writes into `prd_config.yaml` only when it creates a token owner. `${…}` references in deploy files are never replaced by resolved values.
- **Without a deploy file** there are no overrides, but `token_owner_id` and `secrets_file` are still used.

### Token owner
On cross-org deploys, hooks need a `token_owner` in the destination org (today's `ensure_token_owner` / `get_token_owner_from_user`, which offers only admins).
- **Normally:** prd2 uses the destination's `token_owner_id` variable.
- **Missing, or pointing to a user that no longer exists:** the plan includes creating a technical user:
  ```
  PLAN: CREATE user  technical_token_owner_prd2_255590  (admin, password generated and not stored)
  ```
  - username `technical_token_owner_prd2_<org_id>`. Rossum usernames are unique across all organizations, so the org ID keeps it unique;
  - first and last name `prd2` / `technical token owner`;
  - admin group: `groups: ["<api_base>/groups/3"]`, since the admin group always has ID 3. This is the same role today's prompt requires;
  - `metadata: {"created_by": "prd2"}`;
  - a generated password sent in the create request, so no activation email goes out (see "Password" below). Hook tokens are issued by Rossum for the token owner, so nobody ever needs the password.
- **After "Apply":** prd2 creates the user first and saves its ID as `token_owner_id` in that subdir's `variables` in `prd_config.yaml`.
- **Leftover user:** if a user with that username already exists in the org (e.g. a run that failed before saving), prd2 reuses it. If the name is taken but the user isn't visible in this org, the create fails and prd2 reports it.
- **Password:**
  - generated with Python's `secrets` module, which reads the OS's cryptographically secure random source (`os.urandom`); never `random`;
  - 20 characters drawn from lowercase, uppercase, digits and `!#$%&*+-=?@^_`, with at least one of each class so it passes common password policies. That is about 124 bits of entropy;
  - held only in a local variable for the one create request. It never appears in the plan, terminal output, `.prd_logs`, error messages (`format_api_error` prints the response, never the request body), deploy state or `prd_config.yaml`;
  - if Rossum rejects it under its password policy, prd2 shows the API's validation message and saves nothing.
  ```python
  import secrets
  import string

  def generate_password(length: int = 20) -> str:
      classes = [string.ascii_lowercase, string.ascii_uppercase, string.digits, "!#$%&*+-=?@^_"]
      alphabet = "".join(classes)
      chars = [secrets.choice(c) for c in classes]
      chars += [secrets.choice(alphabet) for _ in range(length - len(chars))]
      secrets.SystemRandom().shuffle(chars)
      return "".join(chars)
  ```
- **No question:** the technical user is created automatically, interactive or not.
- **Same-org deploys** keep the hook's token owner, as today.

Wizard changes:
- **No multi-target question.**
- **Values per dir:**
  - for each override it asks for the value in both dirs (prefilled with each dir's current value), then writes the variable into both subdirs' `variables` in `prd_config.yaml` (or into the deploy file's own block, if you choose "only for this file") and a reference to it;
  - for the type-wide name-suffix question it writes the `${source.…}$/#/${vars.…}` form.
- **New alignment step:**
  - It lists selected objects that have no same-alias counterpart in the other dir.
  - Where the other dir has an object of the same type whose name matches (after the overrides, or with the environment marker stripped), it offers the `prd2 alias mv` that aligns them, in either dir.

### Deploy without a deploy file
- `prd2 deploy run --from <dir> --to <dir>` deploys **everything in the source dir**: every workspace, queue (with schema, inbox and email templates), hook, rule, label and engine (with engine fields). It works in either direction.
- **Objects are deployed as they are:** no attribute overrides, so names and other values are copied unchanged. Use a deploy file when the destination needs different values.
- **Objects that exist only in the destination** are never touched or deleted.
- **The organization object** is deployed only with `--include-organization`.
- **Secrets:** from the destination's `secrets_file` variable, or `--secrets-file <path>`. Without either, hooks keep whatever secrets the destination has; a credential that has to be created stops the deploy (section 11).
- **Token owner on cross-org deploys:** the destination's `token_owner_id` variable, `--token-owner <user id>`, or a created technical user (see "Token owner").
- **Deploy state:** one file per dir pair, shared by both directions. Dir names are sorted, e.g. `deploy_states/prod-org_prod__sandbox-org_dev.json`.
- **Ambiguous-ID answers** apply to that run only, since there is no file to store pins in. prd2 says so and suggests a deploy file to keep them. Without a terminal, ambiguous IDs stop the deploy.

### Matching objects between source and target
- An object's counterpart is the object with the **same alias in the target dir**. There is no other mapping.
- No counterpart → it is created in the target. The plan shows it under CREATE.
- **Possible duplicate:** when the target has an object of the same type and name under a different alias, the plan prints a warning naming both aliases and the `prd2 alias mv` that would align them.
- After each create, deploy writes the new object into the target dir under the source alias and updates that org's `.prd_state`. The post-deploy pull then keeps the alias.
- **Before planning, deploy pulls the target dir** (implicit merge, section 8), so its index includes objects created in Rossum since the last pull. It never asks anything: a local file that conflicts is left as it is and listed.

### Resolving references
- Deploy first runs the code-file check (section 6) on the source dir, so it deploys the working code files. Today `update_hook_code` and `update_formula_fields_code` do the same for hooks and formulas.
- Source objects are read in token form, then attribute overrides are applied.
- API payloads come from resolving tokens against the target: alias → target ID (target index, or created in this deploy).
- Existing policies stay:
  - missing in a list → dropped with a warning;
  - missing single reference → error;
  - same-org → falls back to the source object where `keep_dependency_without_equivalent` applies.
- References that exist only on the target stay (`persist_target_only_references`), in both directions.
- The ID-based `lookup_table` is replaced by alias resolution. Plain-number IDs are handled by the pass below, which replaces today's implicit ID override in `settings`/`metadata` (`replace_references_in_unstructured_attributes`).
- `--ld` (local deploy) becomes the default behaviour. Labels, email templates and `run_after` predecessors resolve from local files.

### Plain-number IDs in code, settings and metadata
Covers IDs that are not tokens:
- formulas, hook code and rule `trigger_condition`;
- values in `settings` and `metadata` that pull left raw.

**Finding candidates**
- Integers and digit strings in `settings`/`metadata`, and digit runs inside strings and code. They match only as whole numbers, not glued to letters or digits (the existing `_id_regex`).
- A candidate counts as an ID only if it exists in the source dir's alias index (the data `prd2 alias list` prints). Every other number is left alone.

**Determining the type**
IDs are unique per type, not across types (queue 22 and inbox 22 can both exist), so a lookup can return one or several (type, alias) entries.
1. One entry → that type.
2. Several → narrowed by context:
   - JSON key name (`queue_id`, `hook_ids`), via `_reference_type_from_key`;
   - URL context (`/queues/22`);
   - in code, the identifier before the number on the same line (`QUEUE_ID = 22`, `queue_id == 22`, `"hook_id": 22`), with the same key-name rules;
   - a pin in the deploy file (see below).
3. Still several → ambiguous.

**Mapping to the target**
- Source (type, alias) → same alias in the target index → target ID.
- A target created in this deploy gets its ID filled in during the second pass.

**Outcomes**

| Case | Result |
|---|---|
| Resolved | Replaced with the target ID |
| ID belongs to an object in the target subdir (same org) | Left unchanged; it already points to the target |
| No counterpart, same org | Left unchanged; the source object is valid in the same org |
| No counterpart, cross-org | Removed if it is an item in a `settings`/`metadata` list (as today); otherwise left unchanged. Shown in the plan diff as `prd://queues/invoices-at#id (not in target)` |
| Ambiguous | Asked before the deploy (below) |

**Ambiguous IDs: the only question besides Apply**
- Replacements are not listed separately; the plan diff already shows them as slugs (see "Plan display").
- Each ambiguous ID is asked once, before the plan is printed, so the plan reflects the answers:

```
hooks/mdh-vendors.py:2   TARGET = 77001
Which object is 77001?
  > inbox invoices-cz
    engine field ap-engine/vat-rate
    not a reference (never replace)
    skip this time (deploy unchanged)
```

- With a deploy file, the answer is saved there as a pin, so the same question doesn't come back. "Skip this time" saves nothing.
- Then the plan, then "Apply this deploy?".
- Without a terminal, prd2 stops before the plan. It lists each ambiguous ID with file:line and the candidate slugs, so they can be pinned in the deploy file.

**Pins (on a deploy-file object)**
- `id_refs: [inboxes/invoices-cz]`: an ambiguous number in that object which equals the ID of inbox `invoices-cz` in the source dir means that inbox.
  - The pin names the object rather than the number, so it works in both directions even though the number differs per environment.
- `not_ids: [1000]`: numbers in that object that only look like an ID (an amount, a threshold). They are never replaced.
- The prompt writes `id_refs` / `not_ids`, or you add them by hand.

### Plan display
- Both sides of the diff are in token form:
  - planned data, converted against the target index (which already knows the aliases of objects about to be created);
  - the live target, converted against the same index.
- Unordered reference lists are sorted by alias on both sides, so a different remote order never shows (section 7).
- Plain-number IDs that deploy replaces (code, `settings`, `metadata`) are shown as tokens on both sides too, e.g. `QUEUE_ID = prd://queues/invoices-cz#id`. This is display only; the payload contains the target ID.
- The plan never shows numeric IDs:
  - no dummy IDs like `<NEW COPY>[0](...)`; a reference to an object about to be created shows its normal token, and that object is listed under CREATE;
  - the first line names the direction, e.g. `PLAN prod-org/prod → sandbox-org/dev (deploy_files/dev-prod.yaml, reverse)`;
  - headers show `alias → destination-subdir/alias`, plus `(new)` for creates (`create_source_to_target_string`, [base_deploy_object.py:189](deployment_manager/commands/deploy/subcommands/run/deploy_objects/base_deploy_object.py:189));
  - the only numbers left are ones deploy doesn't treat as references (not an object ID, `not_ids`, or a skipped ambiguous ID).
- Warnings, rebase markers (↩) and conflict markers use the same labels.
- `--changes-only` is the default. `--show-unchanged` brings back the full plan. "Hidden N unchanged object(s)" stays.

```
PLAN sandbox-org/dev → prod-org/prod
PLAN: CREATE hook   export-to-sap  → prod/export-to-sap (new)
PLAN: UPDATE queue  invoices-cz    → prod/invoices-cz
    "hooks": [
      "prd://hooks/mdh-vendors",
+     "prd://hooks/export-to-sap"
    ],
PLAN: UPDATE hook   mdh-vendors    → prod/mdh-vendors
    config.code:
-   QUEUE_ID = prd://queues/invoices-old#id
+   QUEUE_ID = prd://queues/invoices-cz#id
```

### Send only what the plan shows
One function computes each object's change set. The plan renders it, and apply recomputes it against the live target and sends exactly that.

1. **Unit of change = top-level field.** Deploy uses PATCH (rossum_api `update`), and Rossum replaces each top-level field as a whole. If anything inside `settings`, `metadata`, `config`, `content`, `actions` or a list changed, the whole field is sent.
2. **Fields that belong together are sent together:** `queue.hooks` + `queue.webhooks`. The API uses `webhooks` when they disagree.
3. **Write-only fields are always sent:** hook `secrets` and integration credential secret keys (section 11) from the destination's secrets file (`secrets_file` variable, or `--secrets-file`). GET never returns them, so they can't show up as a change. The plan shows `secrets: N keys (values hidden, always sent)`.
4. **Computed against the live target right before each write.** Earlier writes in the same deploy change server-side relations (a hook's `queues` changes that queue's `hooks`). If the live change set contains a field the plan didn't show, that object is skipped and reported.
5. **Both sides of a relation are made consistent before planning.** For `queue.hooks` ↔ `hook.queues`, the side that differs from its `.prd_state` base is the edit; it is mirrored to the other side in memory. If both sides were edited in conflicting ways, stop with an error that names both files.
6. **Read-only back-references** are never sent or shown as changes; the change appears on the owning object. If the source has a back-reference whose owning object isn't selected, the plan warns, e.g. "rule `block-duplicate` attaches to `invoices-cz` in source but isn't in this deploy — the target queue won't get it". This extends `collect_unassigned_hooks_warning` ([queue_deploy_object.py:274](deployment_manager/commands/deploy/subcommands/run/deploy_objects/queue_deploy_object.py:274)).
7. **Creates send the full object.** References to objects created later go out in the second pass, which is just another change set computed against the live target.

Already safe without new rules:
- target-only references (see above);
- ignored AI fields (`automation_level`, `default_score_threshold`, `settings.columns`, … are copied from the target first, so they come out unchanged).

### Deploy state
- **One state file per deploy file** (`deploy_state_file`), shared by both directions. Without a deploy file, one per dir pair, also shared.
- **Keys:** entries are keyed by type and alias. `prd2 alias mv` rewrites them.
- **`ids` per dir**, e.g. `{"sandbox-org/dev": 1230128, "prod-org/prod": 1509387}`. If a dir's current ID differs from the recorded one, the object was recreated and its `last_applied` is discarded (treated as a first deploy).
- **`created_in`:** the dir where a deploy created the object. `deploy revert` deletes only objects created in the run's destination.
- **`deployed`:** per destination dir, the `org_id`, `last_deployed_at` and source dir of the last run there. This replaces the `deployed_org_id` / `last_deployed_at` keys in the deploy file.
- **`last_applied`:** the full planned object in token form, the same for both directions:
  - references and plain-number IDs as tokens (internal only, never written to user files);
  - overridden paths (every path in `attribute_override`) left out, since their value comes from the destination's variables;
  - Rossum-maintained fields, fields deploy never sends, `secrets` and `token_owner` left out.

  It is recorded even when no API call was needed. Otherwise the next run would see every unsent field as a change made only on the destination.
- **Comparison on every run**, field by field (shared merge function, section 12):
  - S = the run's source files;
  - T = the destination's live objects, converted to tokens with its index;
  - L = `last_applied`.

  Overridden paths are not compared, because each run sets them from the destination's variables. The plan still shows them when they differ from the live destination.
- **No direction dependence:** L is the same either way, so a forward run followed by a reverse run with no edits in between gives an empty plan.
- **Merge, field by field** (the same rules as the pull merge, section 8):
  - only the source changed → deployed;
  - only the destination changed → **rebased automatically**. The destination keeps its value, prd2 writes it into the source files (the JSON, and the code file for code fields), and the plan reports it as info;
  - both changed to the same value → nothing to do;
  - both changed differently → code fields and nested objects are merged first (line by line, key by key), so only truly overlapping edits conflict. A cleanly merged result is deployed and also written into the source. For a real conflict the source wins by default; `--prefer=target` keeps the destination's value and rebases it.
- **What a rebase writes:**
  - only the source dir's local files. Nothing is pushed to the source org. After the deploy, prd2 lists the rebased files ("3 fields rebased into sandbox-org/dev — review with git diff and push");
  - values in source form. References are tokens, so they are the same in both dirs; plain-number IDs in code are mapped from destination IDs back to source IDs;
  - not rebased: a value that references an object existing only in the destination, or a plain number that can't be mapped. The destination keeps it and the plan says why. For lists this is today's `persist_target_only_references` behaviour;
  - never rebased: overridden paths, Rossum-maintained fields, fields deploy never sends, and write-only secrets.
- **`--no-rebase`** (today's flag, new meaning): destination-only changes are overwritten with the source's values instead, e.g. to reset prod to dev.
- **After the run**, `last_applied` is the merged result, so the next run in either direction starts clean.
- **No questions:** today's rebase and conflict-resolution prompts are gone (see "Prompts").
- **Removed:** the `forward` / `reverse` entries in today's [state.py](deployment_manager/commands/deploy/subcommands/run/merge/state.py).

### Both directions

| Needed for the reverse direction | How |
|---|---|
| Running it | The same deploy file with `--from` / `--to` swapped; no reverse file, no reverse command |
| Counterparts | Same alias in the other dir, which works the same both ways |
| Aliases equal in both dirs | Created objects get the source alias; pull strips the environment marker when generating aliases; `prd2 alias mv` for the rest (the wizard and plan point to it) |
| References | Tokens, resolved against the run's destination |
| Plain-number IDs | Looked up in the run's source index, replaced from the destination's index |
| Pins | `id_refs` name objects, so they work both ways |
| Overrides | One `attribute_override` per object; its values reference variables, and each run uses the destination's set |
| Token owner, secrets | The destination's `token_owner_id` / `secrets_file` variables from `prd_config.yaml`, with or without a deploy file; a technical user is created if the token owner is missing |
| State | One file, shared by both directions |
| Destination index current | Destination dir pulled before planning |

### Prompts
A deploy asks at most two questions. Everything else is shown in the plan or decided by a default.

| Question | When |
|---|---|
| Ambiguous plain-number ID ("Which object is 77001?") | Only when a number matches objects of several types and nothing in its context tells which. It is asked once; the answer is saved as a pin in the deploy file. Without a deploy file it is asked on every run. |
| "Apply this deploy?" | Always, after the plan. `--auto-apply` / `-y` skips it. |

- **Credentials:** besides these two, prd2 asks for an API token only when one is missing or expired, as today.
- **Without a terminal:** a run that would need the ambiguity question stops before deploying anything, and Apply requires `-y`.
- **Variables are never confirmed.** Resolved values appear in the plan diff (as slugs where they are references), and a missing variable is an error before the plan.

What replaces today's other questions:

| Today | New |
|---|---|
| "Select target organization" (destination dir without `organization.json`) | `org_id` from `prd_config.yaml` |
| "Name for the deploy state file" | `deploy_states/<deploy file name>.json`, or the automatic file without a deploy file |
| "Do you want to disable warnings like this for this queue? (y/n/yy)" | Warnings are printed in the plan. `ignore_deploy_warnings: true` on a queue silences them |
| "Please choose target hook token owner" | The destination's `token_owner_id` variable, otherwise a created technical user |
| "Please select template for hook …" (private hooks) | Matched by template name in the destination org; no match is a plan error naming the hook |
| "Rebase it into source? (y/n/yy/nn)" and "Select overrides to delete" | Automatic: a field changed only in the destination since the last deploy stays there and is written into the source files, and the plan reports it (marker below). `--no-rebase` overwrites instead. Overrides never need deleting, because overridden paths aren't compared |
| Conflicts written into the source file + "Confirm that conflicts were resolved" | Merged automatically where the edits don't overlap (line by line for code, key by key for objects). Real conflicts are marked in the plan; the source wins by default, and `--prefer=target` keeps the destination's value |
| Pre-deploy refresh of the destination dir hitting a local conflict | No question: the conflicting local file is left as it is and listed. The plan compares against the live destination anyway |
| "There was an error during deploy. Do you want to pull the changes?" | The destination dir is always pulled afterwards. Objects the deploy created are written under their alias. Other new remote objects that would need a subdir choice are skipped (`skip_objects_without_subdir`) and reported |

Plan marker:
```
PLAN: UPDATE hook  mdh-vendors → prod/mdh-vendors
    config.code:                       ⇄ merged: dev's change (line 12) deployed, prod's change (line 40) kept
-   QUEUE_ID = prd://queues/invoices-old#id
+   QUEUE_ID = prd://queues/invoices-cz#id
    ↩ rebased into sandbox-org/dev (changed in prod since the last deploy):
      "events": + "annotation_content.updated"
      config.code: line 40
```

## 11. Integration credentials

[Integration credentials](https://rossum.app/api/docs/openapi/internal/api/integration-credential/) store third-party API credentials that any number of hooks in one organization share.
- **Endpoint:** `/api/v1/integration_credentials`, internal API, admin users only.
- **Types:** today only `coupa_sand_oauth2`, whose `secret` holds `client_id`, `client_secret`, `base_api_url` and an optional `scope`.
- **Use from hooks:** a hook references them in `hook.integration_credentials`, a list of URLs. Only credentials of the hook's own organization can be attached.

They become a first-class object type (`CustomResource.IntegrationCredential`, like labels) in pull, push and deploy.

### Local files
`<subdir>/integration_credentials/<alias>.json` holds the object as the API returns it, with references as tokens:

```jsonc
{
  "id": 42,
  "url": "https://acme-test.rossum.app/api/v1/integration_credentials/42",
  "name": "Coupa (DEV)",
  "type": "coupa_sand_oauth2",
  "organization": "prd://organization",
  "secret": {
    "client_id": "a1b2c3d4",
    "client_secret": "[redacted...]",               // the API never returns the real value
    "base_api_url": "https://acme-test.coupahost.com",
    "scope": "core.invoice.create core.common.read"
  },
  "hooks": ["prd://hooks/coupa-export"]               // read-only back-reference
}
```

- **Subdir:** the subdir of the first hook that uses the credential (the way rules follow their queues). Otherwise the regex or prompt, as for other objects.
- **Access:** pulled with an access check, like labels. With a non-admin token they are skipped with a notice.
- **Hook side:** hooks reference it as `"integration_credentials": ["prd://integration_credentials/coupa"]`.
- **Pull merge:** `[redacted...]` is the same on every side, so it never shows up as a change or a conflict. `hooks` is always taken from remote (read-only back-reference).

### Secret values
- **Write-only keys:** any `secret` key that GET returns as `[redacted...]`. That is `client_secret` today, and it covers future credential types without code changes.
- **Where they come from:** the environment's secrets file (the `secrets_file` variable, or `--secrets-file`). The file is now keyed by object type and alias, for hooks too:
  ```json
  {
    "hooks": {"export-to-sap": {"sap_password": "${env.SAP_PROD_PASSWORD}"}},
    "integration_credentials": {"coupa": {"client_secret": "${env.COUPA_PROD_SECRET}"}}
  }
  ```
- **The placeholder is never sent.** On create, every write-only key must come from the secrets file, otherwise prd2 stops before the plan and names the key. On update, a write-only key is sent only when the secrets file has it; otherwise it is left out and Rossum keeps the stored value (`PATCH` merges `secret` keys).

### Push
- **Create** (`integration_credentials/<alias>.json` without `id`): write-only keys are merged in from the subdir's secrets file.
- **Update:** changed fields are sent, plus write-only keys present in the secrets file.
- **Delete:** Rossum answers `409` while hooks still use the credential; push reports those hooks by alias.
- **`type` can't change after creation.** A changed `type` is a validation error ("create a new credential instead").

### Deploy
```yaml
integration_credentials:
  - alias: coupa
    attribute_override:
      name: '${source.name_suffix}$/#/${vars.name_suffix}'
      secret.base_api_url: ${vars.coupa_url}
      secret.client_id: ${vars.coupa_client_id}
```
- **Selection:** a deploy-file object like any other. A selected hook also brings the credentials it references, the way a selected rule brings its labels. An entry of its own is only needed for overrides.
- **Order:** deployed before hooks, so hooks can reference it. Its `hooks` list is never sent; the relation is set through `hook.integration_credentials`.
- **Cross-org:** Rossum accepts only credentials of the hook's own organization. A referenced credential without a counterpart in the destination is dropped from the hook's list with a warning (the general rule for missing list references), so cross-org it has to be deployed too.
- **Create:** the source's `secret` after overrides, plus write-only keys from the destination's secrets file. A missing key stops the deploy before the plan.
- **Update:** the same rules as push. A `type` that differs between source and destination is an error.
- **Plan:** a write-only key that is sent is shown as `secret.client_secret: (from secrets file, value hidden)`. Other secret keys diff normally.
- **Test after deploy:** prd2 calls `POST /integration_credentials/{id}/test` for every credential it created or changed, and prints `status`, `error` and `missing_scopes`. A failed test is a warning; nothing is rolled back. Push does the same.
- **Deploy state:** `last_applied` leaves out write-only keys.
- **Without a deploy file:** credentials are part of "everything", with secrets from the destination's `secrets_file`.

## 12. Shared merge function

`deep_three_way_merge` ([merge.py](deployment_manager/commands/deploy/subcommands/run/merge/merge.py)) is extended and used by both pull (local / remote / base) and deploy (source / target / last applied):
- the list of Rossum-maintained fields (always remote / always target);
- a real set merge for unordered lists (today it reports a conflict when both sides change a primitive list);
- keyed list merge (schema nodes, enum options, rule actions);
- line-level code merge via `git merge-file`;
- the existing per-key three-way logic, dict recursion and `prefer`.

## 13. Commands and project setup

- `prd2 init`: adds `**/.prd_state/` and `.DS_Store` (any level) to `.gitignore`, next to today's credentials, `deploy_secrets/` and `hook_sync_configs/` entries; code files stay versioned. Re-running `prd2 init .` adds missing lines to an existing project. The `modified_by` git filter stays. It keeps each subdirectory's `variables` block in `prd_config.yaml`.
- `prd2 alias mv <type>/<old> <new>`: moves the file or folder and rewrites tokens in the org dir, deploy files and deploy state.
- `prd2 alias list [<dir>]`: prints the alias / type / ID / name table.
- Guard: every command refuses directories that contain `*_[<id>]` paths, with a "new layout, re-init and pull" message.
- `prd2 pull --prefer=local|remote` for conflicts.
- `prd2 push [--prefer=local|remote] [--force] [--indexed-only] [--all] [--yes]`: changes are found against `.prd_state`, not git status; `--indexed-only` filters to staged files.
- `prd2 deploy run <deploy file> [--from <dir> --to <dir>] [--var NAME=value …] [--show-unchanged] [--prefer=source|target] [--no-rebase] [-y]`. `--from` / `--to` swapped runs the file in reverse. `--prefer` (real conflicts only) defaults to `source`.
- `prd2 deploy run --from <dir> --to <dir> [--include-organization] [--secrets-file <path>] [--token-owner <user id>] [--show-unchanged] [--prefer=source|target] [-y]`. Without the flags, secrets file and token owner come from the destination's variables.
- `prd2 deploy template create/update`: as today, minus multi-target, plus the alignment step.
- `prd2 deploy revert <deploy file> [--from <dir> --to <dir>]` / `prd2 deploy revert --from <dir> --to <dir>`: deletes only objects a deploy created in that run's destination (`created_in`).

## 14. Code removed

- `templatize_name_id`, `detemplatize_name_id`, `find_local_object_path_by_id` ([functions.py](deployment_manager/utils/functions.py))
- the `_[]` placeholder module [placeholder.py](deployment_manager/commands/upload/placeholder.py)
- `_rename_for_create`, `_substitute_parent_placeholders`, `_own_placeholder_segment` ([apply.py](deployment_manager/commands/upload/apply.py))
- `_parse_id_from_path` and the `_[]` branches in `classify` ([plan.py](deployment_manager/commands/upload/plan.py))
- `find_all_object_paths` (`**/*.json` glob) and its callers' assumptions, replaced by the layout walker (section 4); `delete_empty_folders` and `delete_empty_formula_dir`; the unused `DEPLOY_IGNORED_DIRS`
- git-status-based change detection in push:
  - `get_changed_file_paths` in `prepare_changed_objects`;
  - `mark_unstaged_objects_as_updated` (remote existence check for untracked files);
  - `dedup_changes_by_path`;
  - `merge_formula_changes` / `merge_hook_changes` (replaced by the code-file engine);
  - `evaluate_delete_dependencies` / `cascade_delete_ops`;
  - `_build_deleted_changed_object` with its path-based ID recovery ([upload/directory.py:205](deployment_manager/commands/upload/directory.py:205));
  - the D/?? rename pairing in `classify`.

  `load_deleted_object_from_git` stays only for the missing-base fallback.
- the `casefold` path comparison in [remover.py](deployment_manager/commands/download/remover.py)
- `non_versioned_object_attributes.json` and its path-walking helpers in [read_write.py](deployment_manager/common/read_write.py) and [download/helpers.py](deployment_manager/commands/download/helpers.py)
- the ID-based `lookup_table` and `replace_references_in_unstructured_attributes` in deploy, replaced by alias resolution and the plain-number ID pass
- multi-target support:
  - `targets` lists and `Target.index`;
  - index pairing in `_replace_reference_in_url`;
  - `create_dummy_id_from_parent`;
  - `get_multi_targets_from_user` / `add_multi_targets_to_object` ([template/helpers.py](deployment_manager/commands/deploy/subcommands/template/helpers.py));
  - the "multiple targets and a single source" conflict handling;
- `deploy template reverse` ([template/reverse.py](deployment_manager/commands/deploy/subcommands/template/reverse.py)) and [reverse_override.py](deployment_manager/commands/deploy/subcommands/run/reverse_override.py) (`reverse_source_target_in_yaml`, `reverse_attributes_v2`): one file now runs in both directions
- `deployed_org_id` / `last_deployed_at` in the deploy file (moved to deploy state)
- `reverse_mapping_after_deploy`: the post-deploy block in [run.py](deployment_manager/commands/deploy/subcommands/run/run.py) and `DEPLOY_KEY_REVERSE_MAPPING`
- `forward` / `reverse` entries in deploy state
- deploy-time questions replaced by plan output and defaults (see "Prompts" in section 10):
  - `prompt_rebase_field` and the override-deletion checkbox in `compare_target_objects`;
  - writing conflicts into source files plus "Confirm that conflicts were resolved";
  - `prompt_pending_warnings`;
  - `get_token_owner_from_user`;
  - `get_hook_template_from_user`;
  - the state-file name prompt in `ensure_deploy_state_file`;
  - the target-organization selection and the post-error pull question in [run.py](deployment_manager/commands/deploy/subcommands/run/run.py)

## 15. Phasing

Each phase can ship on its own.

1. **Alias paths, index and state.** Alias layout in pull/push, environment-marker stripping, the layout walker that ignores extra files and folders, the in-memory index, `.prd_state` (full base + `modified_at`), a JSON without `id` meaning create, the old-layout guard.
2. **Code files.** One engine for formulas, hook code and the new rule `trigger_condition` files; expand/fold/check; fold before git detection.
3. **Pull with implicit merge, push against the base.** The extended merge function; push change detection against `.prd_state` with merge-before-push; base updates in push.
4. **Reference tokens.** Structural fields first, then URLs and IDs in settings. Round-trip tests.
5. **Deploy.**
   - deploy file by alias (wizard, update), both directions with `--from` / `--to`;
   - `variables` per subdir in `prd_config.yaml` (plus optional deploy-file overrides) with `${vars.…}` / `${source.…}` / `${env.…}` / `--var`;
   - token owner from variables, technical user created when missing;
   - secrets file keyed by object type and alias;
   - deploy without a deploy file (`--from/--to`);
   - matching by alias, duplicate warning, pull of the target before planning;
   - references resolved against the target, plain-number IDs with the ambiguity prompt and `id_refs` / `not_ids`;
   - slug-only plan, `--changes-only` default with the change-set rules;
   - deploy state by alias, shared by both directions, with `created_in` and `deployed` per dir.
6. **Integration credentials.** Pull, push and deploy of the new type, write-only secret keys from the secrets file, hook references, the test call after create/change.
7. **Tooling.** `prd2 alias mv`, `prd2 alias list`, the alignment step in `deploy template create`.

## 16. Testing

- Property test: `decode(encode(x)) == x` on all fixture objects.
- Extra files and folders:
  - `.claude/`, `notes/`, `node_modules/`, `__pycache__/` and `*.md` files anywhere in the project don't change what pull, push or deploy do;
  - a JSON copy of an object with the same `id` is reported and left alone; pull doesn't delete it;
  - `hooks/payload.json` without hook fields is ignored and doesn't block push;
  - `hooks/test_mdh_vendors.py` and `formulas/helpers.py` are ignored with a notice;
  - an unparsable JSON at a known position skips only that object;
  - a queue removed in Rossum whose folder has extra files: prd2's files are deleted, the extra files and folder stay;
  - empty folders prd2 didn't empty are kept;
  - a moved queue folder carries its extra files along;
  - the git `modified_by` filter doesn't touch JSON files outside object positions;
  - `.DS_Store` files at any depth are git-ignored after `prd2 init`, and the layout walker never reads them.
- List ordering:
  - a remote that returns `queue.hooks` / `hook.queues` in a different order → no file change after pull, nothing pushed, no deploy plan diff, no conflict;
  - unordered lists in files are sorted by alias; raw (unknown) entries come after tokens;
  - `prd2 alias mv` re-sorts the affected lists;
  - `queue.rules`, `hook.events`, `rule.actions`, schema `content` and `settings` lists keep their order;
  - `rule.actions[].payload.labels` is sorted.
- Merge function unit tests: one per field rule and whole-object case; nested non-code fields (the section 8 example); set merge; keyed list merge with reorders; code line merge with and without overlap.
- Code files:
  - a `.py` edited by hand is folded into the JSON; JSON code edited by hand rewrites the `.py`;
  - both edited, with clean and overlapping changes;
  - a missing file is written from the JSON;
  - after a git merge both files agree;
  - conflict markers in a code file or JSON block push and deploy;
  - rule `trigger_condition` round-trips through `rules/<alias>.py`.
- Aliases: `Invoices CZ (DEV)` in `dev` and `Invoices CZ` in `prod` get the same alias; collisions; remote rename keeps the alias.
- Pull integration ([virtual_api.py](tests/integration/virtual_api.py)):
  - queue moved to another workspace;
  - local edit + remote edit to different fields merges silently;
  - read-only back-reference addition arrives locally.
- Push integration:
  - create queue + schema + inbox + hook in one push (cycles); rename via `git mv`; delete;
  - an edited and committed file is still pushed;
  - files changed by an uncommitted pull are not pushed;
  - key reordering or whitespace in a JSON is not a change;
  - remote changed since the base: a clean merge pushes the merged object; a conflict asks per field or follows `--prefer`; `--force` overwrites;
  - after git-pulling a teammate's pushed commit, push sends nothing and refreshes the bases;
  - a deleted file deletes the object, in the subdir from the base's `path`;
  - a folder move without content change makes no API call;
  - a missing base falls back to the git HEAD version;
  - `--indexed-only` limits the push to staged files.
- Deploy integration:
  - change-set payload equals the plan;
  - `settings` sent whole;
  - `hooks` + `webhooks` sent together;
  - secrets always sent;
  - one-sided `queue.hooks` edit mirrored;
  - a back-reference whose owning object isn't deployed is warned;
  - object without a same-alias counterpart is created under the source alias and written into the target dir;
  - same name under a different alias in the target → duplicate warning;
  - same-org fallback;
  - regex and literal overrides; tokens in override values;
  - a deploy file without `patch_target_org` doesn't deploy the organization.
- Both directions:
  - the same deploy file run with `--from` / `--to` swapped; other dirs are an error;
  - forward run followed by a reverse run with no edits → empty plan;
  - a change made only in prod deployed back to dev;
  - one override `${source.name_suffix}$/#/${vars.name_suffix}` gives the right name in both directions;
  - `${vars.…}` resolves to the destination's value on each run; a variable missing in one dir's block is an error;
  - a destination-only change stays in the destination, is written into the source files, and is reported in the plan; `--no-rebase` overwrites it instead;
  - non-overlapping code edits on both sides are merged, deployed and written into the source; overlapping ones conflict, and the source wins unless `--prefer=target`;
  - a destination-only change that references a destination-only object isn't rebased;
  - rebased plain-number IDs in code are mapped back to source IDs;
  - nothing is pushed to the source org by a rebase;
  - `token_owner_id` and `secrets_file` are resolved from the destination's variables;
  - recreated object (different ID) discards `last_applied`;
  - target dir pulled before planning picks up an object created in Rossum.
- Without a deploy file:
  - `--from dev --to prod` deploys every object in dev unchanged; objects only in prod are untouched;
  - `--from prod --to dev` works the same way back;
  - one automatic state file per dir pair, shared by both directions;
  - organization only with `--include-organization`; secrets file and token owner from the destination's variables, or the flags;
  - ambiguous IDs asked each run; without a terminal the deploy stops.
- Plain-number IDs in deploy:
  - replaced in hook code, formulas, rule conditions, `settings` and `metadata`;
  - an ID shared by two types is resolved by key name, by URL context and by the identifier in code;
  - unresolved → prompted before the plan, the answer saved as a pin and not asked again; "skip this time" deploys it unchanged;
  - replaced IDs appear in the plan diff as slugs; no numeric IDs anywhere in the plan;
  - no counterpart, same-org vs cross-org (removed from lists);
  - a target created in the same deploy gets its ID in the second pass.
- `deploy revert` deletes only objects created in the run's destination (`created_in`).
- Variables:
  - `${vars.…}` (destination) and `${source.…}` in override values, both parts of a regex override (escaped), top-level settings and tokens;
  - whole-value references keep their type, embedded ones become text;
  - variables from `prd_config.yaml`, overridden by the deploy file's block, overridden by `--var`;
  - `prd2 init` keeps the `variables` blocks;
  - `${env.…}` in variables, the deploy file and the secrets file;
  - other `${…}` (NetSuite templates) are left untouched; `$${…}` escapes;
  - an undefined variable or a missing environment variable is an error before planning;
  - the deploy file written back keeps the `${…}` references.
- Prompts:
  - a deploy with pinned IDs and an existing token owner asks only "Apply this deploy?"; with `-y` it asks nothing;
  - no rebase, conflict, warning, token-owner, template, state-file or organization questions in any run;
  - without a terminal, an ambiguous ID stops the run before anything is deployed.
- Token owner:
  - missing `token_owner_id` on a cross-org deploy → the plan shows the technical user; after "Apply" it is created with the admin role and a generated password, and its ID is saved in `prd_config.yaml`;
  - the password appears nowhere: output, log files, `prd_config.yaml`, deploy state;
  - an existing `technical_token_owner_prd2_<org_id>` user is reused; a name taken outside the org is reported;
  - the created user is in group 3 (admin);
  - generated passwords have 20 characters, contain every character class, and two runs never produce the same one;
  - a stale `token_owner_id` (user deleted) is treated as missing;
  - same-org deploys don't create a user.
- Integration credentials:
  - pull writes `integration_credentials/<alias>.json` with `client_secret` as `[redacted...]`, under the subdir of the first hook using it; skipped with a notice for non-admin tokens;
  - hook `integration_credentials` becomes tokens and resolves back to URLs;
  - push create takes `client_secret` from the secrets file and stops if it's missing; update leaves it out unless the secrets file has it; the placeholder is never sent;
  - push delete of a credential still used by hooks reports the hooks;
  - a changed `type` is a validation error;
  - deploy creates the credential before the hook, with overrides and the destination's secret, and the hook references the new credential;
  - cross-org deploy of a hook without its credential drops the reference with a warning;
  - the test call runs after create/change and a failure is reported as a warning;
  - `[redacted...]` never causes a pull or deploy diff or conflict.

## 17. To check against the Rossum API

- The exact list of read-only back-references. In particular, whether `schema.queues` is writable; if it is, it moves to the set-merge group.
- That PATCH replaces nested JSON fields (`settings`, `metadata`, `config`) as a whole.
- How a mismatch between `queue.hooks` and `queue.webhooks` behaves when only one of them is sent.
- Rule fields: `trigger_condition` is the only code field (per the business-rules reference). Action payloads hold message text and field IDs only.
- Technical users:
  - Rossum's password policy (length limit, allowed special characters) against the generator above.
- Integration credentials (internal API):
  - `PATCH` merges `secret` keys as documented;
  - whether credential types other than `coupa_sand_oauth2` are planned.
