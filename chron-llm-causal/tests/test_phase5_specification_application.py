import json
from pathlib import Path
import pytest

@pytest.fixture
def audit_data():
    audit_path = Path("data/audit/phase5_specification_application_v1.json")
    assert audit_path.exists(), "FAIL: 監査JSONファイルが存在しません"
    return json.loads(audit_path.read_text(encoding="utf-8"))

def test_verdict_is_pass(audit_data):
    """VERDICT が PASS であることの明示的検証"""
    assert audit_data["verdict"] == "PASS", f"FAIL: 生成器のVerdictが {audit_data['verdict']} です"

def test_source_coverage(audit_data):
    """補強1: 行数カバレッジの再計算によるパース漏れ検証"""
    cov = audit_data["source_coverage"]
    assert cov["total_source_lines"] > 0
    assert cov["total_source_lines"] == cov["total_extracted_lines"], "FAIL: 抽出漏れ（サイレントドロップ）を検出"

def test_zero_loss_accounting(audit_data):
    """ゼロロス会計不変条件の再集計検証"""
    total = len(audit_data["specification_units"])
    mapped = len(audit_data["delta1_mappings"])
    unresolved = len(audit_data["unresolved"])
    
    assert total == (mapped + unresolved), f"FAIL: 会計違反 Total({total}) != Mapped({mapped}) + Unresolved({unresolved})"
    assert audit_data["accounting"]["silent_loss"] == 0, "FAIL: silent_loss が検知されました"

def test_unresolved_categorization(audit_data):
    """補強2: unresolved 原因カテゴリとテキストの必須検証"""
    valid_categories = {"MISSING_DEPENDENCY", "CROSS_DOMAIN_CONFLICT", "OBSOLETE_SPEC", "AMBIGUOUS_AUTHORITY"}
    for u in audit_data["unresolved"]:
        assert "category" in u, f"FAIL: {u['unit_id']} にカテゴリタグがありません"
        assert u["category"] in valid_categories, f"FAIL: 不正なカテゴリタグ {u['category']}"
        assert len(u.get("reason", "").strip()) > 0, "FAIL: 原因テキストが空です"

def test_authority_and_invariants_structure(audit_data):
    """権限境界と不変条件の構造検証"""
    assert len(audit_data["authority_boundaries"]) > 0, "FAIL: 権限境界が定義されていません"
    assert len(audit_data["invariant_dependencies"]) > 0, "FAIL: 不変条件依存が定義されていません"
    
    for r in audit_data["causal_relations"]:
        assert r["classification"] in ["EVIDENCE", "CANDIDATE"]
        assert r["classification"] != "PROMOTED", "FAIL: 推論の事実への不当昇格を検出"

def test_provenance_completeness(audit_data):
    """Provenance集合の完全一致検証"""
    units = {u["unit_id"] for u in audit_data["specification_units"]}
    provs = {p["unit_id"] for p in audit_data["provenance"]}
    assert units == provs, "FAIL: Specification Unit と Provenance の集合が不一致です"