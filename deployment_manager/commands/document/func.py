def find_matching_configurations(hooks: dict, schema_id: str):
    matching_configs = []
    additional_mapping = False
    target_schema_id = None
    for hook in hooks:
        template = hook.get("hook_template") if hook.get("hook_template") else ""
        config_url = hook.get("config",{}).get("url", "")
        if template.endswith("hook_templates/39") or "svc/master-data-hub" in config_url:
            for config in (hook["settings"].get("configurations", {}) or hook["settings"].get("configs", {})):
                #print (f"schema_id {schema_id}")
                additional_mappings = [x["target_schema_id"] for x in config.get("additional_mappings", [])]
                #print (f"config.mapping {config["mapping"]}")
                if schema_id == config["mapping"]["target_schema_id"]:
                    matching_configs.append(config)
                if schema_id in additional_mappings:
                    target_schema_id = config["mapping"]["target_schema_id"]
                    additional_mapping = True

    return matching_configs, additional_mapping, target_schema_id
