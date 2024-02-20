<h1><font color="#006FE8"> Project deployment tool </font></h1>

This command line tool is used to help users customizing and delivering projects on Rossum platform to easily track changes, deploy and release changes/entire project to different environments inside the same cluster.

### Prerequisites ###
*git* - any git based versioning tool  
*rossum account* - *admin* role credentials to at least one organization

### Terms ###
*source* - in the context of this tool references to a dev/test organization and/or workspace(s) where Rossum project and all the associated objects (hooks, queues, ...) are created.  
*target* - a "production" environment (organization and/or workspaces(s)) where the project is deployed for customer use. Eventually changed will be released here from the source environment.  
*local* - file storage of the local machine where git repository of the project is cloned  
*remote* - organization and all the objects owned by the organization in Rossum platform

</br>
<h2><font color="#004795"> Installation guide </font></h2>

```
brew install pipx
pipx ensurepath
pipx install .
```

Restart the terminal.

</br>
<h2><font color="#004795"> User guide </font></h2>

**It's important to understand that this tool, at the current state, DOES NOT do any git commits/reverts/MRs whatsoever. User is responsible to commit (or revert), switch to another branch, whatever is necessary when it is required (ie released new working version, at that point a manual commit is required). This has a reasoning - process of testing/releasing is usually iterative and doing automatic commits would simply flood git repository with meaningless commits and it would be hard to return to a certain working snapshot of the project.**


<span style="color:#004795"> **Initialize empty project** </span>  
(local repository does not exist yet)

Run `prd init <project_name>` which will initialize an empty GIT repository.

