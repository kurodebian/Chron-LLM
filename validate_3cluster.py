# validate_3cluster.py
import json
from jsonschema import validate

schema = json.load(open("chron-llm-spec-v0.2.schema.json"))
instance = json.load(open("3cluster.instance.json"))

try:
    validate(instance, schema)
    print("OK: 3cluster.instance.json matches SOT schema.")
except Exception as e:
    print("ERROR:", e)
    exit(1)
