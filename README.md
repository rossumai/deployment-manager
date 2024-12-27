# Deployment manager

This CLI tool aims to help users configure and manage projects on the Rossum platform. It allows you to track changes made inside Rossum, apply locally made changes in Rossum, and deploy the entire project to different organisations.

## Installation guide

1. You can use this one-liner to download the installation script and let it execute the steps automatically:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/rossumai/deployment-manager/main/install.sh)"
```
2. You can also do these steps manually:
```
git clone https://github.com/rossumai/deployment-manager.git
cd deployment-manager

brew install pipx

pipx ensurepath
pipx install .
```

Make sure to restart the terminal before using the command.

You can then start using the tool in any directory by running:
```
prd2
```

### Updating to a new version
This command will automatically pull the latest vesion from the GIT repo and install it locally:
```
prd2 update
```
You can also specify a branch to install:
```
prd2 update --branch=some-cool-early-feature
```

### Migration from v1

Please note that the new version of the tool (`prd2`) is not backwards-compatible. If you would like to use it for an existing project, we recommend downloading the whole project again via the new version and going from there. You can keep using the old version under `prd`.

Here are a few specific tips when migrating projects manually:
- You need to make sure to pull the objects into the right directories that you create for them (e.g., `org/test` and `org/prod`).
- If you had an existing mapping, you would then need to manually assing the target IDs after generating a deploy file via `prd2 deploy template`.
- **The old version of the tool is still available under the name `prd`**, You can use it for older projects where the migration would not be worth it.

## Quick Start Guide

> ℹ️ Whenever in doubt, you can run `prd2 --help` to get guidance and overview of all parameters and options. `--help` is also available for all subcommands (e.g., `prd2 pull --help`).

### 1. Create a new project
Follow the CLI instructions to initialize a new project. **You must setup at least one org-level directory and one subdir**:
```
prd2 init <NAME-OF-PROJECT>
```
For each subdir, you can specify a regex for the name of objects. Once you `pull` objects from Rossum, these objects will automatically be placed into the respective subdir.
> This only applies if the object does not have a local copy in a different subdir though!

You can rerun this command later to add new directories into the project.

> ℹ️ Note: all dirs and subdirs need to be added inside the configuration file (`prd_config.yaml`) to work properly with PRD commands.

This command creates the specified directories and puts the provided credentials into them. 

This command also initializes an empty GIT repository.

### 2. Get the objects from Rossum to the created repo
Reference one of your (sub)dirs and download (`pull`) changes from Rossum.
```
cd <NAME-OF-PROJECT>
prd2 pull <DIR-NAME>
```
You can reference the whole org-level dir (e.g., `sandbox-org`) or subdir(s) (e.g., `sandbox-org/dev sandbox-org/uat`) or any combination thereof. Org-level dirs are expanded into its subdirs.

Before downloading, the command checks if the local objects have any uncommitted changes and warns you if there are any (so as not to override them).

### 3. Get local changes back into Rossum
After you make changes in the project, run:
```
prd2 push <DIR-NAME>
```
The `<DIR-NAME>` should correspond to the directory where you made the changes. You can specify more.

Before uploading the changes, This command will check if the object `last_modified` timestamp on the remote is the same as the one for the local object. If not, the changes are not pushed unless you override this behaviour via the `--force` flag.

> ℹ️ Note: you currently cannot delete objects using `prd2 push`. But you can do so explicitly via `prd2 purge`.

### 4. Copy (deploy) configuration elsewhere
If you want to create a copy of your configuration (typically move a test setup into production), you first need to create a deploy file specifying what should be copied (deployed):
```
prd2 deploy template
```

This command allows you to specify attribute override for all objects of a certain type. This is particularly useful for changing suffixes (e.g., `DEV` -> `PROD`).

Once you go through the CLI guide, you can also make other changes manually in the deploy file (e.g., attribute_override of specific objects). Any object specified in the deploy file with an empty `targets` will have a new copy created. If there is an ID specified, this command will instead update the object with that ID.

Then you can go ahead and **run the deploy**:
```
prd2 deploy run <DEPLOY-FILE-PATH>
```
You will first see a plan of the deploy (what will be deployed, what are the changes) and then you are asked for confirmation that those changes should be applied.

Once the `deploy` is finished, you will get a new file with a `_deployed` suffix. If you created new objects, their IDs will be on the right hand side. This file is created in case you wanted to keep using the original deploy file as a template. For future deploys, you should use the `_deployed` file since it will update the right objects, not create new ones again.

You can **update a previously existing deploy file** via:
```
prd2 deploy template -f <PATH> --interactive
```
Without the `--interactive` flag, the update would fix names based on object IDs or add hooks assigned to the already specified queues, but it would not add/remove any of the specified objects in the deploy file.

You can leave comments in the YAML, they will get preserved (bar a few exceptions).

## User Guide

### Directory structure
A single PRD project corresponds to a single GIT repository. Inside the project, there can be any number of directories, each corresponding to a single Rossum organization.

These `org-level` directories are specified in `prd_config.yaml`. Example:
```YAML
directories:
  sandbox-org:
    org_id: '251437'
    api_base: https://rdttest.rossum.app/api/v1
    subdirectories:
      dev:
        regex: ''
      uat:
        regex: ''
  prod-org:
    org_id: '255590'
    api_base: https://rdttest.rossum.app/api/v1
    subdirectories:
      prod:
        regex: ''

