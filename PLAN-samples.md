# Samples for [PLAN-aliases.md](PLAN-aliases.md)

These are illustrative files for one fictional project. JSON samples carry `//` comments to explain them; the real files have no comments.

## The project

| Subdir | Rossum org |
|---|---|
| `sandbox-org/dev` | `https://acme-test.rossum.app` |
| `prod-org/prod` | `https://acme.rossum.app` |

```
project/
  prd_config.yaml                          # directories, plus variables per subdir                → sample 1
  deploy_files/dev-prod.yaml               # created by `prd2 deploy template create`, used in both directions → sample 2
  deploy_states/dev-prod.json              # deploy three-way base, shared by both directions        → sample 6
  deploy_states/prod-org_prod__sandbox-org_dev.json   # automatic, for deploys without a file
  deploy_secrets/prod.json, dev.json       # git-ignored, keyed by object type and alias           → sample 1
  sandbox-org/
    .prd_state/                            # pull three-way base, git-ignored                         → sample 5
    dev/                                   # object files named by alias                              → sample 4
  prod-org/
    .prd_state/
    prod/
```

---

## 1. Environment variables: `prd_config.yaml`

Defined once per subdir and shared by every deploy file, by deploys without a file, and by push. `prd2 init` keeps these blocks.

```yaml
directories:
  sandbox-org:
    org_id: '251437'
    api_base: https://acme-test.rossum.app/api/v1
    subdirectories:
      dev:
        regex: ''
        variables:
          token_owner_id: 12345                  # saved by prd2 after it created the technical user
          secrets_file: deploy_secrets/dev.json
          name_suffix: " (DEV)"
          hook_suffix: " [DEV]"
          inbox_prefix: ap-cz-dev
          dataset: vendors_dev
          sap_endpoint: ${env.SAP_TEST_ENDPOINT}
          fallback_queue: ap-cz-archive
          dup_rule_enabled: true
          coupa_url: https://acme-test.coupahost.com
          coupa_client_id: dev-client-1
  prod-org:
    org_id: '255590'
    api_base: https://acme.rossum.app/api/v1
    subdirectories:
      prod:
        regex: ''
        variables:
          # token_owner_id missing → the next cross-org deploy into prod creates technical_token_owner_prd2_255590
          secrets_file: deploy_secrets/prod.json
          name_suffix: ""
          hook_suffix: ""
          inbox_prefix: ap-cz
          dataset: vendors
          sap_endpoint: ${env.SAP_PROD_ENDPOINT}
          fallback_queue: manual-review          # a queue that exists only in prod
          dup_rule_enabled: false                # the rule is switched off in prod only
          coupa_url: https://acme.coupahost.com
          coupa_client_id: prod-client-7
```

`deploy_secrets/prod.json` (git-ignored), keyed by object type and alias:
```json
{
  "hooks": {"export-to-sap": {"sap_password": "${env.SAP_PROD_PASSWORD}"}},
  "integration_credentials": {"coupa": {"client_secret": "${env.COUPA_PROD_SECRET}"}}
}
```

---

## 2. Deploy file: `deploy_files/dev-prod.yaml`

Same structure and the same wizard as today; only the references change. Values that differ per environment are variable references, so the same file runs in both directions. One queue entry, today and new:

```yaml
# today
queues:
  - id: 1230128
    name: Invoices CZ (DEV)
    overwrite_ignored_fields: false
    targets:
      - id: 1509387
        attribute_override:
          name: ' \(DEV\)/#/'
    schema:
      id: 1823001
      targets:
        - id: 2034001
          attribute_override: {}
    inbox:
      id: 77001
      targets:
        - id: 88001
          attribute_override:
            email_prefix: ap-cz
```

```yaml
# new
queues:
  - alias: invoices-cz             # the counterpart is invoices-cz in the other dir
    overwrite_ignored_fields: false
    attribute_override:
      name: '${source.name_suffix}$/#/${vars.name_suffix}'
    schema:
      attribute_override: {}
    inbox:
      attribute_override:
        email_prefix: ${vars.inbox_prefix}
```

The whole file. There are no `token_owner_id` or `secrets_file` keys: they come from the destination's variables.

