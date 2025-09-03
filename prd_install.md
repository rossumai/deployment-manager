# Intall a fork of PRD with the docommando command:
cd ~
mkdir prd-doc-fork
cd prd-doc-fork
python -m venv .venv
source .venv/bin/activate
pip install https://github.com/rossumai/deployment-manager/releases/download/v2.5.2b/deployment_manager-2.5.2-py3-none-any.whl
nano ~/.zshrc
# Add this to the end of the file
alias prddoc=~/prd-doc-fork/.venv/bin/prd2
# Exit via CTRL + C
source ~/.zshrc
# You should see docommando listed:
prddoc

# Follow the instructions in this article to set up AWS CLI:
https://rossumai.atlassian.net/wiki/spaces/RAD/pages/2621112497/Logging+to+AWS
# The only difference to the guide is to put this into ~/.aws/config:
[sso-session main]
sso_start_url = https://d-93670fe985.awsapps.com/start
sso_region = eu-west-1

[profile rossum-dev]
region = eu-west-1
sso_session = main
sso_account_id = 494114742120
sso_role_name = BedrockDev

# Once you are logged into AWS via 'aws sso login', everything should be ready
# Now you should set up a PRD project:
cd ~/prd-projects # or whatever
prddoc init <my-project-name>
# Follow the instructions on the CLI and once done, move to the directory
cd <my-project-name>
prddoc docommando
# Now select the dir and subdir and queues by following the CLI instructions
