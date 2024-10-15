import re
from ruamel.yaml import YAML


class DeployYaml:
    RELEASE_KEYWORD_REGEX = re.compile(r"^release(_(\w)+)?$")

    def __init__(self, file: str):
        self._yaml = YAML()
        self.data = self._yaml.load(file)

    def get_object_in_yaml(self, type: str, id: int):
        objects = self.data.get(type, [])
        for object in objects:
            if object.get("id", None) == id:
                return object
        return None

    def save_to_file(self, file_path: str):
        with open(file_path, "wb") as wf:
            self._yaml.dump(self.data, wf)