```
The config specifies the URLs and org IDs for each org-level directory. There are also so called subdirectories.

Inside an org-level directory, there is always at least a single subdirectory. This subdirectory corresponds to a grouping of Rossum objects (e.g., "DEV", "UAT", etc.).

If the project has dedicated organizations for each part of the implementation lifecycle (TEST+PROD, DEV+TEST+PROD, etc.), then the subdirectory is usually only for compatibility reasons. But if there is a single organization for the whole project ("same-org"), subdirectories allow the segregation of testing and production objects.

The directories and subdirectories are relevant in 2 ways:
1. They are a part of the path to specific objects.
2. They are used in PRD commands to specify which parts of the project are to be used.

Commands like `pull` and `push` can take any combination of dirs and subdirs. Dirs are automatically expanded to include all of its subdirs.

Inside the subdirectories, there is always one folder for `workspaces` and another for `hooks`. Under each workspace, there is a folder for `queues`. Each queue subfolder then has the configuration for the queue, its schema, and inbox. In this respect, PRD is opinionated and expects each queue to have its own schema. Inbox is optional.

A full example of a project directory structure with 2 organizations and 2 subdirectories in the `sandbox-org` can be found below:

```JSON
├── prd_config.yaml
├── prod-org
│   ├── credentials.yaml
│   ├── organization.json
│   └── prod
│       ├── hooks
│       │   └── Master Data Hub 1 - DEV_[521877].json
│       └── workspaces
│           └── AP_[572556]
│               ├── queues
│               │   └── Invoices_[1509387]
│               │       ├── formulas
│               │       │   └── some_formula.py
│               │       ├── inbox.json
│               │       ├── queue.json
│               │       └── schema.json
│               └── workspace.json
└── sandbox-org
    ├── credentials.yaml
    ├── dev
    │   └── workspaces
    │       └── AP_[521887]
    │           ├── queues
    │           │   └── Invoices_[1230128]
    │           │       ├── inbox.json
    │           │       ├── queue.json
    │           │       └── schema.json
    │           └── workspace.json
    ├── organization.json
    └── uat
        └── workspaces
            └── AP_[563305]
                ├── queues
                │   └── Invoices_[1462491]
                │       ├── inbox.json
                │       ├── queue.json
                │       └── schema.json
                └── workspace.json
```


### Interactions with GIT

PRD has 2 mechanisms to keep track of changes when comparing local and remote Rossum objects:
1. Checking the `modified_at` timestamp
2. Checking changes tracked by GIT

#### Checking timestamps

##### Push

`push` command by default analyzes the `modified_at` attribute on each API object in the remote and compares it to the one in the local JSON object. If the `modifed_at` timestamp in remote is different from the local one, `push` will skip this object to avoid overwriting changes to the object made on the remote, but not existing locally.

You can override this and push such local objects with `--force` or `-f`. 

##### Pull

`pull` command also utilizes the `modified_at` timestamp to compare local and remote objects. In this case though, it does so to only download objects that really did change in the remote. `pull` assumes this is the case when the timestamps are not equal.

You can override this and pull all objects with `--all` or `-a`.

#### Checking GIT changes

##### Push

`push` uses GIT to know which objects were changed locally and should be pushed to remote. If you add `--all` or `-a`, PRD pushes all your local objects, irrespective if they were changed or not.

##### Pull

`pull` uses GIT to prevent overwriting local uncommitted changes. If the timestamps are not equal (see above), but the object is tracked in GIT as modified, PRD will ask the user to confirm overwriting the object. 

PRD does not create any commits for the user, but it expects the user to commit in the following situations:
- Running `prd2 pull` and having a synced up version of local-remote
- Running `prd2 push` and having a "working solution" in remote

> **Rule of thumb**: The user should commit local changes after a series of the same PRD command, before a different command is use. Example:
1. `push`ing changes made to an extension ->
2.  debugging in the Rossum UI and seeing that one more change is needed ->
3. `push`ing again -> commiting ->
4. `pull`ing changes a day later made by someone else in the UI


### Working with credentials

PRD commands almost always need credentials (Rossum API URL + token / password & username) to work properly. PRD tries to find and use credentials in the following order:
1. Use credentials from the org-level directory in `credentials.yaml` file.
2. If the credentials are invalid (e.g., expired token), ask the user for a valid one and save it for future use.
3. If there are no credentials in the file, ask the user for a token without saving it.

Some commands (e.g., `purge`) ask you for credentials every time because they can be used with any Rossum organization, not just the ones you have pulled locally.


## Full(er) Command Reference

### Pull

When saving remote objects locally, `pull` tries to guess into what org-level dir and subdir to place the object . The org-level dir is clear based on the provided credentials. The subdir is evaluated/guessed in the following order:
1. If there is a single subdir configured in the org-level dir, use that one.
2. If a subdir has an object with the same ID, use that one.
3. If configured, try matching the subdir's regex against the remote object's name.
4. If there are any objects without a subdir left, ask the user if they want to manually assign them, otherwise do not save such objects.

`-c` or `-cm` parameter can be added to automatically commit all changes with default or custom (`-m` parameter) commit message.

The following object attributes are ignored - that means they are neither pulled nor pushed:
  - Queue: ["counts", "users"]
  - Hook: ["status"]

### Push

If you have many local changes and want to push only some of them to remote, you can run `git add <selected_paths>` and then use `push` with `-io` or `--indexed-only` parameter which will only register changes added to GIT index.

`-c` or `-cm` parameter can be added to automatically commit all changes with default or custom (`-m` parameter) commit message.

### Deploy

**For cross-org deploys, some parts of the Rossum configuration are ignored because they are not writable via the API** (e.g., approval workflows, engines, etc.).

IDs of dependencies (e.g., `queue.hooks`) are automatically replaced when deploying. PRD does a lookup of each source dependency to find its target equivalent.

PRD handles the following edge cases:
1. For a single ID, if there is no target equivalent, the dependency is kept the same (e.g., `queue.schema`) and a warning is shown.
2. For a list of IDs, if one of the dependencies has no target equivalent, it is skipped (the rest of the list of IDs is applied). This can be overriden for queues and their hooks (see the deploy file reference below).
3. For both cases, if there are multiple target equivalents, their count is compared to the count of "siblings" of the current object:
    - If this count is equal (e.g., releasing 2 `queues`, each with its own version of `hooks), each sibiling object gets its own target equivalent (based on the index)
    - If the count is not equal, all siblings get the first target equivalent as their dependency
