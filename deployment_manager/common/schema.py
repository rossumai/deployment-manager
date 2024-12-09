from typing import Any


def find_schema_id(schema: Any, schema_id: str):
    if isinstance(schema, list):
        for subschema in schema:
            result = find_schema_id(subschema, schema_id)
            if result:
                return result
    elif isinstance(schema, dict) and "children" in schema:
        if isinstance(schema["children"], dict):
            result = find_schema_id(schema["children"], schema_id)
            if result:
                return result
        elif isinstance(schema["children"], list):
            for subschema in schema["children"]:
                result = find_schema_id(subschema, schema_id)
                if result:
                    return result
    elif isinstance(schema, dict) and schema.get("id", None) == schema_id:
        return schema
