"""
Independent Scanner Verification Suite (Step 4-4-C - Reinforced)
C-T1a 〜 C-T18 の独立性・物理全数観測・二層分離検証
"""

import ast
import json
from pathlib import Path
import pytest

from causal_kernel.audit.independent_delta1_scanner import (
    IndependentDelta1Scanner,
    Delta1GroundTruth,
)

NORMALIZED_DIR = Path("data/delta1_normalized")
SCANNER_MODULE_PATH = Path("src/causal_kernel/audit/independent_delta1_scanner.py")


# C-T1a: AST 静的解析による Producer モジュールの import 排除証明
def test_ct1a_static_import_analysis():
    source = SCANNER_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = {"extract_component", "normalizer", "causal_extract_component"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden_modules, f"Forbidden import found: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert node.module not in forbidden_modules, f"Forbidden import-from found: {node.module}"


# C-T1b: AST 静的解析による ID 生成関数およびハッシュシンボルの非存在証明
def test_ct1b_static_symbol_analysis():
    source = SCANNER_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_names = {"generate_canonical_edge_id", "sha256", "md5", "hashlib"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in forbidden_names, f"Forbidden symbol referenced: {node.id}"
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_names, f"Forbidden attribute referenced: {node.attr}"


# C-T2: Node の Layer A (物理) / Layer B (Canonical) 分離検証
def test_ct2_nodes_physical_and_canonical():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    gt, summary = scanner.scan()
    assert gt.physical_node_count == 340
    assert len(gt.canonical_nodes) == 321  # 重複・不適格排除後の Canonical ノード数
    assert summary.nodes["total_physical"] == 340
    assert summary.nodes["canonical"] == 321
    assert summary.nodes["rejected"] == 19


# C-T3: 312 Edge の Layer A/B 同時検証
def test_ct3_edges_physical_and_canonical():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    gt, summary = scanner.scan()
    assert gt.physical_edge_count == 312
    assert len(gt.canonical_edges) == 312
    assert summary.edges["total_physical"] == 312
    assert summary.edges["canonical"] == 312


# C-T4: Proposal の分離検証
def test_ct4_proposals_count():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    gt, summary = scanner.scan()
    assert gt.physical_proposal_count == 46
    assert len(gt.observed_proposals) == 46
    assert summary.physical_population["proposals"] == 46


# C-T5: component_id 補完廃止の検証 (Missing component_id -> SCHEMA_VIOLATION)
def test_ct5_missing_component_id_triggers_schema_violation(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "nodes": [],
            "edges": [],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    _, summary = scanner.scan()
    assert summary.status == "FAIL"
    assert any(e["type"] == "SCHEMA_VIOLATION" and "component_id" in e["message"] for e in summary.errors)


# C-T6: 物理カウント保持と Canonical 昇格拒絶の分離検証 (Missing Edge ID)
def test_ct6_physical_count_retained_on_rejected_edge(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [{"id": "N1", "origin": "EXPLICIT_NODE"}],
            "edges": [
                {"id": "E1", "from": "N1", "to": "N1", "relation": "r"},
                {"from": "N1", "to": "N1", "relation": "r"}  # Missing ID
            ],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_edge_count == 2
    assert len(gt.canonical_edges) == 1  # 物理2、Canonical 1
    assert summary.edges["rejected"] == 1
    assert summary.status == "FAIL"


# C-T7: Missing Node ID での物理カウント保持と Canonical 昇格拒絶検証
def test_ct7_physical_count_retained_on_rejected_node(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [
                {"id": "N1", "origin": "EXPLICIT_NODE"},
                {"origin": "EXPLICIT_NODE"}  # Missing ID
            ],
            "edges": [],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_node_count == 2
    assert len(gt.canonical_nodes) == 1
    assert summary.nodes["rejected"] == 1


# C-T8: Missing proposals フィールドで SCHEMA_VIOLATION
def test_ct8_missing_proposals_field_schema_violation(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [],
            "edges": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    _, summary = scanner.scan()
    assert summary.status == "FAIL"
    assert any("proposals" in e["message"] for e in summary.errors)


# C-T9: 非文字列型 from/to/relation で昇格拒絶
def test_ct9_non_string_edge_struct_rejected(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [],
            "edges": [{"id": "E1", "from": 123, "to": "N2", "relation": "r"}],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_edge_count == 1
    assert len(gt.canonical_edges) == 0
    assert summary.status == "FAIL"


# C-T10: Duplicate Edge ID の検証
def test_ct10_duplicate_edge_id_rejected(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [],
            "edges": [
                {"id": "E1", "from": "A", "to": "B", "relation": "r1"},
                {"id": "E1", "from": "C", "to": "D", "relation": "r2"}
            ],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_edge_count == 2
    assert len(gt.canonical_edges) == 1
    assert summary.identity["duplicate_edge_ids"] == 1


# C-T11: Semantic Duplicate の検証
def test_ct11_semantic_duplicate_rejected(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [],
            "edges": [
                {"id": "E1", "from": "A", "to": "B", "relation": "r1"},
                {"id": "E2", "from": "A", "to": "B", "relation": "r1"}
            ],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_edge_count == 2
    assert len(gt.canonical_edges) == 1
    assert summary.identity["duplicate_semantic_edges"] == 1


# C-T12: Synthetic Node の保持
def test_ct12_synthetic_node_retained(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [{"id": "N1", "origin": "SYNTHETIC_ENDPOINT_NODE"}],
            "edges": [],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert len(gt.canonical_nodes) == 1
    assert summary.nodes["synthetic_endpoint"] == 1


# C-T13: Unknown Origin の拒絶
def test_ct13_unknown_origin_rejected(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [{"id": "N1", "origin": "INVALID_ORIGIN"}],
            "edges": [],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_node_count == 1
    assert len(gt.canonical_nodes) == 0
    assert summary.status == "FAIL"


# C-T14: 非リスト型 nodes の SCHEMA_VIOLATION
def test_ct14_non_list_nodes_schema_violation(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": "not_a_list",
            "edges": [],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    _, summary = scanner.scan()
    assert summary.status == "FAIL"
    assert any("nodes" in e["message"] for e in summary.errors)


# C-T15: 非リスト型 edges の SCHEMA_VIOLATION
def test_ct15_non_list_edges_schema_violation(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [],
            "edges": {},
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    _, summary = scanner.scan()
    assert summary.status == "FAIL"
    assert any("edges" in e["message"] for e in summary.errors)


# C-T16: 空文字列 `id` での拒絶
def test_ct16_empty_string_ids_rejected(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [{"id": "  ", "origin": "EXPLICIT_NODE"}],
            "edges": [],
            "proposals": []
        }),
        encoding="utf-8"
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_node_count == 1
    assert len(gt.canonical_nodes) == 0
    assert summary.status == "FAIL"


# C-T17: 単体スタンドアロン実行確認
def test_ct17_scanner_standalone():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    gt, summary = scanner.scan()
    # 物理全数 340, 312, 46 が正しく検出されていることを独立検証
    assert gt.physical_node_count == 340
    assert gt.physical_edge_count == 312
    assert gt.physical_proposal_count == 46


# C-T18: サマリー項目の完全性チェック
def test_ct18_summary_metrics_completeness():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    _, summary = scanner.scan()
    assert "physical_population" in summary.__dict__
    assert "canonical_population" in summary.__dict__
    assert summary.nodes["rejected"] == 19
    assert summary.edges["rejected"] == 0