```yaml
source_dir: sandbox-org/dev
target_dir: prod-org/prod
source_url: https://acme-test.rossum.app/api/v1
target_url: https://acme.rossum.app/api/v1
patch_target_org: false                    # also the default when missing
deploy_state_file: deploy_states/dev-prod.json

variables:                                 # optional: values only for this deploy file
  prod-org/prod:
    dataset: vendors_eu

workspaces:
  - alias: ap-cz

queues:
  - alias: invoices-cz
    keep_hook_dependencies_without_equivalent: false
    ignore_deploy_warnings: false
    overwrite_ignored_fields: false
    attribute_override:
      name: '${source.name_suffix}$/#/${vars.name_suffix}'
    schema:
      attribute_override: {}
    inbox:
      attribute_override:
        email_prefix: ${vars.inbox_prefix}

integration_credentials:
  - alias: coupa
    attribute_override:
      name: '${source.name_suffix}$/#/${vars.name_suffix}'
      secret.base_api_url: ${vars.coupa_url}
      secret.client_id: ${vars.coupa_client_id}
      # secret.client_secret comes from the destination's secrets file

hooks:
  - alias: mdh-vendors
    attribute_override:
      name: '${source.hook_suffix}$/#/${vars.hook_suffix}'
      settings.configurations[0].dataset: ${vars.dataset}
    id_refs: [inboxes/invoices-cz]         # saved by the ambiguity prompt for "TARGET = 77001" in the code
    not_ids: [1000]                        # "BATCH = 1000" equals label legacy's ID but isn't a reference
  - alias: export-to-sap
    attribute_override:
      name: '${source.hook_suffix}$/#/${vars.hook_suffix}'
      settings.endpoint: ${vars.sap_endpoint}
      settings.fallback_queue: prd://queues/${vars.fallback_queue}   # token, resolved in the destination
      settings.batch_size: 50                                          # literal: the same in both directions
  - alias: coupa-export                    # references integration credential coupa, which is deployed first

rules:
  - alias: block-duplicate
    attribute_override:
      enabled: ${vars.dup_rule_enabled}    # whole-value reference: sent as a boolean

labels:
  - alias: needs-review

email_templates:
  - alias: invoices-cz/rejection

engines:
  - alias: ap-engine

unselected_hooks:
  - webhook-2                              # attached to invoices-cz, deliberately not deployed
```

How the overrides resolve:

