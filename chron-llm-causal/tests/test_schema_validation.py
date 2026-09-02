from pathlib import Path
import pytest
from causal_kernel.kernel.validator.schema_validator import SchemaValidator

@pytest.fixture
def validator():
    return SchemaValidator(schema_dir="schemas")

@pytest.mark.parametrize("data_path,schema_name", [
    # Delta1Extraction
    ("data/delta1_normalized/causal_extract_core_v1.json", "delta1_extraction"),
    ("data/delta1_normalized/causal_extract_core_v2.json", "delta1_extraction"),
    # Delta1Graph
    ("data/audit/phase6_dependency_graph_v1.json", "delta1_graph"),
    ("data/audit/phase7_global_causal_graph_v1.json", "delta1_graph"),
    ("data/audit/phase7_global_specification_graph_v1.json", "delta1_graph"),
    # Delta2MasterGraph
    ("data/graphs/causal_master_graph_v2.json", "delta2_mastergraph"),
])
def test_real_data_schema_compliance(validator, data_path, schema_name):
    path = Path(data_path)
    assert path.exists(), f"データファイルが存在しません: {data_path}"
    
    is_valid, errors = validator.validate_file(path, schema_name)
    assert is_valid, f"{data_path} のスキーマ検証に失敗しました:\n" + "\n".join(str(e) for e in errors)