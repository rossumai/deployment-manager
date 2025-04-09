import requests
import operator
from rossum_python import *


def rossum_hook_request_handler(payload: dict) -> dict:
    rossum = RossumPython.from_payload(payload)
    settings = payload.get("settings", {})
    base_url = payload["base_url"]
    
    try:
        field = settings["field"]
        label_id = settings["label_id"]
        add_condition = settings["add_condition"]
        remove_condition = settings["remove_condition"]
    except KeyError as e:
        rossum.show_error(f"Missing required setting: {e}")
        return rossum.hook_response()
    
    operators = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne
    }
    
    if hasattr(rossum.field, field):
        value = getattr(rossum.field, field).value
        
        for op_symbol, op_func in operators.items():
            if isinstance(add_condition, str) and add_condition.startswith(op_symbol):
                if op_symbol in [">", "<", ">=", "<="]:
                    try:
                        value = float(value)
                        threshold = float(add_condition[len(op_symbol):].strip())
                    except ValueError:
                        rossum.show_error(f"Value or condition threshold could not be converted to float.")
                        return rossum.hook_response()
                if op_func(value, threshold):
                    print(value, threshold, op_symbol)
                    modify_label(rossum, base_url, "add", label_id)
                break
        else:
            
            if value == add_condition:
                
                modify_label(rossum, base_url, "add", label_id)
        
        if value == remove_condition:
            modify_label(rossum, base_url, "remove", label_id)
            
        
    return {"messages": [], "operations": []}
   
    
def modify_label(rossum: RossumPython, base_url, operation: str, label_id: int) -> None:
    body = {
        "operations": {
            operation: [f"{base_url}/api/v1/labels/{label_id}"]
        },
        "objects": {
            "annotations": [rossum.annotation.url]
        }
    }
    
    auth = {
        "Authorization": f"Bearer {rossum.annotation._token}"
    }
    
    requests.post(f"{base_url}/api/v1/labels/apply", json=body, headers=auth)