# generate_schema_from_types.py
import re
import json
from pathlib import Path

TARGET_NAME = "chron-llm-spec-v0.2.spec"

def find_sot():
    """
    archive/ を除外して SOT を探す
    """
    for path in Path(".").rglob(TARGET_NAME):
        if "archive" not in str(path):
            return path
    raise FileNotFoundError(f"{TARGET_NAME} not found outside archive/")

SOT_FILE = find_sot()
print(f"Using SOT file: {SOT_FILE}")

TYPE_MAP = {
    "ID": {"type": "string"},
    "Role": {"type": "string", "enum": ["reply", "temporal", "bridge"]},
    "Int": {"type": "integer"},
    "Float": {"type": "number"},
    "Time": {"type": "number"},
    "Bool": {"type": "boolean"},
    "Area": {"type": "number"},
}

def is_field_line(line):
    if ":" not in line:
        return False
    if line.count(":") != 1:
        return False
    if any(x in line for x in ["=", "==", "IF", ">", "<"]):
        return False
    return True

def parse_type_block(text):
    types = {}
    pattern = r"TYPE\s+(\w+)\s*=\s*\{([^}]*)\}"
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)

    for typename, body in matches:
        schema = {"type": "object", "properties": {}, "required": []}
        lines = [line.strip() for line in body.split("\n")]
        fields = [line for line in lines if is_field_line(line)]

        for f in fields:
            name, t = f.split(":", 1)
            name = name.strip()
            t = t.strip()

            if t.endswith("[]"):
                base = t[:-2]
                schema["properties"][name] = {
                    "type": "array",
                    "items": TYPE_MAP.get(base, {"type": "string"})
                }
            elif t.endswith("?"):
                base = t[:-1]
                schema["properties"][name] = TYPE_MAP.get(base, {"type": "string"})
            elif t.startswith("Float["):
                schema["properties"][name] = {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                }
            elif "|" in t:
                opts = [x.strip() for x in t.split("|")]
                schema["properties"][name] = {"type": "string", "enum": opts}
            else:
                schema["properties"][name] = TYPE_MAP.get(t, {"type": "string"})

            schema["required"].append(name)

        types[typename] = schema

    return types

def main():
    text = SOT_FILE.read_text()
    types = parse_type_block(text)

    with open("chron-llm-spec-v0.2.schema.json", "w") as f:
        json.dump(types, f, indent=2)

    print("Generated chron-llm-spec-v0.2.schema.json")

if __name__ == "__main__":
    main()
