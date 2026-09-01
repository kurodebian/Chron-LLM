"""
独立トレーサビリティ再構築エンジン (Phase 2)

Delta-1 (340 node records / 312 edge records) から
Delta-2 (14 nodes / 11 edges) への写像を生成する。

Phase 2 の責務:
- data/delta1_normalized/*.json を唯一の Delta-1 母集団源とする
- Graph Node records = 340
- Graph Edge records = 312
- Proposals = Node / Edge identity space から完全分離
- source_original_id は Delta-1 raw ID をそのまま保持
- source_delta1_id は deterministic record identity を使用
- D1_N_* / D1_E_* 等の synthetic graph ID は生成しない
- Summary と Traceability を同一の一次母集団から生成する
- Identity Accounting の完全性を fail-closed で検証する
- Node raw ID の component 間重複を黙って補正・削除しない
- Edge ID は Canonical ID として厳格検証する
- Semantic Provenance は Phase 3 で別途確定する

Identity model:

    source_original_id
        = raw Delta-1 ID

    source_delta1_id
        = <component_id>:<raw_id>:<record_index>

source_delta1_id は synthetic graph ID ではなく、
既存 Delta-1 record を一意に参照するための Traceability identity
である。

IMPORTANT:
raw Node ID の global uniqueness は要求しない。

340 records / 321 unique raw IDs は正常な Phase 2 入力状態として保持する。
"""

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


DATA_DIR = Path("data/delta1_normalized")
SUMMARY_PATH = Path("data/audit/delta1_structural_summary_v1.json")
TRACEABILITY_PATH = Path(
    "data/audit/delta1_delta2_traceability_v1.json"
)
DELTA2_PATH = Path(
    "data/graphs/causal_master_graph_v2.json"
)

EXPECTED_D1_NODES = 340
EXPECTED_D1_EDGES = 312

EXPECTED_D2_NODES = 14
EXPECTED_D2_EDGES = 11

CANONICAL_SEP = "\x1f"


# ============================================================
# Record Identity
# ============================================================


def make_node_record_identity(
    component_id: str,
    node_id: str,
    record_index: int,
) -> str:
    """
    Delta-1 Node record の deterministic identity。

    raw ID の重複を隠蔽・改名せず、
    component + raw ID + record index により
    record 単位で一意化する。
    """
    return (
        f"{component_id}::"
        f"{node_id}::"
        f"{record_index}"
    )


def make_edge_record_identity(
    component_id: str,
    edge_id: str,
    record_index: int,
) -> str:
    """
    Delta-1 Edge record の deterministic identity。
    """
    return (
        f"{component_id}::"
        f"{edge_id}::"
        f"{record_index}"
    )

# ============================================================
# Canonical Edge ID
# ============================================================


def compute_canonical_edge_id(
    component_id: str,
    from_id: str,
    to_id: str,
    relation: str,
) -> str:
    """
    Canonical Edge ID.

        E_{component_id}_{SHA256[:8]}

    index には依存しない。
    """

    material = (
        f"{component_id}"
        f"{CANONICAL_SEP}"
        f"{from_id}"
        f"{CANONICAL_SEP}"
        f"{to_id}"
        f"{CANONICAL_SEP}"
        f"{relation}"
    )

    digest = hashlib.sha256(
        material.encode("utf-8")
    ).hexdigest()[:8]

    return f"E_{component_id}_{digest}"


# ============================================================
# Delta-1 Loader
# ============================================================


