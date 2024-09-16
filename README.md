<h1><font color="#006FE8"> Project deployment tool </font></h1>

This command line tool is used to help users customizing and delivering projects on Rossum platform to easily track changes, deploy and release changes/entire project to different environments inside the same cluster.

### Prerequisites ###
**git** - any git based versioning tool  
**rossum account** - *admin* role credentials to at least one organization

### Terms ###
**source** - in the context of this tool references to a dev/test organization and/or workspace(s) where Rossum project and all the associated objects (hooks, queues, ...) are created.  
**target** - a "production" environment (organization and/or workspaces(s)) where the project is deployed for customer use. Eventually changes will be released here from the source environment.  
**local** - file storage of the local machine where git repository of the project is cloned  
**remote** - organization and all the objects owned by the organization in Rossum platform

</br>
<h2><font color="#004795"> Installation guide </font></h2>

1. You can use this one-liner to download the installation script and let it execute the steps automatically:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/rossumai/prd/main/install.sh)"
```
2. You can also do these steps manually:
```
git clone https://github.com/rossumai/prd.git
cd prd

brew install pipx

pipx ensurepath
pipx install .
```

Restart the terminal.

When updating, you can:
1. Run `prd update`.
2. Run `git pull` where you manually pulled the repository and then run `pipx install . --force`.

</br>
<h2><font color="#004795"> User guide </font></h2>

**Note that this tool is not designed to automatically do any git commits, rollbacks, merge requests and similar git actions. User is responsible to commit (or revert), switch to another branch, whatever is necessary when it is required (i.e., released new working version, at that point a manual commit is required). This has a reasoning - process of testing/releasing is usually iterative and doing automatic commits would simply flood git repository with meaningless commits and it may make it harder to return to a certain working snapshot of the project.**


<span style="color:#004795"> **Initialize empty project and repository** </span>  

1. Run `prd init <project_name>` which will initialize an empty GIT repository. You can also use `.` for the project name and use the current directory.
2. Fill in the required credentials in the `credentials.json` file that was created in the project folder - either `source.token` (retrieved using /auth endpoint) or `source.username` and `source.password`.
3. Fill in `source_api_base` in the `prd_config.yaml` file.
4. If you are going to deploy the code to a different Rossum organization configure `target_api_base` and `use_same_org_as_target: false` in `prd_config.yaml` and either `target.token` or `target.username` and `target.password` in `credentials.json`.

> ℹ️ This command creates local git repository. If you want to connect it to an existing remote repository, call `git remote add <reponame> <giturl>`. If you already have an existing remote repository, it might be easier to clone it from the remote and create an `credentials.json` file manually in the root folder.


<span style="color:#004795">**Pull (download) configuration of existing project**</span>

Run `pull` command inside the project's root folder. This will load all objects stored in the organization and create `mapping.yaml` file. If this project already contains test and production objects, you will need to modify created `mapping.yaml` file to link the test and production objects (in the context of this readme, these will be referred to as `source` and `target`)  
  
Sample `mapping.yaml` after `pull` of simple project. Notice how `target_object` is null, that's because there are no "production" versions of these objects yet. More about that later.
```
ORGANIZATION: # organization category, always top level
  id: 123456 # id of the organization
  name: Production # name of the organization
  target_object: null # id of the couterpart object in the target environment
  HOOKS: # hooks category
    - id: 111
      ignore: true # if true, object is not pushed to remote
      name: Magic Items
      targets
        - target_id: null
  SCHEMAS:
    - id: 222
      name: Purchase orders schema
      targets
        - target_id: null
  WORKSPACES:
    - QUEUES:
        - INBOX:
            id: 333
            name: Incoming Purchase Orders
            targets
              - target_id: null
          id: 4444
          name: Incoming Purchase Orders
          targets
            - target_id: null
      id: 321654
      name: Dev & test
      targets
        - target_id: null
          attribute_override:
            name: Prod
```
And the source folder after pulling these objects:
```
source
 ┣ hooks
 ┃ ┗ Magic Items_[111].json
 ┣ schemas
 ┃ ┗ Purchase orders schema_[222].json
 ┣ workspaces
 ┃ ┗ Dev & Test_[321654]
 ┃ ┃ ┣ queues
 ┃ ┃ ┃ ┗ Incoming Purchase Orders_[4444]
 ┃ ┃ ┃ ┃ ┣ inbox.json
 ┃ ┃ ┃ ┃ ┗ queue.json
 ┃ ┃ ┗ workspace.json
 ┗ organization.json
