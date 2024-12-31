# Check source workspaces
# If 404 -> remove target (if there are queues, let the error happen) and remove from yaml

# Check source queues
# If 404 -> remove target and remove from yaml (including subobjects)
# If no other queue is using its schema, remove it as well

# Check queue.inbox
# If 404 -> remove target and remove from yaml

# Check hooks
# If 404 -> remove target and remove from yaml

# If there was any 404 -> repull source (and target if applicable)
