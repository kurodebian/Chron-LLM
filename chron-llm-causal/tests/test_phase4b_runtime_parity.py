import json
from pathlib import Path

def test_phase4b_independent_runtime_parity():
    audit_path = Path("data/audit/phase4b_runtime_parity_v1.json")
    assert audit_path.exists(), "Audit artifact missing"
    
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    
    assert data["audit_version"] == "PHASE4B_RUNTIME_PARITY_V1"
    assert data["sbcl_execution"]["exit_code"] == 0
    assert data["verdict"] == "PASS"
    assert len(data["discrepancies"]) == 0
    
    trace = data["sbcl_execution"]["trace"]
    expected = data["independent_expected_trace"]
    
    # 独立再計算トレースとSBCL実効トレースの一致性検証
    assert trace == expected
    
    tests_map = {t["test_id"]: t for t in trace}
    
    # 個別テストケースおよびエラー理由の厳密アサート
    assert tests_map["TC1_VALID_PATH"]["status"] == "ACCEPT"
    assert tests_map["TC2_INVALID_AUTH"]["status"] == "REJECT"
    assert tests_map["TC2_INVALID_AUTH"]["reason"] == "ERR_MISSING_AUTH_GUARD"
    assert tests_map["TC3_DERIVE_PURITY_VIOLATION"]["status"] == "REJECT"
    assert tests_map["TC3_DERIVE_PURITY_VIOLATION"]["reason"] == "ERR_DERIVE_PURITY_FAIL"