```

<span style="color:#004795">**Push (upload) configuration for testing**</span>

You've made your changes to the configuration - changed schema, hook settings etc in the `source` folder object's JSON definition . Run `push` command - this command calls git to see all changes in your local repository in `source` folder and pushes all changed objects to Rossum.  

Push command by default analyzes `modified_at` attribute (can be overridden by `-f` parameter) on each API object in the `remote` and `local` and compares them - if the `modifed_at` timestamp in the `remote` is different to the one in the local repository, the push command will skip pushing this object to the `remote` to avoid overwriting changes to the object that haven't been versioned yet.  

By adding `-a` the tool pushes all objects from your `local` to the `remote`, irrespective if they were changed or not.


<span style="color:#004795">**Release tested configuration to production**</span>

All changes have been tested and you are ready to push the configuration to production organization/workspace. At this point commit any changes in the `source` folder.  
Next, prepare the `mapping.yaml` for release ([see mapping section] #mapping)  

> 🛑 If you have referenced some existing objects as a target to be updated (meaning `target_id` was set in the mapping), make sure to call `pull` after modifying the `mapping.yaml` - this will move the objects referenced into target folder.

Call `release` command - this will `push` all objects from the `source` and using `mapping.yaml` update existing objects or create new ones in the `target` (organization/workspace(s)). This command will also override attributes of the `source` objects as defined in the `mapping.yaml` (see description of `mapping.yaml` below). After the release a `pull` is automatically called and `source` and `target` folders are updated.  

It is recommended to first run the command with `-p` parameter to see the overview of the changes that are going to be released. This should help validate `mapping.yaml` is configured correctly before releasing to avoid complicated rollback if the mapping is misconfigured.

After the release the sample project mapping will be updated with target_object IDs.
```
ORGANIZATION: # organization category, always top level
  id: 123456 # id of the organization
  name: Production # name of the organization
  targets:
    - target_id: 123789 # id of the couterpart object in the target environment
  HOOKS: # hooks category
    - id: 111
      ignore: true # if true, object is not pushed to remote
      name: Magic Items
      targets:
        - target_id: null # this remains empty, because ignore flag prevented the release to create the counterpart object
  SCHEMAS:
    - id: 222
      name: Purchase orders schema
      targets:
        - target_id: 2222
  WORKSPACES:
    - QUEUES:
        - INBOX:
            id: 333
            name: Incoming Purchase Orders
            targets:
              - target_id: 3333
          id: 4444
          name: Incoming Purchase Orders
          targets:
            - target_id: 4444
      id: 321654
      name: Dev & test
      targets:
        - target_id: 321987
          attribute_override:
            name: Prod
```

And the `target` folder after the release is finished. Notice the name of the Workspace - this is due to the `attribute_override` defined in the mapping file. Hook Magic Items is missing because `ignore` flag was set to true.
```
target
 ┣ hooks
 ┣ schemas
 ┃ ┗ Purchase orders schema_[2222].json
 ┣ workspaces
 ┃ ┗ Prod_[321987]
 ┃ ┃ ┣ queues
 ┃ ┃ ┃ ┗ Incoming Purchase Orders_[4444]
 ┃ ┃ ┃ ┃ ┣ inbox.json
 ┃ ┃ ┃ ┃ ┗ queue.json
 ┃ ┃ ┗ workspace.json
 ┗ organization.json
