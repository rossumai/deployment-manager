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