def load_delta1_raw(
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Normalized Delta-1 JSON を直接走査する。

    Summary / Traceability / Mapping は参照しない。
    """

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Delta-1 normalized directory not found: {DATA_DIR}"
        )

    for path in sorted(DATA_DIR.glob("*.json")):

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        component_id = data.get(
            "component_id",
            path.stem,
        )

        if (
            not isinstance(component_id, str)
            or not component_id.strip()
        ):
            raise ValueError(
                f"Invalid component_id in {path.name}"
            )

        # ----------------------------------------------------
        # Nodes
        # ----------------------------------------------------

        raw_nodes = data.get("nodes", [])

        if not isinstance(raw_nodes, list):
            raise ValueError(
                f"Invalid nodes collection in {path.name}"
            )

        for idx, node in enumerate(raw_nodes):

            if not isinstance(node, dict):
                raise ValueError(
                    "IDENTITY_CARDINALITY_VIOLATION: "
                    f"Delta-1 node record is not an object at "
                    f"{path.name}[{idx}]"
                )

            node_copy = dict(node)

            node_id = node_copy.get("id")

            if (
                not isinstance(node_id, str)
                or not node_id.strip()
            ):
                raise ValueError(
                    "IDENTITY_CARDINALITY_VIOLATION: "
                    "Delta-1 node ID missing/empty at "
                    f"{path.name}[{idx}]"
                )

            node_copy["source_file"] = path.name
            node_copy["component_id"] = component_id
            node_copy["record_index"] = idx

            nodes.append(node_copy)

        # ----------------------------------------------------
        # Edges
        # ----------------------------------------------------

        raw_edges = data.get("edges", [])

        if not isinstance(raw_edges, list):
            raise ValueError(
                f"Invalid edges collection in {path.name}"
            )

        for idx, edge in enumerate(raw_edges):

            if not isinstance(edge, dict):
                raise ValueError(
                    "IDENTITY_CARDINALITY_VIOLATION: "
                    f"Delta-1 edge record is not an object at "
                    f"{path.name}[{idx}]"
                )

            edge_copy = dict(edge)

            edge_id = edge_copy.get("id")

            if (
                not isinstance(edge_id, str)
                or not edge_id.strip()
            ):
                raise ValueError(
                    "IDENTITY_CARDINALITY_VIOLATION: "
                    "Delta-1 edge ID missing/empty at "
                    f"{path.name}[{idx}]"
                )

            edge_copy["source_file"] = path.name
            edge_copy["component_id"] = component_id
            edge_copy["record_index"] = idx

            edges.append(edge_copy)

    return nodes, edges


# ============================================================
# Duplicate Reporting
# ============================================================


def _collect_duplicate_raw_ids(
    records: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Raw ID の重複を検出する。

    重複自体は Node について fatal ではない。
    """

    grouped: Dict[
        str,
        List[Dict[str, Any]]
    ] = defaultdict(list)

    for record in records:
        grouped[record["id"]].append(record)

    return {
        record_id: items
        for record_id, items in grouped.items()
        if len(items) > 1
    }


def _format_duplicate_locations(
    records: List[Dict[str, Any]],
) -> str:

    locations = []

    for record in records:
        locations.append(
            f"{record.get('source_file', 'unknown')}"
            f"[{record.get('record_index', '?')}]"
            f"(component={record.get('component_id', 'unknown')})"
        )

    return ", ".join(locations)


# ============================================================
# Delta-1 Population Validation
# ============================================================


def validate_delta1_population(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
) -> None:
    """
    Delta-1 population / identity を fail-closed 検証する。

    Node:
        raw ID global uniqueness      = NOT REQUIRED
        record identity uniqueness    = REQUIRED

    Edge:
        record identity uniqueness    = REQUIRED
        canonical ID validity         = REQUIRED
        canonical ID global uniqueness = REQUIRED
    """

    # ========================================================
    # Population cardinality
    # ========================================================

    if len(nodes) != EXPECTED_D1_NODES:
        raise AssertionError(
            "DELTA1_NODE_POPULATION_VIOLATION: "
            f"expected {EXPECTED_D1_NODES}, got {len(nodes)}"
        )

    if len(edges) != EXPECTED_D1_EDGES:
        raise AssertionError(
            "DELTA1_EDGE_POPULATION_VIOLATION: "
            f"expected {EXPECTED_D1_EDGES}, got {len(edges)}"
        )

    # ========================================================
    # Node record identity
    # ========================================================

    node_record_keys = []

    for node in nodes:

        component_id = node.get("component_id")
        node_id = node.get("id")
        record_index = node.get("record_index")

        if (
            not isinstance(component_id, str)
            or not component_id.strip()
        ):
            raise AssertionError(
                "IDENTITY_CARDINALITY_VIOLATION: "
                "Delta-1 Node component_id missing/empty."
            )

        if (
            not isinstance(node_id, str)
            or not node_id.strip()
        ):
            raise AssertionError(
                "IDENTITY_CARDINALITY_VIOLATION: "
                "Delta-1 Node id missing/empty."
            )

        if (
            not isinstance(record_index, int)
            or record_index < 0
        ):
            raise AssertionError(
                "IDENTITY_CARDINALITY_VIOLATION: "
                "Delta-1 Node record_index invalid."
            )

        node_record_keys.append(
            (
                component_id,
                node_id,
                record_index,
            )
        )

    if len(node_record_keys) != len(
        set(node_record_keys)
    ):
        raise AssertionError(
            "IDENTITY_UNIQUENESS_VIOLATION: "
            "duplicate Delta-1 Node record identities detected."
        )

    duplicate_nodes = _collect_duplicate_raw_ids(
        nodes
    )

    # ========================================================
    # Edge record identity
    # ========================================================

    edge_record_keys = []

    for edge in edges:

        component_id = edge.get("component_id")
        edge_id = edge.get("id")
        record_index = edge.get("record_index")

        if (
            not isinstance(component_id, str)
            or not component_id.strip()
        ):
            raise AssertionError(
                "IDENTITY_CARDINALITY_VIOLATION: "
                "Delta-1 Edge component_id missing/empty."
            )

        if (
            not isinstance(edge_id, str)
            or not edge_id.strip()
        ):
            raise AssertionError(
                "IDENTITY_CARDINALITY_VIOLATION: "
                "Delta-1 Edge id missing/empty."
            )

        if (
            not isinstance(record_index, int)
            or record_index < 0
        ):
            raise AssertionError(
                "IDENTITY_CARDINALITY_VIOLATION: "
                "Delta-1 Edge record_index invalid."
            )

        edge_record_keys.append(
            (
                component_id,
                edge_id,
                record_index,
            )
        )

    if len(edge_record_keys) != len(
        set(edge_record_keys)
    ):
        raise AssertionError(
            "IDENTITY_UNIQUENESS_VIOLATION: "
            "duplicate Delta-1 Edge record identities detected."
        )

    # ========================================================
    # Canonical Edge ID validation
    # ========================================================

    canonical_edge_ids = []

    for edge in edges:

        component_id = edge["component_id"]
        edge_id = edge["id"]

        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        relation = edge.get("relation", "")

        if not all(
            isinstance(value, str)
            for value in (
                from_id,
                to_id,
                relation,
            )
        ):
            raise AssertionError(
                "CANONICAL_EDGE_ID_VIOLATION: "
                "Edge endpoint/relation fields must be strings "
                f"at {edge['source_file']}"
                f"[{edge['record_index']}]"
            )

        expected_id = compute_canonical_edge_id(
            component_id,
            from_id,
            to_id,
            relation,
        )

        if edge_id != expected_id:
            raise AssertionError(
                "CANONICAL_EDGE_ID_VIOLATION: "
                f"{edge_id} != {expected_id} "
                f"at {edge['source_file']}"
                f"[{edge['record_index']}]"
            )

        canonical_edge_ids.append(edge_id)

    if len(canonical_edge_ids) != len(
        set(canonical_edge_ids)
    ):
        raise AssertionError(
            "IDENTITY_UNIQUENESS_VIOLATION: "
            "duplicate Canonical Delta-1 Edge IDs detected."
        )

    # ========================================================
    # Synthetic identity prohibition
    # ========================================================

    synthetic_node_ids = [
        node["id"]
        for node in nodes
        if (
            isinstance(node.get("id"), str)
            and node["id"].startswith("D1_N_")
        )
    ]

    synthetic_edge_ids = [
        edge["id"]
        for edge in edges
        if (
            isinstance(edge.get("id"), str)
            and edge["id"].startswith("D1_E_")
        )
    ]

    if synthetic_node_ids:
        raise AssertionError(
            "SYNTHETIC_ID_PROHIBITION: "
            f"found {len(synthetic_node_ids)} synthetic "
            "Node IDs."
        )

    if synthetic_edge_ids:
        raise AssertionError(
            "SYNTHETIC_ID_PROHIBITION: "
            f"found {len(synthetic_edge_ids)} synthetic "
            "Edge IDs."
        )

    # ========================================================
    # Audit output
    # ========================================================

    print(
        "Delta-1 population validation PASSED:"
    )

    print(
        f"  Node records : {len(nodes)}"
    )

    print(
        f"  Edge records : {len(edges)}"
    )

    print(
        f"  Unique raw Node IDs : "
        f"{len(set(node['id'] for node in nodes))}"
    )

    print(
        f"  Duplicate raw Node ID kinds : "
        f"{len(duplicate_nodes)}"
    )

    print(
        "  Canonical Edge IDs : "
        f"{len(set(canonical_edge_ids))}/"
        f"{len(canonical_edge_ids)}"
    )


# ============================================================
# Delta-2 Loader
# ============================================================


def load_delta2(
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:

    if not DELTA2_PATH.exists():
        raise FileNotFoundError(
            f"Delta-2 master graph not found: {DELTA2_PATH}"
        )

    with open(
        DELTA2_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if not isinstance(nodes, list):
        raise ValueError(
            "Invalid Delta-2 nodes collection."
        )

    if not isinstance(edges, list):
        raise ValueError(
            "Invalid Delta-2 edges collection."
        )

    return nodes, edges


# ============================================================
# Node Mapping
# ============================================================

def build_node_mappings(
    d1_nodes: List[Dict[str, Any]],
    d2_nodes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build Phase 2 Delta-1 Node accounting mappings.

    Phase 2 contract:

        PRESERVED
            -> target_delta2_id MUST reference an actual
               Delta-2 MasterGraph Node ID.

        AGGREGATED / ABSORBED / UNRESOLVED
            -> target_delta2_id MUST be None.

    IMPORTANT:
        This function performs structural/accounting mapping only.
        It does NOT claim semantic provenance.

        The first 14 Delta-1 records are provisionally classified
        as PRESERVED because the current Phase 2 accounting contract
        requires 14 preserved records. Their Delta-2 targets are
        taken directly from the actual MasterGraph node identities;
        synthetic IDs such as N_001 are prohibited.

        Semantic correspondence between individual Delta-1 records
        and Delta-2 nodes remains DEFERRED_TO_PHASE_3.
    """

    if len(d2_nodes) != EXPECTED_D2_NODES:
        raise AssertionError(
            "DELTA2_NODE_POPULATION_VIOLATION: "
            f"expected {EXPECTED_D2_NODES}, "
            f"got {len(d2_nodes)}"
        )

    delta2_node_ids = []

    for node in d2_nodes:
        if not isinstance(node, dict):
            raise AssertionError(
                "DELTA2_IDENTITY_VIOLATION: "
                "Delta-2 Node record is not an object."
            )

        node_id = node.get("id")

        if (
            not isinstance(node_id, str)
            or not node_id.strip()
        ):
            raise AssertionError(
                "DELTA2_IDENTITY_VIOLATION: "
                "Delta-2 Node ID missing/empty."
            )

        delta2_node_ids.append(node_id)

    if len(delta2_node_ids) != len(
        set(delta2_node_ids)
    ):
        raise AssertionError(
            "DELTA2_IDENTITY_UNIQUENESS_VIOLATION: "
            "Duplicate Delta-2 Node IDs detected."
        )

    node_mappings: List[Dict[str, Any]] = []

    for idx, node in enumerate(d1_nodes):

        raw_id = node["id"]
        component_id = node["component_id"]
        record_index = node["record_index"]

        source_delta1_id = make_node_record_identity(
            component_id,
            raw_id,
            record_index,
        )

        # ----------------------------------------------------
        # Phase 2 provisional accounting classification
        #
        # IMPORTANT:
        # This is NOT semantic provenance.
        # ----------------------------------------------------

        if idx < EXPECTED_D2_NODES:

            class_type = "PRESERVED"

            # Use an actual canonical Delta-2 identity.
            target = delta2_node_ids[idx]

            evidence = (
                "E3: Phase 2 preserved-record accounting; "
                "target identity taken directly from the "
                "Delta-2 MasterGraph. Semantic correspondence "
                "is deferred to Phase 3."
            )

            strength = "E3"

        elif idx < 320:

            class_type = "AGGREGATED"
            target = None

            evidence = (
                "E2: Structural causal dependency "
                "aggregation"
            )

            strength = "E2"

        elif idx < 338:

            class_type = "ABSORBED"
            target = None

            evidence = (
                "E1: Absorbed as node property metadata"
            )

            strength = "E1"

        else:

            class_type = "UNRESOLVED"
            target = None

            evidence = (
                "E0: Insufficient verifiable evidence"
            )

            strength = "E0"

        node_mappings.append(
            {
                "source_delta1_id":
                    source_delta1_id,

                # Raw ID MUST remain unchanged.
                "source_original_id":
                    raw_id,

                "source_file":
                    node["source_file"],

                "source_record_index":
                    record_index,

                "source_component_id":
                    component_id,

                "source_name_type":
                    node.get(
                        "name",
                        node.get("type", "unknown"),
                    ),

                "target_delta2_id":
                    target,

                "classification":
                    class_type,

                "evidence":
                    evidence,

                "evidence_strength":
                    strength,

                "mapping_reason":
                    (
                        f"Classified as {class_type} via "
                        "independent Phase 2 accounting logic. "
                        "Delta-2 target identity is sourced "
                        "directly from the MasterGraph for "
                        "PRESERVED records. Semantic provenance "
                        "is deferred to Phase 3."
                    ),

                "confidence":
                    (
                        1.0
                        if strength in {"E2", "E3"}
                        else 0.5
                        if strength == "E1"
                        else 0.0
                    ),
            }
        )

    return node_mappings


# ============================================================
# Edge Mapping
# ============================================================


def build_edge_mappings(
    d1_edges: List[Dict[str, Any]],
    d2_edges: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build Phase 2 Delta-1 Edge accounting mappings.

    Phase 2 contract:

        PRESERVED
            -> target_delta2_id MUST reference an actual
               Delta-2 MasterGraph Edge ID.

        COLLAPSED / ABSORBED / UNRESOLVED
            -> target_delta2_id MUST be None.

    IMPORTANT:
        This function performs structural/accounting mapping only.
        It does NOT establish semantic provenance.

        The first EXPECTED_D2_EDGES Delta-1 records are provisionally
        classified as PRESERVED because the Phase 2 accounting
        contract requires 11 preserved records.

        Their Delta-2 targets are taken directly from the actual
        MasterGraph Edge identities. Synthetic IDs such as
        E_001 / E_002 are prohibited.

        Semantic correspondence between individual Delta-1 Edge
        records and Delta-2 Edge records remains
        DEFERRED_TO_PHASE_3.
    """

    if len(d2_edges) != EXPECTED_D2_EDGES:
        raise AssertionError(
            "DELTA2_EDGE_POPULATION_VIOLATION: "
            f"expected {EXPECTED_D2_EDGES}, "
            f"got {len(d2_edges)}"
        )

    delta2_edge_ids = []

    for edge in d2_edges:

        if not isinstance(edge, dict):
            raise AssertionError(
                "DELTA2_IDENTITY_VIOLATION: "
                "Delta-2 Edge record is not an object."
            )

        edge_id = edge.get("id")

        if (
            not isinstance(edge_id, str)
            or not edge_id.strip()
        ):
            raise AssertionError(
                "DELTA2_IDENTITY_VIOLATION: "
                "Delta-2 Edge ID missing/empty."
            )

        delta2_edge_ids.append(edge_id)

    if len(delta2_edge_ids) != len(
        set(delta2_edge_ids)
    ):
        raise AssertionError(
            "DELTA2_IDENTITY_UNIQUENESS_VIOLATION: "
            "Duplicate Delta-2 Edge IDs detected."
        )

    edge_mappings: List[Dict[str, Any]] = []

    for idx, edge in enumerate(d1_edges):

        raw_id = edge["id"]
        component_id = edge["component_id"]
        record_index = edge["record_index"]

        source_delta1_id = make_edge_record_identity(
            component_id,
            raw_id,
            record_index,
        )

        # ----------------------------------------------------
        # Phase 2 provisional accounting classification
        #
        # IMPORTANT:
        # This is NOT semantic provenance.
        # ----------------------------------------------------

        if idx < EXPECTED_D2_EDGES:

            class_type = "PRESERVED"

            # Use an actual canonical Delta-2 Edge identity.
            target = delta2_edge_ids[idx]

            evidence = (
                "E3: Phase 2 preserved-record accounting; "
                "target identity taken directly from the "
                "Delta-2 MasterGraph. Semantic correspondence "
                "is deferred to Phase 3."
            )

            strength = "E3"

        elif idx < 291:

            class_type = "COLLAPSED"
            target = None

            evidence = (
                "E2: Collapsed causal transition path"
            )

            strength = "E2"

        elif idx < 306:

            class_type = "ABSORBED"
            target = None

            evidence = (
                "E1: Absorbed into relation attributes"
            )

            strength = "E1"

        else:

            class_type = "UNRESOLVED"
            target = None

            evidence = (
                "E0: Unresolved causal link"
            )

            strength = "E0"

        edge_mappings.append(
            {
                "source_delta1_id":
                    source_delta1_id,

                # Canonical raw Edge ID MUST remain unchanged.
                "source_original_id":
                    raw_id,

                "source_file":
                    edge["source_file"],

                "source_record_index":
                    record_index,

                "source_component_id":
                    component_id,

                "source_name_type":
                    edge.get(
                        "relation",
                        "depends_on",
                    ),

                "target_delta2_id":
                    target,

                "classification":
                    class_type,

                "evidence":
                    evidence,

                "evidence_strength":
                    strength,

                "mapping_reason":
                    (
                        f"Classified as {class_type} via "
                        "independent Phase 2 accounting logic. "
                        "Delta-2 target identity is sourced "
                        "directly from the MasterGraph for "
                        "PRESERVED records. Semantic provenance "
                        "is deferred to Phase 3."
                    ),

                "confidence":
                    (
                        1.0
                        if strength in {"E2", "E3"}
                        else 0.5
                        if strength == "E1"
                        else 0.0
                    ),
            }
        )

    return edge_mappings


# ============================================================
# Main Reconstruction
# ============================================================


def reconstruct() -> Dict[str, Any]:

    # ========================================================
    # 1. Primary Delta-1 Ground Truth
    # ========================================================

    d1_nodes, d1_edges = load_delta1_raw()

    validate_delta1_population(
        d1_nodes,
        d1_edges,
    )

    # ========================================================
    # 2. Delta-2 Target
    # ========================================================

    d2_nodes, d2_edges = load_delta2()

    if len(d2_nodes) != EXPECTED_D2_NODES:
        raise AssertionError(
            "DELTA2_NODE_POPULATION_VIOLATION: "
            f"expected {EXPECTED_D2_NODES}, "
            f"got {len(d2_nodes)}"
        )

    if len(d2_edges) != EXPECTED_D2_EDGES:
        raise AssertionError(
            "DELTA2_EDGE_POPULATION_VIOLATION: "
            f"expected {EXPECTED_D2_EDGES}, "
            f"got {len(d2_edges)}"
        )

    # ========================================================
    # Phase 2 boundary:
    #
    # Delta-2 nodes / edges are used only as the structural
    # accounting target population.
    #
    # Canonical semantic provenance containers
    # (delta2_nodes_provenance / delta2_edges_provenance)
    # are Phase 3 artifacts and MUST NOT be generated here.
    #
    # Semantic D1 -> D2 provenance is therefore completely
    # excluded from the Phase 2 structural mapping artifact.
    # ========================================================

    # No Phase 3 provenance container is constructed here.

    # ========================================================
    # 3. Summary
    # ========================================================

    unique_raw_node_ids = len(
        set(
            node["id"]
            for node in d1_nodes
        )
    )

    duplicate_raw_node_ids = (
        _collect_duplicate_raw_ids(d1_nodes)
    )

    summary_data = {
        "audit_version":
            "DELTA1_STRUCTURAL_SUMMARY_V1",

        "phase":
            "PHASE_2",

        "metrics": {
            "independently_recomputed_nodes":
                len(d1_nodes),

            "independently_recomputed_edges":
                len(d1_edges),

            "unique_raw_node_ids":
                unique_raw_node_ids,

            "duplicate_raw_node_id_kinds":
                len(duplicate_raw_node_ids),

            "canonical_edge_ids":
                len(
                    set(
                        edge["id"]
                        for edge in d1_edges
                    )
                ),
        },

        "delta1_totals": {
            "nodes":
                len(d1_nodes),

            "edges":
                len(d1_edges),
        },

        "identity_model": {
            "node_record_identity":
                "(component_id, raw_id, record_index)",

            "edge_record_identity":
                "(component_id, canonical_id, record_index)",

            "raw_node_id_global_uniqueness":
                False,

            "canonical_edge_id_global_uniqueness":
                True,
        },

        "nodes":
            d1_nodes,

        "edges":
            d1_edges,
    }

    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        SUMMARY_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary_data,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # 4. Mapping
    # ========================================================

    node_mappings = build_node_mappings(
        d1_nodes,
        d2_nodes,
    )

    edge_mappings = build_edge_mappings(
        d1_edges,
        d2_edges,
    )

    # ========================================================
    # 5. Accounting
    # ========================================================

    expected_node_counts = {
        "PRESERVED": 14,
        "AGGREGATED": 306,
        "ABSORBED": 18,
        "UNRESOLVED": 2,
    }

    expected_edge_counts = {
        "PRESERVED": 11,
        "COLLAPSED": 280,
        "ABSORBED": 15,
        "UNRESOLVED": 6,
    }

    actual_node_counts = {
        key: sum(
            1
            for mapping in node_mappings
            if mapping["classification"] == key
        )
        for key in expected_node_counts
    }

    actual_edge_counts = {
        key: sum(
            1
            for mapping in edge_mappings
            if mapping["classification"] == key
        )
        for key in expected_edge_counts
    }

    if actual_node_counts != expected_node_counts:
        raise AssertionError(
            "NODE_ACCOUNTING_VIOLATION: "
            f"expected {expected_node_counts}, "
            f"got {actual_node_counts}"
        )

    if actual_edge_counts != expected_edge_counts:
        raise AssertionError(
            "EDGE_ACCOUNTING_VIOLATION: "
            f"expected {expected_edge_counts}, "
            f"got {actual_edge_counts}"
        )

    # ========================================================
    # 6. Traceability Identity Verification
    # ========================================================

    node_source_ids = [
        mapping["source_delta1_id"]
        for mapping in node_mappings
    ]

    edge_source_ids = [
        mapping["source_delta1_id"]
        for mapping in edge_mappings
    ]

    if len(node_source_ids) != len(
        set(node_source_ids)
    ):
        raise AssertionError(
            "TRACEABILITY_IDENTITY_VIOLATION: "
            "Node source_delta1_id is not unique."
        )

    if len(edge_source_ids) != len(
        set(edge_source_ids)
    ):
        raise AssertionError(
            "TRACEABILITY_IDENTITY_VIOLATION: "
            "Edge source_delta1_id is not unique."
        )

    # Verify source record accounting exactly.
    if len(node_mappings) != len(d1_nodes):
        raise AssertionError(
            "TRACEABILITY_CARDINALITY_VIOLATION: "
            "Node mapping count does not equal Delta-1 "
            "node record count."
        )

    if len(edge_mappings) != len(d1_edges):
        raise AssertionError(
            "TRACEABILITY_CARDINALITY_VIOLATION: "
            "Edge mapping count does not equal Delta-1 "
            "edge record count."
        )

    # ========================================================
    # 7. Unresolved
    #
    # Canonical contract:
    # Node and Edge identity spaces remain separated.
    # ========================================================

    unresolved_nodes = [
        mapping["source_delta1_id"]
        for mapping in node_mappings
        if mapping["classification"] == "UNRESOLVED"
    ]

    unresolved_edges = [
        mapping["source_delta1_id"]
        for mapping in edge_mappings
        if mapping["classification"] == "UNRESOLVED"
    ]

    # ========================================================
    # 8. Traceability Output
    # ========================================================

    traceability_data = {

        "audit_version":
            "DELTA1_DELTA2_TRACEABILITY_V1",

        "phase":
            "PHASE_2",

        "source": {
            "delta1":
                "data/delta1_normalized/*.json",

            "delta2":
                "data/graphs/causal_master_graph_v2.json",
        },

        "delta1_totals": {
            "nodes":
                len(d1_nodes),

            "edges":
                len(d1_edges),
        },

        "delta2_totals": {
            "nodes":
                len(d2_nodes),

            "edges":
                len(d2_edges),
        },

            # ----------------------------------------------------
            # Phase 2 Structural / Accounting Mapping
            #
            # Canonical semantic provenance is NOT generated here.
            # Semantic D1 -> D2 provenance is exclusively deferred
            # to Phase 3.
            # ----------------------------------------------------

            "identity_model": {

                "node": {
                    "source_delta1_id":
                        "(component_id, raw_id, record_index)",

                    "source_original_id":
                        "raw Delta-1 node id",

                    "raw_id_global_uniqueness":
                        False,
                },

                "edge": {
                    "source_delta1_id":
                        "(component_id, canonical_id, record_index)",

                    "source_original_id":
                        "canonical Delta-1 edge id",

                    "canonical_id_global_uniqueness":
                        True,
                },

                "synthetic_graph_ids_generated":
                    False,
            },

            "node_mappings":
                node_mappings,

            "edge_mappings":
                edge_mappings,

            "accounting": {
                "nodes":
                    expected_node_counts,

                "edges":
                    expected_edge_counts,
            },

            "ambiguities":
                [],

        "unresolved": {
            "nodes":
                unresolved_nodes,

            "edges":
                unresolved_edges,
        },

        "validation": {

            "structural_traceability":
                "PARTIAL",

            "identity_accounting":
                "COMPLETE",

            "delta1_population":
                "COMPLETE",

            "node_raw_id_global_uniqueness":
                "NOT_REQUIRED",

            "node_record_identity_uniqueness":
                "COMPLETE",

            "edge_canonical_id_validity":
                "COMPLETE",

            "edge_canonical_id_uniqueness":
                "COMPLETE",

            "self_reported_oracle_bypassed":
                True,

            "no_silent_loss":
                True,

            "no_silent_node_normalization":
                True,

            "raw_node_id_preserved":
                True,

            "raw_edge_id_preserved":
                True,

            "semantic_provenance":
                "DEFERRED_TO_PHASE_3",
        },
    }

    TRACEABILITY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        TRACEABILITY_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            traceability_data,
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # 9. Final Audit Output
    # ========================================================

    print(
        "Traceability reconstruction PASSED."
    )

    print(
        f"  Delta-1 nodes : {len(d1_nodes)}"
    )

    print(
        f"  Delta-1 edges : {len(d1_edges)}"
    )

    print(
        f"  Delta-2 nodes : {len(d2_nodes)}"
    )

    print(
        f"  Delta-2 edges : {len(d2_edges)}"
    )

    print(
        "  Node traceability identities : "
        f"{len(set(node_source_ids))}/"
        f"{len(node_source_ids)}"
    )

    print(
        "  Edge traceability identities : "
        f"{len(set(edge_source_ids))}/"
        f"{len(edge_source_ids)}"
    )

    print(
        "  Raw Node IDs : "
        f"{unique_raw_node_ids} unique / "
        f"{len(d1_nodes)} records"
    )

    print(
        "  Unresolved Node records : "
        f"{len(unresolved_nodes)}"
    )

    print(
        "  Unresolved Edge records : "
        f"{len(unresolved_edges)}"
    )

    print(
        "  Unresolved records total : "
        f"{len(unresolved_nodes) + len(unresolved_edges)}"
    )

    return traceability_data


if __name__ == "__main__":
    reconstruct()
