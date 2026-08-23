import json
import pathlib
import pytest

CORPUS_DIR = pathlib.Path("../spec_sheet").resolve()
AUDIT_FILE = pathlib.Path("data/audit/phase7a_phase6_extraction_audit_v1.json").resolve()

# .spec を含むサポート対象拡張子の定義
SUPPORTED_EXTENSIONS = {".spec", ".yaml", ".yml", ".json", ".md", ".lisp", ".txt", ".org"}


def get_actual_corpus_files():
    """コーパスディレクトリ配下の全仕様書ファイルを独立して全数走査 (.spec を含む)"""
    if not CORPUS_DIR.exists():
        pytest.skip(f"Corpus directory {CORPUS_DIR} does not exist.")

    files = [
        p for p in CORPUS_DIR.rglob("*")
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def test_source_inventory_complete():
    """1. コーパスの全ソースファイル数と監査レポート報告数の整合性を検証"""
    actual_files = get_actual_corpus_files()
    assert len(actual_files) > 0, f"Spec corpus in {CORPUS_DIR} is empty or has no supported files!"

    assert AUDIT_FILE.exists(), f"Audit file {AUDIT_FILE} missing."
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    reported_count = audit_data.get("source_file_count", 0)
    assert reported_count == len(actual_files), (
        f"Audit source file count ({reported_count}) does not match "
        f"actual disk inventory count ({len(actual_files)})"
    )


def test_every_source_file_accounted():
    """2. すべてのソースファイル（104件）が監査レポートで追跡・分類されているか検証"""
    actual_files = get_actual_corpus_files()
    actual_rel_paths = sorted([str(p.relative_to(CORPUS_DIR)) for p in actual_files])

    assert AUDIT_FILE.exists(), f"Audit output {AUDIT_FILE} missing."
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    included_in_audit = sorted(audit_data.get("included_source_files", []))
    assert actual_rel_paths == included_in_audit, (
        f"Mismatch between disk source files and audit included_source_files.\n"
        f"Disk count: {len(actual_rel_paths)}, Audit count: {len(included_in_audit)}"
    )


def test_file_count_discrepancy_calculation():
    """3. 報告ファイル数と実際のスキャン件数の乖離計算の数値整合性を検証"""
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    source_count = audit_data.get("source_file_count", 0)
    phase6_reported = audit_data.get("phase6_reported_file_count", 0)
    discrepancy = audit_data.get("file_count_discrepancy", 0)

    assert discrepancy == abs(source_count - phase6_reported), (
        f"File count discrepancy calculation error: expected {abs(source_count - phase6_reported)}, "
        f"got {discrepancy}"
    )


def test_provenance_and_path_resolution():
    """4. コーパスの絶対パス解決結果の保持を検証"""
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    resolved_path = audit_data.get("corpus_resolved_path")
    assert resolved_path == str(CORPUS_DIR), f"Resolved corpus path mismatch: {resolved_path} vs {CORPUS_DIR}"


def test_phase7a_inventory_verdict():
    """5. Phase 7A インベントリ修復状態の判定を検証"""
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    verdict = audit_data.get("verdict")
    assert verdict in {"PASS", "INVENTORY_REPAIRED"}, (
        f"Phase 7A Audit Verdict is {verdict}. Inventory repair incomplete."
    )