| Override | dev → prod | prod → dev |
|---|---|---|
| queue `name` | pattern ` \(DEV\)$` → `""`: `Invoices CZ (DEV)` → `Invoices CZ` | pattern `$` → ` (DEV)`: `Invoices CZ` → `Invoices CZ (DEV)` |
| inbox `email_prefix` | `ap-cz` | `ap-cz-dev` |
| hook `dataset` | `vendors_eu` (the deploy file's own value wins) | `vendors_dev` |
| hook `settings.endpoint` | `$SAP_PROD_ENDPOINT` | `$SAP_TEST_ENDPOINT` |
| hook `settings.fallback_queue` | `prd://queues/manual-review` → prod ID | `prd://queues/ap-cz-archive` → dev ID |
| hook `settings.batch_size` | `50` | `50` |
| rule `enabled` | `false` | `true` |
| credential `secret.client_id` / `base_api_url` | `prod-client-7` / prod Coupa | `dev-client-1` / test Coupa |
| credential `secret.client_secret` | `$COUPA_PROD_SECRET` via `deploy_secrets/prod.json` | from `deploy_secrets/dev.json` |
| token owner | prod's `token_owner_id`, or a created technical user | dev's `12345` |

What it shows:
- **References:** `alias` instead of `id` + `name`, and no `targets`. The counterpart is always the same alias in the other dir.
- **Variables:**
  - global in `prd_config.yaml`, picked by the destination of each run;
  - `${source.…}` lets one regex override strip the source's suffix and add the destination's;
  - a deploy file can override a value for itself (`dataset`), and `--var` overrides one for a single run;
  - `${env.…}` reads a value from the environment, in variables and in secrets files.
- **Override forms:**
  - regex with variables;
  - whole-value references, typed like the variable;
  - a token pointing to an object that exists only in one environment;
  - a literal that is the same in both directions.
- **Integration credential:**
  - overrides apply as for any other object;
  - the secret comes from the destination's secrets file;
  - the hook that uses it simply references it.
- **Pins:** `id_refs` names the object, so it works in both directions; `not_ids` lists literal numbers.

---

## 3. Commands and plan

```
prd2 deploy run deploy_files/dev-prod.yaml                                             # dev → prod
prd2 deploy run deploy_files/dev-prod.yaml --from prod-org/prod --to sandbox-org/dev   # prod → dev, same file
prd2 deploy run deploy_files/dev-prod.yaml --var dataset=vendors_v2                    # one variable changed for this run

prd2 deploy run --from sandbox-org/dev --to prod-org/prod     # no deploy file: everything in dev, as it is
prd2 deploy run --from prod-org/prod --to sandbox-org/dev     # everything in prod, back to dev

prd2 deploy revert deploy_files/dev-prod.yaml                 # deletes only objects dev → prod deploys created in prod
```

The first dev → prod run, while prod has no `token_owner_id` yet:

```
PLAN sandbox-org/dev → prod-org/prod (deploy_files/dev-prod.yaml)
PLAN: CREATE user                    technical_token_owner_prd2_255590 (admin, password generated and not stored)
PLAN: CREATE integration_credential  coupa → prod/coupa (new)
    secret.base_api_url: https://acme.coupahost.com
    secret.client_id: prod-client-7
    secret.client_secret: (from secrets file, value hidden)
PLAN: CREATE hook                    coupa-export → prod/coupa-export (new)
    "integration_credentials": ["prd://integration_credentials/coupa"]
    "token_owner": technical_token_owner_prd2_255590
...
Apply this deploy? [y/N]
```

After "Apply":
- prd2 saves the new user's ID as `token_owner_id` under `prod` in `prd_config.yaml`;
- it tests the new credential (`status: ok`, no missing scopes).

Without a deploy file:
- every workspace, queue (with schema, inbox and email templates), hook, rule, label, engine and integration credential in the source dir is deployed;
- there are no overrides, so `Invoices CZ (DEV)` arrives in prod under that name;
- secrets file and token owner come from the destination's variables, as above;
- objects that exist only in the destination are untouched;
- the state goes to `deploy_states/prod-org_prod__sandbox-org_dev.json`, shared by both directions;
- answers to ambiguous IDs apply to that run only.

---

## 4. Slugs: `prd2 alias list` and object files

There is no stored slug file. The slug is the file or folder name, and the ID and name are inside the object JSON. `prd2 alias list` prints the table:

```
$ prd2 alias list sandbox-org/dev
TYPE             ALIAS                   ID        NAME
workspaces       ap-cz                   521887    AP CZ
workspaces       ap-sk                   521890    AP SK
queues           invoices-cz             1230128   Invoices CZ (DEV)          ← environment marker "(DEV)" left out
queues           ap-cz-archive           1230200   Archive                    ← same name in two workspaces:
queues           ap-sk-archive           1230201   Archive                      parent alias prefixed
schemas          invoices-cz             1823001   Invoices CZ schema         ← schema and inbox reuse the queue alias
inboxes          invoices-cz             77001     Invoices CZ inbox
email_templates  invoices-cz/rejection   90012     Rejection                  ← nested: parent/child
hooks            mdh-vendors             521877    MDH vendors [DEV]
hooks            export-to-sap           521990    Export to SAP [DEV]
hooks            webhook                 521995    Webhook                    ← same name: -2 by ascending ID
hooks            webhook-2               522010    Webhook
hooks            coupa-export            522040    Coupa export [DEV]
rules            block-duplicate         8801      Block duplicate invoices
labels           needs-review            3301      Needs review
labels           legacy                  1000      Legacy
engines          ap-engine               4401      AP engine
engine_fields    ap-engine/invoice-id    99001     invoice_id
engine_fields    ap-engine/vat-rate      77001     vat_rate                   ← same ID as inbox invoices-cz
integration_credentials  coupa           42        Coupa (DEV)

$ prd2 alias list prod-org/prod
TYPE             ALIAS                   ID        NAME
queues           invoices-cz             1509387   Invoices CZ                ← same alias as in dev
queues           manual-review           1509500   Manual review              ← exists only in prod
hooks            mdh-vendors             611200    MDH vendors
...
```

Files on disk:

```
sandbox-org/dev/
  workspaces/ap-cz/workspace.json
  workspaces/ap-cz/queues/invoices-cz/queue.json
  workspaces/ap-cz/queues/invoices-cz/schema.json
  workspaces/ap-cz/queues/invoices-cz/inbox.json
  workspaces/ap-cz/queues/invoices-cz/formulas/amount_total.py
  workspaces/ap-cz/queues/invoices-cz/email_templates/rejection.json
  workspaces/ap-cz/queues/ap-cz-archive/...
  workspaces/ap-sk/queues/ap-sk-archive/...
  hooks/mdh-vendors.json
  hooks/mdh-vendors.py
  hooks/export-to-sap.json
  rules/block-duplicate.json
  rules/block-duplicate.py
  labels/needs-review.json
  engines/ap-engine/engine.json
  engines/ap-engine/engine_fields/invoice-id.json
  integration_credentials/coupa.json
```

### `workspaces/ap-cz/queues/invoices-cz/queue.json`
```jsonc
{
  "id": 1230128,                                                // own identity stays as Rossum returns it
  "url": "https://acme-test.rossum.app/api/v1/queues/1230128",
  "name": "Invoices CZ (DEV)",
  "workspace": "prd://workspaces/ap-cz",
  "schema": "prd://schemas/invoices-cz",
  "inbox": "prd://inboxes/invoices-cz",                         // read-only back-reference
  "hooks": ["prd://hooks/export-to-sap", "prd://hooks/mdh-vendors", "prd://hooks/webhook-2"],
  "webhooks": ["prd://hooks/export-to-sap", "prd://hooks/mdh-vendors", "prd://hooks/webhook-2"],
  "rules": ["prd://rules/block-duplicate"],                     // read-only back-reference
  "engine": "prd://engines/ap-engine",
  "automation_level": "confident",                              // never deployed (target keeps its own)
  "settings": {
    "columns": [],
    "export_target": "prd://queues/invoices-cz/export?format=xml"   // URL with a suffix
  },
  "modified_by": "https://acme-test.rossum.app/api/v1/users/12345",
  "created_at": "2026-03-02T08:10:11.000000Z"
}
```

### `hooks/mdh-vendors.json`
```jsonc
{
  "id": 521877,
  "url": "https://acme-test.rossum.app/api/v1/hooks/521877",
  "name": "MDH vendors [DEV]",
  "type": "function",
  "queues": ["prd://queues/ap-sk-archive", "prd://queues/invoices-cz"],          // unordered list: sorted by alias
  "run_after": ["prd://hooks/webhook"],
  "events": ["annotation_content.initialize"],
  "token_owner": "https://acme-test.rossum.app/api/v1/users/12345",   // users are never tokenized
  "settings": {
    "configurations": [{
      "dataset": "vendors_dev",
      "queue_ids": ["prd://queues/invoices-cz#id"],          // was 1230128 (int); key "queue_ids" tells the type
      "schema_id": "prd://schemas/invoices-cz#id-str",      // was "1823001" (string)
      "default_label": "prd://labels/needs-review"          // was a label URL
    }],
    "max_results": 1000                                     // left as is: the key doesn't name a type
  },
  "config": {
    "runtime": "python3.12",
    // you edit hooks/mdh-vendors.py (also versioned) and push folds it in here.
    // Code is never tokenized; deploy replaces these numbers in the payload only.
    "code": "QUEUE_ID = 1230128\nTARGET = 77001\nBATCH = 1000\n\ndef rossum_hook_request_handler(payload):\n    ..."
  },
  "modified_by": "https://acme-test.rossum.app/api/v1/users/12345"
}
```

How deploy treats the numbers in that code on a dev → prod run:

| Number | Lookup in the dev index | Result in the prod payload |
|---|---|---|
| `1230128` | queue `invoices-cz` only | prod ID of `invoices-cz` |
| `77001` | inbox `invoices-cz` **and** engine field `ap-engine/vat-rate` | ambiguous → `id_refs: [inboxes/invoices-cz]` → prod ID of that inbox |
| `1000` | label `legacy` | `not_ids: [1000]` → unchanged |

### `rules/block-duplicate.json`
```jsonc
{
  "id": 8801,
  "url": "https://acme-test.rossum.app/api/v1/rules/8801",
  "name": "Block duplicate invoices",
  "enabled": true,
  "organization": "prd://organization",
  "queues": ["prd://queues/invoices-cz"],
  "trigger_condition": "is_duplicate(field.document_id)",     // versioned copy; edit rules/block-duplicate.py
  "actions": [
    {"id": "dup-msg",   "type": "show_message",  "event": "validation",
     "payload": {"type": "error", "content": "Duplicate invoice", "schema_id": "document_id"}},
    {"id": "dup-label", "type": "add_label",     "event": "annotation_imported",
     "payload": {"labels": ["prd://labels/needs-review"]}},
    {"id": "dup-mail",  "type": "send_email",    "event": "annotation_imported",
     "payload": {"email_template": "prd://email_templates/invoices-cz/rejection", "attach_document": false}},
    {"id": "dup-move",  "type": "change_queue",  "event": "annotation_imported",
     "payload": {"queue": "prd://queues/ap-cz-archive", "reimport": false}}
  ]
}
```


### `integration_credentials/coupa.json`
```jsonc
{
  "id": 42,
  "url": "https://acme-test.rossum.app/api/v1/integration_credentials/42",
  "name": "Coupa (DEV)",
  "type": "coupa_sand_oauth2",                    // can't change after creation
  "organization": "prd://organization",
  "secret": {
    "client_id": "dev-client-1",
    "client_secret": "[redacted...]",              // never returned by the API; comes from the secrets file
    "base_api_url": "https://acme-test.coupahost.com",
    "scope": "core.invoice.create core.common.read"
  },
  "hooks": ["prd://hooks/coupa-export"]              // read-only back-reference
}
```

`hooks/coupa-export.json` references it:
```jsonc
{
  "id": 522040,
  "name": "Coupa export [DEV]",
  "queues": ["prd://queues/invoices-cz"],
  "integration_credentials": ["prd://integration_credentials/coupa"],
  "...": "..."
}
```

---

## 5. Pull three-way base: `sandbox-org/.prd_state/hooks/521877.json`

Git-ignored. It holds the complete remote object exactly as this clone last synced it (raw API form), plus the text last written to each code file.

```jsonc
{
  "base": {
    "id": 521877,
    "url": "https://acme-test.rossum.app/api/v1/hooks/521877",
    "name": "MDH vendors [DEV]",
    "type": "function",
    "queues": ["https://acme-test.rossum.app/api/v1/queues/1230128"],
    "run_after": ["https://acme-test.rossum.app/api/v1/hooks/521995"],
    "events": ["annotation_content.initialize"],
    "settings": {
      "configurations": [{
        "dataset": "vendors_dev",
        "queue_ids": [1230128],
        "schema_id": "1823001",
        "default_label": "https://acme-test.rossum.app/api/v1/labels/3301"
      }],
      "max_results": 1000
    },
    "config": {"runtime": "python3.12", "code": "QUEUE_ID = 1230128\nTARGET = 77001\nBATCH = 1000\n..."},
    "modified_at": "2026-10-30T09:12:44.000000Z",     // used by push's timestamp check
    "modified_by": "https://acme-test.rossum.app/api/v1/users/12345"
  },
  "code_files": {
    "hooks/mdh-vendors.py": "QUEUE_ID = 1230128\nTARGET = 77001\nBATCH = 1000\n..."
  }
}
```

A pull after edits on both sides:

| Field | Base | Local (not pushed) | Remote (edited in Rossum) | Merged | Why |
|---|---|---|---|---|---|
| `name` | `MDH vendors [DEV]` | same | `MDH vendors v2 [DEV]` | remote | only remote changed; the alias stays `mdh-vendors` |
| `events` | `[initialize]` | `[initialize, updated]` | same as base | local | only local changed |
| `queues` | `[invoices-cz]` | same | `+ ap-sk-archive` | `[ap-sk-archive, invoices-cz]` | set merge, written sorted by alias |
| `settings.configurations[0].dataset` | `vendors_dev` | same | `vendors_dev2` | remote | nested key, only remote changed |
| `config.code` | v1 | `.py` edited (folded first) | same as base | local | only local changed |
| `modified_at`, `modified_by` | old | – | new | remote | maintained by Rossum |

No conflict, so the file is written without a prompt and `base` becomes the remote version. The next push passes the timestamp check and sends `events` and the code on top of the remote changes.

Fields changed on both sides to different values would be asked per field (`l/r/ll/rr`) or settled with `--prefer`.

---

## 6. Deploy three-way base: `deploy_states/dev-prod.json`

Committed, one per deploy file, shared by both directions. `last_applied` is the same whichever way the last run went:
- references and plain-number IDs are tokens;
- every path in `attribute_override` is left out, because each run sets it from the destination's variables;
- Rossum-maintained fields, fields deploy never sends, secrets and `token_owner` are left out.

```jsonc
{
  "deployed": {
    "prod-org/prod":   {"org_id": 255590, "last_deployed_at": "2026-10-31T14:02:10Z", "from": "sandbox-org/dev"},
    "sandbox-org/dev": {"org_id": 251437, "last_deployed_at": "2026-11-02T09:30:00Z", "from": "prod-org/prod"}
  },
  "hooks": {
    "mdh-vendors": {
      "ids": {"sandbox-org/dev": 521877, "prod-org/prod": 611200},   // a changed ID means the object was recreated
      "last_applied": {
        // name and settings.configurations[0].dataset are left out: overridden, so environment-specific
        "type": "function",
        "queues": ["prd://queues/invoices-cz"],        // ap-sk-archive isn't in this deploy → dropped (with a warning)
        "run_after": ["prd://hooks/webhook"],
        "events": ["annotation_content.initialize"],
        "settings": {
          "configurations": [{
            "queue_ids": ["prd://queues/invoices-cz#id"],
            "schema_id": "prd://schemas/invoices-cz#id-str",
            "default_label": "prd://labels/needs-review"
          }],
          "max_results": 1000
        },
        "config": {
          "runtime": "python3.12",
          "code": "QUEUE_ID = prd://queues/invoices-cz#id\nTARGET = prd://inboxes/invoices-cz#id\nBATCH = 1000\n..."
        }
      }
    },
    "export-to-sap": {
      "ids": {"sandbox-org/dev": 521990, "prod-org/prod": 611350},
      "created_in": "prod-org/prod",                  // a dev → prod deploy created it; `deploy revert` may delete it
      "last_applied": {"type": "function", "queues": ["prd://queues/invoices-cz"], "...": "..."}
    }
  },
  "queues": {
    "invoices-cz": {
      "ids": {"sandbox-org/dev": 1230128, "prod-org/prod": 1509387},
      "last_applied": {
        "workspace": "prd://workspaces/ap-cz",
        "schema": "prd://schemas/invoices-cz",
        "hooks": ["prd://hooks/export-to-sap", "prd://hooks/mdh-vendors"],     // webhook-2 is in unselected_hooks
        "webhooks": ["prd://hooks/export-to-sap", "prd://hooks/mdh-vendors"],
        "engine": "prd://engines/ap-engine",
        "settings": {"export_target": "prd://queues/invoices-cz/export?format=xml"}
        // not here: name (overridden), inbox and rules (read-only), automation_level and settings.columns (never deployed)
      }
    }
  },
  "inboxes": {
    "invoices-cz": {
      "ids": {"sandbox-org/dev": 77001, "prod-org/prod": 88001},
      "last_applied": {"name": "Invoices CZ inbox", "queues": ["prd://queues/invoices-cz"]}
      // email_prefix: overridden; email: never deployed
    }
  },
  "integration_credentials": {
    "coupa": {
      "ids": {"sandbox-org/dev": 42, "prod-org/prod": 57},
      "created_in": "prod-org/prod",
      "last_applied": {"type": "coupa_sand_oauth2", "secret": {"scope": "core.invoice.create core.common.read"}}
      // name, secret.client_id and secret.base_api_url: overridden; secret.client_secret: write-only, never stored
    }
  },
  "rules": {
    "block-duplicate": {
      "ids": {"sandbox-org/dev": 8801, "prod-org/prod": 9902},
      "last_applied": {"name": "Block duplicate invoices", "queues": ["prd://queues/invoices-cz"], "trigger_condition": "is_duplicate(field.document_id)", "actions": ["..."]}
      // enabled: overridden (${vars.dup_rule_enabled})
    }
  }
}
```

How the same state serves both directions:
- **S** = the run's source files;
- **T** = the destination's live objects, converted to tokens;
- **L** = `last_applied`.

| Run | Situation | Outcome |
|---|---|---|
| dev → prod | A line added to `hooks/mdh-vendors.py` in dev (S ≠ L, T = L) | Deployed. The payload has prod IDs; the plan shows `prd://queues/invoices-cz#id`. |
| dev → prod | `annotation_content.updated` added to `events` in prod only (T ≠ L, S = L) | Rebased: prod keeps it, dev's `hooks/mdh-vendors.json` gets it, and the plan reports it. `--no-rebase` would overwrite it |
| dev → prod | Dev changed line 12 of `mdh-vendors.py`, prod changed line 40 | Merged: dev's change is deployed, prod's change stays and is written into dev's `.py` and JSON |
| dev → prod | Dev queue renamed to `Invoices CZ & SK (DEV)` | `name` is overridden: the regex makes it `Invoices CZ & SK` in prod |
| prod → dev, right after | Nothing changed | Empty plan; L is the same in both directions |
| prod → dev | A fix to `block-duplicate.py` made in prod (S ≠ L) | Deployed to dev |
| prod → dev | `email_prefix` differs (`ap-cz` vs `ap-cz-dev`) | Not compared; the override sends dev's value `ap-cz-dev`, which dev already has → no change |
| prod → dev | Prod queue renamed to `Invoices CZ & SK` | The same regex override, with dev's variables, makes it `Invoices CZ & SK (DEV)` in dev |