Fill in the required credentials in the `credentials.json` file that was created in the project folder - `API_BASE` (ie.: https://elis.rossum.ai/api/v1) and either `TOKEN` or `USERNAME` and `PASSWORD`. Make sure `use_same_org_as_target:false`, unless you are going to release to different organization.  
If you are going to deploy the code to different Rossum organization configure `TO_API_BASE` and either `TO_TOKEN` or `TO_USERNAME` and `TO_PASSWORD` accordingly.  

> ℹ️ This command creates local git repository. If you want to connect it to an existing remote repository, call `git remote add <reponame> <giturl>`. If you already have an existing remote repository, it might be easier to clone it from the remote and create an `credentials.json` file manually in the root folder.


<span style="color:#004795">**Pull (download) configuration of existing project**</span>

Run `pull` command inside the project root folder. This will load all objects stored in the organization, creates `mapping.yaml` file. If this project already contains test and production objects, you will need to modify created `mapping.yaml` file to link the test and production objects (in the context of this readme, these will be refered to as `source` and `target`)

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
      target_object: null
  SCHEMAS:
    - id: 222
      name: Purchase orders schema
      target_object: null
  WORKSPACES:
    - QUEUES:
        - INBOX:
            id: 333
            name: Incoming Purchase Orders
            target_object: null
          id: 4444
          name: Incoming Purchase Orders
          target_object: null
      id: 321654
      name: Dev & test
      target_object: null
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

You've made your changes to the configuration - changed schema, hook settings etc in the `source` folder object's JSON definition . Run `push` command - this command calls git to see all changes in your local repository in `source` folder and pushes all changed objects to Rossum. New files are treated as new objects of the respective category and instead of patching existing object the tool attempts to create new instance of that object.

> ⚠️ Be careful when deleting files (=objects). Changes marked as deleted in your git repository will result in deleting the counterpart object in Rossum. This includes for instance entire workspace - cascade delete is called on all child objects of the workspace.


<span style="color:#004795">**Release tested configuration to production**</span>

All changes have been tested and you are ready to push the configuration to production organization/workspace. At this point commit your changes in the `source` folder. Call `release` command - this will `push` all objects from the `source` and using `mapping.yaml` update existing objects or create new ones in the `target` (organization/workspace(s)). This command will also override attributes of the `source` objects as defined in the `mapping.yaml` (see description of `mapping.yaml` below). If the `target` is in the same organization (ie. different workspace), after the release a `pull` is automatically called and `source` and `target` folders are updated.

After the release the sample project mapping will be updated with target_object ids.
```
ORGANIZATION: # organization category, always top level
  id: 123456 # id of the organization
  name: Production # name of the organization
  target_object: 123789 # id of the couterpart object in the target environment
  HOOKS: # hooks category
    - id: 111
      ignore: true # if true, object is not pushed to remote
      name: Magic Items
      target_object: null # this remains empty, because ignore flag prevented the release to create the counterpart object
  SCHEMAS:
    - id: 222
      name: Purchase orders schema
      target_object: 2222
  WORKSPACES:
    - QUEUES:
        - INBOX:
            id: 333
            name: Incoming Purchase Orders
            target_object: 3333
          id: 4444
          name: Incoming Purchase Orders
          target_object: 4444
      id: 321654
      name: Dev & test
      target_object: 321987
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

<span style="color:#004795">**Production release went bad, I need to revert**</span>

Either the `release` command failed unexpectedly or the released version does not work in production. Revert all changes in the `target` folder and call `push target` command. This will release all objects from `target` folder as they are (no attribute override is performed).

</br>
<h2><font color="#004795"> Available commands </font></h2>

```
pull
```   
Pulls (downloads) all objects from the `source` & `target` environment and updates (or creates) folder & file structure in `source` and `target` folder in the project's local repository. Environment used is the organization of the user (determined from the credentials provided in credentials.json file).  

If `mapping.yaml` file does not exist, file is created and populated with all pulled objects. In this case all objects are considered `source` (in the case of existing test/production deployment, the `mapping.yaml` file needs to be updated to link objects with their `target`). After this is done and `push` command is called, the `mapping.yaml` file is cleaned and only `source` objects remain while `target` objects remain referenced in the _target_ section of each object.

If `mapping.yaml` is already existing, missing records for new objects are created and records for no longer existing objects are removed. If there are new objects found in the organization, an attempt is made to determine whether they belong to `source` or `target` (by analyzing existing `mapping.yaml` file and finding nearest parent object [workspace/organization]). If this cannot be determined, user is prompted to classify the new object(s).
```
push
```
Pushes all eligible (see `mapping.yaml` definition) objects into the `source` organization in Rossum platform. 

```
push target
```
Pushes all eligible objects from local `target` to remote `target`.

```
release
```
Pushes all eligible objects from local `source` to remote `target`. This command replaces all variables and overriden attributes as defined in `mapping.yaml`

</br>
<h2><font color="#004795"> Supported objects </font></h2>

    organizations, workspaces, queues, inboxs, schemas, hooks

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
`mapping.yaml` - file containing metadata of all indexed objects of the `source` enevironment and their respective couterparts in the `target` environment  

#### credentials.json #### 
`API_BASE` - base URL of Rossum API, ending with api version - ie https://elis.rossum.ai/api/v1  
`TOKEN` - valid token generated for admin rossum account. Recommended is to use PASSWORD and USERNAME.
`USERNAME` - Rossum admin account username that is used to generate auth token used for all Rossum API calls  
`PASSWORD` - password for Rossum admin account username  
`USE_SAME_ORG_AS_TARGET` - must be se to true if both source and target environments are in the same organization

#### mapping.yaml ####  
Initialized when not existing or empty during `pull` command. Missing object records are automatically added to this file during `pull` command. Objects missing `target` attribute are copied to the `target` during the `release` and the file is then automatically updated with the `target` object IDs once completed.

`ORGANIZATION | WORKSPACES | QUEUES | INBOX | SCHEMAS | HOOKS` - object type name, used primarily to define structure of the mapping file.  
`id` - unique ID of the Rossum API object.  
`name` - name of the Rossum API object instance.  
`target` - ID of the counterpart object in the `target` environment.  
`ignore` - attribute controlling whether object is pushed to remote during `release` command. Object with `ignore:true` are not pushed to `target` environment. `source` is unaffected and `push` command always releases all changes from the `source` folder.  
`attribute_override` - keys representing attributes of the object on Rossum API are replaced with the value associated with the key during `release` call.  
`attribute_override.{key}` - name of the attribute to be replaced with value of the key - `name`, `url` etc. (basically any writable attribute of the API object).  
 
> Example: `attribute_override.name: "my production hook"`. `source` hook's name "my test hook" is renamed to "my production hook" when deploying the hook to `target` environment.  

`attribute_override.{key}.path` - used when only substring of the attribute's value should be overriden. For instance use to replace queue IDs commonly referenced in various hook.settings (MDH).  
`attribute_override.{key}.reference_type` - only when `path` is defined. This attribute specifies what value type is being overriden and looks for its counterpart in the `mapping.yaml` file. Possible values `ORGANIZATION | WORKSPACES | QUEUES | INBOX | SCHEMAS | HOOKS`.    

> Example: parameters are set as follows - `attribute_override.settings.path:configurations.queue_ids` and `attribute_override.settings.reference_type:QUEUES` - when `release` command is called, `source` object's `hook.settings` is parsed, the `path` is found and all queue references (supports integers, strings and URLs) are replaced with their `target` counterparts.  