import json
import pathlib
import pytest

AUDIT_DIR = pathlib.Path("data/audit").resolve()
CORPUS_DIR = pathlib.Path("../spec_sheet").resolve()

FULL_EXTRACTION_FILE = AUDIT_DIR / "phase6_full_extraction_v2.json"
INVENTORY_FILE = AUDIT_DIR / "phase6_source_inventory_v2.json"
UNRESOLVED_FILE = AUDIT_DIR / "phase6_unresolved_v2.json"
PROVENANCE_FILE = AUDIT_DIR / "phase6_provenance_v2.json"


def test_required_audit_files_exist():
    """必要な 4 つの Phase 6 監査 JSON が存在することを確認"""
    assert FULL_EXTRACTION_FILE.exists(), f"Missing {FULL_EXTRACTION_FILE}"
    assert INVENTORY_FILE.exists(), f"Missing {INVENTORY_FILE}"
    assert UNRESOLVED_FILE.exists(), f"Missing {UNRESOLVED_FILE}"
    assert PROVENANCE_FILE.exists(), f"Missing {PROVENANCE_FILE}"


def test_source_file_count_exact_104():
    """ソースファイル数が正確に 104 であることを検証"""
    with open(FULL_EXTRACTION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data.get("source_files") == 104, f"Expected 104 source files, got {data.get('source_files')}"
    assert data.get("file_count_discrepancy") == 0


def test_zero_silent_loss_and_merge():
    """サイレントロスおよびセマンティックマージが 0 であることを検証"""
    with open(FULL_EXTRACTION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("silent_loss") == 0, "Silent loss detected!"
    assert data.get("silent_merge") is False, "Silent merge detected!"


def test_no_false_yaml_enum_dependency():
    """YAML enum 宣言の不当判定が 0 件であることを検証"""
    with open(FULL_EXTRACTION_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    with open(UNRESOLVED_FILE, "r", encoding="utf-8") as f:
        unresolved_data = json.load(f)

    assert audit_data.get("false_yaml_enum_dependency_count") == 0
    assert unresolved_data.get("false_unresolved_count") == 0


def test_provenance_and_accounting_complete():
    """全抽出項目に Provenance が紐づき、未分類ファイルがないことを検証"""
    with open(FULL_EXTRACTION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("missing_provenance_count") == 0
    assert data.get("unclassified_files_count") == 0
    assert data.get("unclassified_records_count") == 0


def test_phase6_final_verdict_pass():
    """最終 Verdict が PASS であることを検証"""
    with open(FULL_EXTRACTION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("verdict") == "PASS", f"Verdict is {data.get('verdict')}, expected PASS"