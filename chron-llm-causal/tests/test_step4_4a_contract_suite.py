import hashlib
import json
import re
from pathlib import Path

DATA_DIR = Path("data/delta1_normalized")
SUMMARY_FILE = Path("data/audit/delta1_structural_summary_v1.json")
TRACEABILITY_FILE = Path("data/audit/delta1_delta2_traceability_v1.json")

CANONICAL_SEP = "\x1f"


def compute_canonical_edge_id(
    component_id: str, from_id: str, to_id: str, relation: str
) -> str:
    """Canonical Edge ID の正則生成ロジック: E_{component_id}_{SHA256[:8]}"""
    material = f"{component_id}{CANONICAL_SEP}{from_id}{CANONICAL_SEP}{to_id}{CANONICAL_SEP}{relation}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:8]
    return f"E_{component_id}_{digest}"


def load_delta1_population():
    """Producer 処理をインポートせず、生 JSON ファイルから 3 母集団を独立走査"""
    nodes = []
    edges = []
    proposals = []

    for path in sorted(DATA_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        comp_id = data.get("component_id", path.stem)

        for n in data.get("nodes", []):
            nodes.append({"file": path.name, "component_id": comp_id, "data": n})
        for e in data.get("edges", []):
            edges.append({"file": path.name, "component_id": comp_id, "data": e})
        for p in data.get("proposals", []):
            proposals.append(
                {"file": path.name, "component_id": comp_id, "data": p}
            )

    return nodes, edges, proposals


# --- T1 to T3: Population Base Cardinality ---


def test_T1_graph_nodes_population_count():
    nodes, _, _ = load_delta1_population()
    assert len(nodes) == 340, f"T1 FAIL: expected 340 Graph Nodes, got {len(nodes)}"


def test_T2_graph_edges_population_count():
    _, edges, _ = load_delta1_population()
    assert (
        len(edges) == 312
    ), f"T2 FAIL: expected 312 Graph Edges, got {len(edges)}"


def test_T3_extraction_proposals_population_count():
    _, _, proposals = load_delta1_population()
    assert (
        len(proposals) == 46
    ), f"T3 FAIL: expected 46 Proposals, got {len(proposals)}"


# --- T4: Non-Aggregation Contract ---


def test_T4_population_non_aggregation():
    assert SUMMARY_FILE.exists(), "T4 FAIL: Summary file missing."
    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        summary = json.load(f)

    reported_nodes = summary.get("delta1_totals", {}).get("nodes")
    nodes, _, _ = load_delta1_population()
    expected_pure_nodes = len(nodes)  # 340

    assert reported_nodes == expected_pure_nodes, (
        f"Contract Violation (T4): Population aggregated! "
        f"Expected pure Graph Nodes {expected_pure_nodes}, but summary reported {reported_nodes}."
    )


# --- T5 & T6a/b/c: Edge Identity, Uniqueness & Content Derivation ---


def test_T5_canonical_edge_id_existence():
    _, edges, _ = load_delta1_population()
    missing_id_edges = [e for e in edges if not e["data"].get("id")]

    assert (
        len(missing_id_edges) == 0
    ), f"Contract Violation (T5): {len(missing_id_edges)} edges lack a canonical 'id'."


def test_T6a_edge_id_uniqueness():
    _, edges, _ = load_delta1_population()
    edge_ids = [e["data"].get("id") for e in edges]

    assert all(
        edge_ids
    ), "Contract Violation (T6a): One or more Edge IDs are missing/empty."
    assert len(edge_ids) == len(
        edges
    ), "Contract Violation (T6a): Edge ID count mismatch against population."
    assert len(set(edge_ids)) == len(
        edge_ids
    ), "Contract Violation (T6a): Duplicate Edge IDs detected."


def test_T6b_semantic_edge_identity_uniqueness():
    """T6b: 同一意味エッジ (component_id, from, to, relation) の重複拒絶"""
    _, edges, _ = load_delta1_population()
    semantic_keys = [
        (
            e["component_id"],
            e["data"].get("from"),
            e["data"].get("to"),
            e["data"].get("relation"),
        )
        for e in edges
    ]

    assert len(semantic_keys) == len(
        set(semantic_keys)
    ), "Contract Violation (T6b): Duplicate semantic edges detected in population."


def test_T6c_edge_id_content_derivation_and_order_independence():
    _, edges, _ = load_delta1_population()
    if not edges or not any(e["data"].get("id") for e in edges):
        assert (
            False
        ), "Contract Violation (T6c): Cannot test derivation; Edge IDs are absent."

    for e in edges:
        data = e["data"]
        actual_id = data.get("id")
        comp_id = e["component_id"]
        from_id = data.get("from", "")
        to_id = data.get("to", "")
        rel = data.get("relation", "")

        expected_id = compute_canonical_edge_id(
            comp_id, from_id, to_id, rel
        )
        assert (
            actual_id == expected_id
        ), f"Contract Violation (T6c): Edge ID '{actual_id}' mismatch with expected '{expected_id}'."


# --- T7 & T8: Synthetic Identity Audit Across ALL Identity Fields ---


def _extract_identity_field_values(obj):
    """Traceability 内の全構造から ID 参照プロパティを再帰抽出"""
    id_values = []
    target_keys = {
        "source_delta1_id",
        "source_original_id",
        "source_delta1_node_ids",
        "source_delta1_edge_ids",
        "contributing_delta1_nodes",
        "contributing_delta1_edges",
        "id",
    }
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in target_keys:
                if isinstance(v, str):
                    id_values.append(v)
                elif isinstance(v, list):
                    id_values.extend([item for item in v if isinstance(item, str)])
            else:
                id_values.extend(_extract_identity_field_values(v))
    elif isinstance(obj, list):
        for item in obj:
            id_values.extend(_extract_identity_field_values(item))
    return id_values


def test_T7_rejection_of_synthetic_edge_ids():
    with open(TRACEABILITY_FILE, "r", encoding="utf-8") as f:
        trace = json.load(f)

    all_ids = _extract_identity_field_values(trace)
    synthetic = [s for s in all_ids if re.match(r"^D1_E_\d+$", s)]

    assert len(synthetic) == 0, (
        f"Contract Violation (T7): Found {len(synthetic)} synthetic edge identity references (D1_E_*) "
        f"across Traceability fields."
    )


def test_T8_rejection_of_synthetic_node_ids():
    with open(TRACEABILITY_FILE, "r", encoding="utf-8") as f:
        trace = json.load(f)

    all_ids = _extract_identity_field_values(trace)
    synthetic = [s for s in all_ids if re.match(r"^D1_N_\d+$", s)]

    assert len(synthetic) == 0, (
        f"Contract Violation (T8): Found {len(synthetic)} synthetic node identity references (D1_N_*) "
        f"across Traceability fields."
    )


# --- T9, T10a, T10b: Reconciliation Semantics & Error Code Separation ---


def test_T9_phantom_provenance_detection():
    nodes, edges, _ = load_delta1_population()
    gt_node_ids = {n["data"].get("id") for n in nodes if n["data"].get("id")}
    gt_edge_ids = {e["data"].get("id") for e in edges if e["data"].get("id")}

    with open(TRACEABILITY_FILE, "r", encoding="utf-8") as f:
        trace = json.load(f)

    # Claim - GT => PHANTOM_REF
    phantom_nodes = [
        m.get("source_original_id")
        for m in trace.get("node_mappings", [])
        if m.get("source_original_id") not in gt_node_ids
    ]
    phantom_edges = [
        m.get("source_original_id")
        for m in trace.get("edge_mappings", [])
        if m.get("source_original_id") not in gt_edge_ids
    ]

    assert len(phantom_nodes) == 0 and len(phantom_edges) == 0, (
        f"Contract Violation (T9: PHANTOM_REF): Traceability references missing IDs. "
        f"Missing Nodes: {len(phantom_nodes)}, Missing Edges: {len(phantom_edges)}"
    )


def test_T10a_gt_identity_cardinality_completeness():
    """T10a: GT 側のノードおよびエッジに正則 ID が欠損なく埋まっているか (IDENTITY_CARDINALITY_VIOLATION)"""
    nodes, edges, _ = load_delta1_population()

    gt_node_ids = [n["data"].get("id") for n in nodes if n["data"].get("id")]
    gt_edge_ids = [e["data"].get("id") for e in edges if e["data"].get("id")]

    assert len(gt_node_ids) == len(
        nodes
    ), f"Contract Violation (T10a: IDENTITY_CARDINALITY_VIOLATION): GT Node ID missing ({len(nodes) - len(gt_node_ids)} items)."
    assert len(gt_edge_ids) == len(
        edges
    ), f"Contract Violation (T10a: IDENTITY_CARDINALITY_VIOLATION): GT Edge ID missing ({len(edges) - len(gt_edge_ids)} items)."


def test_T10b_untracked_population_detection():
    """T10b: GT - Claim => UNTRACKED Population 検証"""
    nodes, edges, _ = load_delta1_population()

    gt_node_ids = set(n["data"].get("id") for n in nodes if n["data"].get("id"))
    gt_edge_ids = set(e["data"].get("id") for e in edges if e["data"].get("id"))

    with open(TRACEABILITY_FILE, "r", encoding="utf-8") as f:
        trace = json.load(f)

    tracked_node_claims = [
        m.get("source_original_id") for m in trace.get("node_mappings", [])
    ]
    tracked_edge_claims = [
        m.get("source_original_id") for m in trace.get("edge_mappings", [])
    ]

    # Claim 重複の検知
    assert len(tracked_node_claims) == len(
        set(tracked_node_claims)
    ), "Contract Violation (T10b: DUPLICATE_CLAIM): Node claims contain duplicates."
    assert len(tracked_edge_claims) == len(
        set(tracked_edge_claims)
    ), "Contract Violation (T10b: DUPLICATE_CLAIM): Edge claims contain duplicates."

    set_node_claims = set(tracked_node_claims)
    set_edge_claims = set(tracked_edge_claims)

    untracked_nodes = gt_node_ids - set_node_claims
    untracked_edges = gt_edge_ids - set_edge_claims

    assert len(untracked_nodes) == 0 and len(untracked_edges) == 0, (
        f"Contract Violation (T10b: UNTRACKED): Untracked population detected. "
        f"Untracked Nodes: {len(untracked_nodes)}, Untracked Edges: {len(untracked_edges)}"
    )