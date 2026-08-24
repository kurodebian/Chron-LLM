# src/causal_kernel/kernel/validator/schema_validator.py
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import jsonschema
from jsonschema import Draft202012Validator


class SchemaValidator:
    """Draft 2020-12 に準拠した厳格なスキーマ検証クラス"""

    SCHEMA_MAPPING = {
        "delta1_extraction": "delta1-extraction.schema.json",
        "delta1_graph": "delta1-graph.schema.json",
        "delta2_mastergraph": "delta2-mastergraph.schema.json",
        "traceability": "traceability.schema.json",
    }

    def __init__(self, schema_dir: str = "schemas"):
        self.schema_dir = Path(schema_dir)
        self.validators: Dict[str, Draft202012Validator] = {}
        self._load_schemas()

    def _load_schemas(self):
        """schemas ディレクトリから定義を読み込み、Draft202012Validator を初期化"""
        for key, filename in self.SCHEMA_MAPPING.items():
            schema_path = self.schema_dir / filename
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)

            Draft202012Validator.check_schema(schema_data)
            self.validators[key] = Draft202012Validator(schema_data)

    def validate(self, data: Dict[str, Any], schema_type: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """インメモリの dict データを検証し、詳細なエラー情報を返す"""
        if schema_type not in self.validators:
            raise ValueError(f"Unknown schema type: '{schema_type}'. Valid types: {list(self.validators.keys())}")

        validator = self.validators[schema_type]
        errors = list(validator.iter_errors(data))

        if not errors:
            return True, []

        detailed_errors = []
        for err in errors:
            path = ".".join(str(p) for p in err.absolute_path) or "<root>"
            detailed_errors.append({
                "path": path,
                "message": err.message,
                "validator": err.validator,
                "validator_value": err.validator_value,
            })

        return False, detailed_errors

    def validate_file(self, file_path: str, schema_type: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """指定された JSON ファイルを読み込んで検証"""
        path = Path(file_path)
        if not path.exists():
            return False, [{"path": str(file_path), "message": "File not found"}]

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [{"path": str(file_path), "message": f"JSON Decode Error: {e}"}]

        return self.validate(data, schema_type)