4. For queues, any dependencies that exist in target, but not in source (e.g., a production-only "dangling" hook) are kept in the list of dependencies.

#### Multiple targets

A single object can be deployed to multiple target objects by specifying an array of `targets`. The smallest viable configuration example is the following: 
```YAML
workspaces:
  - id: 521887
    name: WS1 DEV
    targets:
      - id:
      - id:

```
Attribute override is added for each target separately:
```YAML
workspaces:
  - id: 521887
    name: WS1 DEV
    targets:
      - id:
        attribute_override:
          name: WS1 UAT
      - id:
        attribute_override:
          name: WS1 PROD

```

#### Pull from production into dev

In cases where the user has a configuration in Rossum production and wants to replicate it for development purposes and then deploy changes back into production, the user can use `reverse_mapping_after_deploy: true` in the deploy file.

This flag will replicate `source_org` into `target_org` and then reverse the left and right hand sides for each object. The resulting deploy file thus has `source_org` and `target_org` reversed and is ready for a dev->prod release.

## Deploy File Reference

You can leave comments in the deploy file and they will be preserved (in almost all cases) even after running PRD commands (this is different from PRD v1).

> ℹ️ Note: Unlike in PRD v1, there is no `ignore` option for objects. If you do not want to deploy something, just remove it from the deploy file. However, this does not work for objects like schemas since a queue always needs one.

For queues, there are optional flags:

#### `queue.keep_hook_dependencies_without_equivalent`

By default, any hooks that did not have have a target equivalent found (the hook was not part of the deploy) will be removed from the list of the deployed (target) queue. If this flag is `true`, the specific queue will retain hook dependencies from source. **This only makes sense for same-org releasing**.

#### `queue.ignore_deploy_warnings`

If `true`, `deploy` does not display the warning that the queue has a workflow or dedicated engine defined. Note that this warning is shown only for cros-org releases.

- Difference between:

### Attribute override

To override attributes in target objects, the user can specify key:value pairs. The keys are JMESPath queries. The values replace whatever is found with these queries during the `deploy` call.

#### Using regex 

Attribute override can also replace only a part of the value by using a regex:
```YAML
workspaces:
  - id: 538437
    name: Invoices US
    targets:
      - id:
        attribute_override:
          name: \bUS\b/#/EU
```
There is a `/#/` separator of the regex on the left and the static value on the right.

Do not forget to escape characters with special regex meaning like brackets:
```YAML
workspaces:
  - id: 538437
    name: Invoices (US)
    targets:
      - id:
        attribute_override:
          name: \(US\)/#/(EU)
```

#### Overriding objects

The JMESPath query for override can be used to replace non-primitive values (e.g., you can replace the whole `settings` object). However, careful if you want to override only a part of the object:

This overrides only the `som` attribute in the object's `metadata`:
```YAML
attribute_override:
  metadata.som: 'second'
```
This overrides the object's whole `metadata` attribute with `{'som': 'second'}`:
```YAML
attribute_override:
  metadata:
	  som: 'second'
```

