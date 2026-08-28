"""
Independent Scanner Verification Suite (Step 4-4-C - Fully Reinforced)
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

# C-T1a / C-T1b 用の禁止モジュールおよびプレフィックス定義
FORBIDDEN_IMPORT_PREFIXES = (
    "causal_kernel.extract_component",
    "causal_kernel.normalizer",
    "causal_kernel.causal_extract_component",
    "causal_kernel.extractor",
    "hashlib",
)

FORBIDDEN_SYMBOLS = {
    "generate_canonical_edge_id",
    "sha256",
    "md5",
    "hashlib",
}


def is_forbidden_module(module_name: str) -> bool:
    """完全一致またはドット区切りのプレフィックス一致で禁止モジュールかを判定"""
    return any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in FORBIDDEN_IMPORT_PREFIXES
    )


# C-T1a: AST 静的解析による Producer モジュールおよび禁止ライブラリの import 排除証明（完全パス・間接import検出対応）
def test_ct1a_static_import_analysis():
    source = SCANNER_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not is_forbidden_module(
                    alias.name
                ), f"Forbidden import found: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not is_forbidden_module(
                    node.module
                ), f"Forbidden import-from found: {node.module}"
            for alias in node.names:
                assert (
                    alias.name not in FORBIDDEN_SYMBOLS
                ), f"Forbidden symbol imported from module: {alias.name}"


# C-T1b: AST 静的解析による既知の禁止シンボルおよび静的に検出可能な動的参照パターンの排除
def test_ct1b_static_symbol_analysis():
    source = SCANNER_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        # 変数名・関数名
        if isinstance(node, ast.Name):
            assert (
                node.id not in FORBIDDEN_SYMBOLS
            ), f"Forbidden symbol referenced: {node.id}"

        # 属性参照 (obj.sha256 など)
        elif isinstance(node, ast.Attribute):
            assert (
                node.attr not in FORBIDDEN_SYMBOLS
            ), f"Forbidden attribute referenced: {node.attr}"

        # 動的呼び出し (__import__('hashlib'), getattr(obj, 'generate_canonical_edge_id'))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "__import__" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        assert not is_forbidden_module(
                            arg.value
                        ), f"Dynamic __import__ of forbidden module: {arg.value}"
                elif node.func.id == "getattr" and len(node.args) >= 2:
                    arg = node.args[1]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        assert (
                            arg.value not in FORBIDDEN_SYMBOLS
                        ), f"Dynamic getattr of forbidden symbol: {arg.value}"


# C-T2: Node の Layer A (物理) / Layer B (Canonical) 分離と人口保存則の検証
def test_ct2_nodes_physical_and_canonical():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    gt, summary = scanner.scan()

    # 物理数の検証
    assert gt.physical_node_count == 340
    assert summary.nodes["total_physical"] == 340

    # Canonical数とRejection数の検証
    assert len(gt.canonical_nodes) == 321
    assert summary.nodes["canonical"] == 321
    assert summary.nodes["rejected"] == 19

    # 人口保存則（Population Conservation）: Physical = Canonical + Rejected
    assert (
        len(gt.canonical_nodes) + summary.nodes["rejected"]
        == gt.physical_node_count
    )


# C-T3: Edge の Layer A/B 同時検証と人口保存則の検証
def test_ct3_edges_physical_and_canonical():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    gt, summary = scanner.scan()

    # 物理数の検証
    assert gt.physical_edge_count == 312
    assert summary.edges["total_physical"] == 312

    # Canonical数とRejection数の検証
    assert len(gt.canonical_edges) == 312
    assert summary.edges["canonical"] == 312
    assert summary.edges["rejected"] == 0

    # 人口保存則（Population Conservation）: Physical = Canonical + Rejected
    assert (
        len(gt.canonical_edges) + summary.edges["rejected"]
        == gt.physical_edge_count
    )


# C-T4: Proposal の分離検証と人口保存則
def test_ct4_proposals_count():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    gt, summary = scanner.scan()

    # 物理観測件数の一致
    assert gt.physical_proposal_count == 46
    assert summary.physical_population["proposals"] == 46

    # 1:1 保存則の明示 (Physical Count = Observed Records)
    assert len(gt.observed_proposals) == gt.physical_proposal_count


# C-T5: component_id 欠落時でも物理カウントを完全保持し、Canonical 昇格のみ拒絶することを検証
def test_ct5_missing_component_id_triggers_schema_violation(tmp_path):
    bad_file = tmp_path / "comp_missing_id.json"
    bad_file.write_text(
        json.dumps({
            "nodes": [{"id": "N1", "origin": "EXPLICIT_NODE"}],
            "edges": [
                {"id": "E1", "from": "N1", "to": "N1", "relation": "r1"}
            ],
            "proposals": [{"id": "P1", "type": "test"}],
        }),
        encoding="utf-8",
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()

    # SCHEMA_VIOLATION が発生していること
    assert summary.status == "FAIL"
    assert any(
        e["type"] == "SCHEMA_VIOLATION" and "component_id" in e["message"]
        for e in summary.errors
    )

    # Layer A: 物理観測事実（不変）
    assert gt.physical_node_count == 1
    assert gt.physical_edge_count == 1
    assert gt.physical_proposal_count == 1

    # Layer B: componentレベルの不正によりCanonical昇格拒絶
    assert len(gt.canonical_nodes) == 0
    assert len(gt.canonical_edges) == 0

    # Proposalは物理的に観測された記録として保持される
    assert len(gt.observed_proposals) == 1


# C-T6: 物理カウント保持と Canonical 昇格拒絶の分離検証 (Missing Edge ID)
def test_ct6_physical_count_retained_on_rejected_edge(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [{"id": "N1", "origin": "EXPLICIT_NODE"}],
            "edges": [
                {"id": "E1", "from": "N1", "to": "N1", "relation": "r"},
                {"from": "N1", "to": "N1", "relation": "r"},  # Missing ID
            ],
            "proposals": [],
        }),
        encoding="utf-8",
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()
    assert gt.physical_edge_count == 2
    assert len(gt.canonical_edges) == 1
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
                {"origin": "EXPLICIT_NODE"},  # Missing ID
            ],
            "edges": [],
            "proposals": [],
        }),
        encoding="utf-8",
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
            "edges": [],
        }),
        encoding="utf-8",
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    _, summary = scanner.scan()
    assert summary.status == "FAIL"
    assert any(
        e["type"] == "SCHEMA_VIOLATION" and "proposals" in e["message"]
        for e in summary.errors
    )


# C-T9: 非文字列型 from/to/relation で昇格拒絶（型パターン網羅検証）
@pytest.mark.parametrize(
    "invalid_val",
    [123, True, None, [], {"key": "val"}],
)
@pytest.mark.parametrize("field", ["from", "to", "relation"])
def test_ct9_non_string_edge_struct_rejected(tmp_path, invalid_val, field):
    edge_data = {"id": "E1", "from": "N1", "to": "N2", "relation": "r1"}
    edge_data[field] = invalid_val

    bad_file = tmp_path / f"comp_{field}.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [],
            "edges": [edge_data],
            "proposals": [],
        }),
        encoding="utf-8",
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()

    # 物理的には1本観測
    assert gt.physical_edge_count == 1
    # Canonical昇格は拒絶
    assert len(gt.canonical_edges) == 0
    assert summary.status == "FAIL"
    assert any(
        e["type"] in ("SCHEMA_VIOLATION", "TYPE_VIOLATION")
        for e in summary.errors
    )


# C-T10: Duplicate Edge ID の検証
def test_ct10_duplicate_edge_id_rejected(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [],
            "edges": [
                {"id": "E1", "from": "A", "to": "B", "relation": "r1"},
                {"id": "E1", "from": "C", "to": "D", "relation": "r2"},
            ],
            "proposals": [],
        }),
        encoding="utf-8",
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
                {"id": "E2", "from": "A", "to": "B", "relation": "r1"},
            ],
            "proposals": [],
        }),
        encoding="utf-8",
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
            "proposals": [],
        }),
        encoding="utf-8",
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
            "proposals": [],
        }),
        encoding="utf-8",
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
            "proposals": [],
        }),
        encoding="utf-8",
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
            "proposals": [],
        }),
        encoding="utf-8",
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    _, summary = scanner.scan()
    assert summary.status == "FAIL"
    assert any("edges" in e["message"] for e in summary.errors)


# C-T16: 空白文字列 `id`（"  "）での Canonical 昇格拒絶と物理保持
def test_ct16_empty_string_ids_rejected(tmp_path):
    bad_file = tmp_path / "comp.json"
    bad_file.write_text(
        json.dumps({
            "component_id": "c-001",
            "nodes": [{"id": "   ", "origin": "EXPLICIT_NODE"}],
            "edges": [],
            "proposals": [],
        }),
        encoding="utf-8",
    )

    scanner = IndependentDelta1Scanner(tmp_path)
    gt, summary = scanner.scan()

    # 物理的にはカウント（観測事実）
    assert gt.physical_node_count == 1
    # 空白IDは不適合のため Canonical 昇格拒絶
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


# C-T18: サマリー項目の完全性とインターフェース検証（hasattrベース）
def test_ct18_summary_metrics_completeness():
    scanner = IndependentDelta1Scanner(NORMALIZED_DIR)
    _, summary = scanner.scan()

    # オブジェクトの公開属性としてインターフェース契約を検証
    assert hasattr(summary, "physical_population")
    assert hasattr(summary, "canonical_population")
    assert summary.nodes["rejected"] == 19
    assert summary.edges["rejected"] == 0