```

Once the production release is successful, commit all the changes in the `target` folder so that you have a working snapshot prepared for when new changes are released in the future.

</br>
<h2><font color="#004795"> Available commands </font></h2>

You can see all parameters for each command by calling `<command> --help`

```
pull
```   
Pulls (downloads) all objects from the `source` & `target` environment and updates (or creates) folder & file structure in `source` and `target` folder in the project's local repository. Environment used is the organization of the user (determined from the credentials provided in credentials.json file).  

If `mapping.yaml` file does not exist, file is created and populated with all pulled objects. In this case all objects are considered `source` (in the case of existing test/production deployment, the `mapping.yaml` file needs to be updated to link objects with their `target`). After this is done and `push` command is called, the `mapping.yaml` file is cleaned and only `source` objects remain while `target` objects remain referenced in the _target_ section of each object.

If `mapping.yaml` is already existing, missing records for new objects are created and records for no longer existing objects are removed. If there are new objects found in the organization, an attempt is made to determine whether they belong to `source` or `target` (by analyzing existing `mapping.yaml` file and finding nearest parent object [workspace/organization]). If this cannot be determined, user is prompted to classify the new object(s).

Just like `push` command, `pull` utilizes `modified_at` timestamp to avoid overwriting `local` objects that are ahead of the `remote` objects.

A `-c` or `-cm` parameter can be added to automatically commit all changes with default or custom (`-m` parameter) commit message right after the pull finishes.
```
push
```
Pushes all eligible (see `mapping.yaml` definition) objects into the `source` organization in Rossum platform. 

```
push target
```
Pushes all eligible objects from local `target` to remote `target`.

The push command also accepts `-a` parameter that will take everything in `source`/`target` and update the corresponding objects in Rossum. If these objects cannot be found, they are recreated.

```
release
```
Pushes all eligible objects from local `source` to remote `target`. This command replaces all variables and overriden attributes as defined in `mapping.yaml`

A single API object can be released/synchronized to multiple target objects by specifying an array of `targets` in the `mapping.yaml`

</br>
<h2><font color="#004795"> Supported objects </font></h2>

    organizations, workspaces, queues, inboxes, schemas, hooks

<h2><font color="#004795"> Unsupported objects' attributes </font></h2>
  The following object attributes are ignored - that means they are not pulled nor pushed.</br></br>
  Queue: ["counts", "users", "workflows"]</br>
  Hook: ["status"]</br>


</br>
<h2><font color="#004795"> Folder & file structure </font></h2>

```
├──source
│   ├──organization.json
│   │──workspaces
│   │   ├──workspace.json
│   │   └──queues
│   │       ├──queue.json
│   │       └──inboxes
│   │           └──inbox.json
│   ├──schemas
│   │   └──schema.json
│   └──hooks
│       └──hook.json
├──target
│   ├──organization.json
│   ├──workspaces
│   │   ├──workspace.json
│   │   └──queues
│   │       ├──queue.json
│   │       └──inboxes
│   │           └──inbox.json
│   ├──schemas
│   │   └──schema.json
│   └──hooks
│      └──hook.json
credentials.json
mapping.yaml
```

`credentials.json` - base configuration file of the tool - contains rossum username/credentials as well as other global parameters  
`mapping.yaml` - file containing metadata of all indexed objects of the `source` environment and their respective couterparts in the `target` environment  

<h3>credentials.json</h3>

```
{
    "source": {
        "api_base": "...",
        "username": "...",
        "password": "..."
    },
    "use_same_org_as_target": true,
    "target": {
        "api_base": "...",
        "username": "...",
        "password": "..."
    }
}
```
`api_base` - base URL of Rossum API, ending with api version - ie https://elis.rossum.ai/api/v1  
`token` - valid token generated for admin rossum account. Recommended is to use PASSWORD and USERNAME.
`username` - Rossum admin account username that is used to generate auth token used for all Rossum API calls  
`password` - password for Rossum admin account username  

<a id="mapping"></a><h3>mapping.yaml</h3>
Initialized when not existing or empty during `pull` command. Missing object records are automatically added to this file during `pull` command. Objects missing `target` attribute are copied to the `target` during the `release` and the file is then automatically updated with the `target` object IDs once completed.

`ORGANIZATION | WORKSPACES | QUEUES | INBOX | SCHEMAS | HOOKS` - object type name, used primarily to define structure of the mapping file.  
`id` - unique ID of the Rossum API object.  
`name` - name of the Rossum API object instance.  
`target` - ID of the counterpart object in the `target` environment.  
`ignore` - attribute controlling whether object is pushed to remote during `release` command. Object with `ignore:true` are not pushed to `target` environment. `source` is unaffected and `push` command always releases all changes from the `source` folder.  
`attribute_override` - includes key:value pairs. The jeys are JMESPath queries. The values replace whatever is found with these queries during `release` call. The values can also include special keywords:

1. Implicit object reference override - it is always attempted to replace object references in any `object.settings` without having to explicitly define it using any option below. This implicit replacement uses `mapping.yaml` definition to determine relationships between `source` and `target` objects.
2. `$prd_ref` - replaces the value or list of values in source (found with the [JMESPath](https://jmespath.org/tutorial.html) query) with their target counterparts. This can be only used for IDs. For example, `queue_ids` in hook configurations.
3. `$source_value` - replaces the keyword with the original (source) attribute's value. Can be used in a string like `$source_value - PROD` (overriding name in this case).
 

```
attribute_override:
  name: "my production hook"
```
`source` hook's name "my test hook" is renamed to "my production hook" when deploying the hook to `target` environment.  

```
attribute_override:
  settings.configurations[*].queue_ids: $prd_ref
```
When the `release` command is called, this query makes the tool look into all objects inside the array under `settings.configurations` and override their `queue_ids` attribute with a target ID counterpart.

The JMESPath query for override can be used to replace non-primitive values (e.g., you can replace the whole `settings` object), but the value must be statically defined in attribute_override (no keywords).

When using keywords, the JMESPath query should end with an attribute which is a single value or a list of such values (`3333` or [`333`, `13993`, `93`]).
