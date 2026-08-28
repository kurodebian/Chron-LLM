"""
Independent Delta-1 Ground Truth Scanner (Step 4-4-C - Freeze Version)

【絶対原則】
1. Observe Everything (Layer A):
   トップレベル JSON が読み込めた時点で、component_id やノード形式の正否に関わらず、
   物理 JSON 内の全レコード (nodes, edges, proposals) を無条件に観測・記録する。
2. Promote to Canonical GT (Layer B):
   component_id の存在、形式、IDの一意性、origin/構造の契約を満たすものだけを Canonical GT へ昇格させる。
3. Proposal の隔離:
   proposals は Layer A (Physical) でのみ観測し、Layer B (Canonical Nodes/Edges) へは絶対に昇格させない。
4. 自動補完・フォールバック・救済変換の完全禁止。
"""

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Dict, List, Set, Tuple, Optional

VALID_NODE_ORIGINS = {
    "EXPLICIT_NODE",
    "SYNTHETIC_ENDPOINT_NODE",
}


# --- Layer A: Physical Observation Records ---
@dataclass(frozen=True)
class ObservedNodeRecord:
    raw_data: Dict[str, Any]
    source_file: str
    record_index: int


@dataclass(frozen=True)
class ObservedEdgeRecord:
    raw_data: Dict[str, Any]
    source_file: str
    record_index: int


@dataclass(frozen=True)
class ObservedProposalRecord:
    raw_data: Dict[str, Any]
    source_file: str
    record_index: int


# --- Layer B: Canonical GT Records ---
@dataclass(frozen=True)
class CanonicalNodeRecord:
    id: str
    component_id: str
    origin: str
    source_file: str
    record_index: int


@dataclass(frozen=True)
class CanonicalEdgeRecord:
    id: str
    component_id: str
    from_id: str
    to_id: str
    relation: str
    source_file: str
    record_index: int


@dataclass(frozen=True)
class Delta1GroundTruth:
    # Layer B: Promoted Canonical Records (Nodes + Edges ONLY)
    canonical_nodes: Tuple[CanonicalNodeRecord, ...]
    canonical_edges: Tuple[CanonicalEdgeRecord, ...]

    # Layer A: Full Physical Observation Data
    observed_nodes: Tuple[ObservedNodeRecord, ...]
    observed_edges: Tuple[ObservedEdgeRecord, ...]
    observed_proposals: Tuple[ObservedProposalRecord, ...]

    # Layer A: Physical Counts
    physical_node_count: int
    physical_edge_count: int
    physical_proposal_count: int


@dataclass(frozen=True)
class ScanSummary:
    status: str  # "PASS" | "FAIL"
    physical_population: Dict[str, int]
    canonical_population: Dict[str, int]
    nodes: Dict[str, int]
    edges: Dict[str, int]
    identity: Dict[str, int]
    errors: Tuple[Dict[str, str], ...]


class IndependentDelta1Scanner:
    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir)

    def scan(self) -> Tuple[Delta1GroundTruth, ScanSummary]:
        # Layer A Collection
        observed_nodes_list: List[ObservedNodeRecord] = []
        observed_edges_list: List[ObservedEdgeRecord] = []
        observed_proposals_list: List[ObservedProposalRecord] = []

        # Layer B Collection
        canonical_nodes_list: List[CanonicalNodeRecord] = []
        canonical_edges_list: List[CanonicalEdgeRecord] = []

        errors: List[Dict[str, str]] = []

        seen_node_ids: Set[str] = set()
        seen_edge_ids: Set[str] = set()
        seen_semantic_edges: Set[Tuple[str, str, str, str]] = set()

        missing_node_ids_count = 0
        missing_edge_ids_count = 0
        duplicate_node_ids_count = 0
        duplicate_edge_ids_count = 0
        duplicate_semantic_edges_count = 0

        explicit_nodes_count = 0
        synthetic_endpoint_nodes_count = 0

        json_files = sorted(self.target_dir.glob("*.json"))

        for file_path in json_files:
            file_name = file_path.name
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": f"Failed to parse JSON: {str(e)}"
                })
                continue

            if not isinstance(data, dict):
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": "Top-level JSON structure must be a dict"
                })
                continue

            # =========================================================
            # LAYER A: Unconditional Physical Observation (Observe Everything)
            # =========================================================

            # 1. Physical Proposals Observation
            proposals_raw = data.get("proposals")
            if proposals_raw is None:
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": "Field 'proposals' is missing"
                })
            elif not isinstance(proposals_raw, list):
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": f"Field 'proposals' must be a list, got {type(proposals_raw).__name__}"
                })
            else:
                for idx, prop in enumerate(proposals_raw):
                    raw_dict = prop if isinstance(prop, dict) else {"__raw__": prop}
                    observed_proposals_list.append(ObservedProposalRecord(
                        raw_data=raw_dict,
                        source_file=file_name,
                        record_index=idx
                    ))

            # 2. Physical Nodes Observation
            nodes_raw = data.get("nodes")
            if nodes_raw is None:
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": "Field 'nodes' is missing"
                })
            elif not isinstance(nodes_raw, list):
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": f"Field 'nodes' must be a list, got {type(nodes_raw).__name__}"
                })
            else:
                for idx, node in enumerate(nodes_raw):
                    raw_dict = node if isinstance(node, dict) else {"__raw__": node}
                    observed_nodes_list.append(ObservedNodeRecord(
                        raw_data=raw_dict,
                        source_file=file_name,
                        record_index=idx
                    ))

            # 3. Physical Edges Observation
            edges_raw = data.get("edges")
            if edges_raw is None:
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": "Field 'edges' is missing"
                })
            elif not isinstance(edges_raw, list):
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": f"Field 'edges' must be a list, got {type(edges_raw).__name__}"
                })
            else:
                for idx, edge in enumerate(edges_raw):
                    raw_dict = edge if isinstance(edge, dict) else {"__raw__": edge}
                    observed_edges_list.append(ObservedEdgeRecord(
                        raw_data=raw_dict,
                        source_file=file_name,
                        record_index=idx
                    ))

            # =========================================================
            # LAYER B: Contract Validation & Canonical GT Promotion
            # =========================================================

            # Component ID Validation (Canonical 昇格のための必要条件)
            component_id = data.get("component_id")
            if not isinstance(component_id, str) or not component_id.strip():
                errors.append({
                    "type": "SCHEMA_VIOLATION",
                    "file": file_name,
                    "message": "Missing or invalid 'component_id' string"
                })
                continue

            # Node Canonical Promotion
            if isinstance(nodes_raw, list):
                for idx, node in enumerate(nodes_raw):
                    if not isinstance(node, dict):
                        errors.append({
                            "type": "SCHEMA_VIOLATION",
                            "file": file_name,
                            "message": f"Node record at index {idx} is not a dict"
                        })
                        continue

                    node_id = node.get("id")
                    origin = node.get("origin")

                    is_id_valid = isinstance(node_id, str) and len(node_id.strip()) > 0
                    is_origin_valid = (origin is None) or (isinstance(origin, str) and origin in VALID_NODE_ORIGINS)

                    if not is_id_valid:
                        missing_node_ids_count += 1
                        errors.append({
                            "type": "IDENTITY_VIOLATION",
                            "file": file_name,
                            "message": f"Node at index {idx} missing valid string 'id'"
                        })

                    if not is_origin_valid:
                        errors.append({
                            "type": "IDENTITY_VIOLATION",
                            "file": file_name,
                            "message": f"Node at index {idx} has invalid origin: {origin}"
                        })

                    if not is_id_valid or not is_origin_valid:
                        continue

                    if node_id in seen_node_ids:
                        duplicate_node_ids_count += 1
                        errors.append({
                            "type": "DUPLICATE_ID",
                            "file": file_name,
                            "message": f"Duplicate Node ID detected: '{node_id}'"
                        })
                        continue

                    seen_node_ids.add(node_id)

                    canonical_origin = origin if origin is not None else "EXPLICIT_NODE"

                    if canonical_origin == "EXPLICIT_NODE":
                        explicit_nodes_count += 1
                    elif canonical_origin == "SYNTHETIC_ENDPOINT_NODE":
                        synthetic_endpoint_nodes_count += 1

                    canonical_nodes_list.append(CanonicalNodeRecord(
                        id=node_id,
                        component_id=component_id,
                        origin=canonical_origin,
                        source_file=file_name,
                        record_index=idx
                    ))

            # Edge Canonical Promotion
            if isinstance(edges_raw, list):
                for idx, edge in enumerate(edges_raw):
                    if not isinstance(edge, dict):
                        errors.append({
                            "type": "SCHEMA_VIOLATION",
                            "file": file_name,
                            "message": f"Edge record at index {idx} is not a dict"
                        })
                        continue

                    edge_id = edge.get("id")
                    src = edge.get("from")
                    dst = edge.get("to")
                    relation = edge.get("relation")

                    is_id_valid = isinstance(edge_id, str) and len(edge_id.strip()) > 0
                    is_struct_valid = (
                        isinstance(src, str) and len(src.strip()) > 0 and
                        isinstance(dst, str) and len(dst.strip()) > 0 and
                        isinstance(relation, str) and len(relation.strip()) > 0
                    )

                    if not is_id_valid:
                        missing_edge_ids_count += 1
                        errors.append({
                            "type": "IDENTITY_VIOLATION",
                            "file": file_name,
                            "message": f"Edge at index {idx} missing valid string 'id'"
                        })

                    if not is_struct_valid:
                        errors.append({
                            "type": "TYPE_VIOLATION",
                            "file": file_name,
                            "message": (
                                f"Edge at index {idx} has invalid structural field type/value "
                                "(from/to/relation must be non-empty strings)"
                            )
                        })

                    if not is_id_valid or not is_struct_valid:
                        continue

                    if edge_id in seen_edge_ids:
                        duplicate_edge_ids_count += 1
                        errors.append({
                            "type": "DUPLICATE_ID",
                            "file": file_name,
                            "message": f"Duplicate Edge ID detected: '{edge_id}'"
                        })
                        continue

                    semantic_key = (component_id, src, dst, relation)
                    if semantic_key in seen_semantic_edges:
                        duplicate_semantic_edges_count += 1
                        errors.append({
                            "type": "DUPLICATE_ID",
                            "file": file_name,
                            "message": f"Semantic duplicate edge detected for key: {semantic_key}"
                        })
                        continue

                    seen_edge_ids.add(edge_id)
                    seen_semantic_edges.add(semantic_key)

                    canonical_edges_list.append(CanonicalEdgeRecord(
                        id=edge_id,
                        component_id=component_id,
                        from_id=src,
                        to_id=dst,
                        relation=relation,
                        source_file=file_name,
                        record_index=idx
                    ))

        status = "PASS" if len(errors) == 0 else "FAIL"

        phys_node_count = len(observed_nodes_list)
        phys_edge_count = len(observed_edges_list)
        phys_prop_count = len(observed_proposals_list)

        gt_snapshot = Delta1GroundTruth(
            canonical_nodes=tuple(canonical_nodes_list),
            canonical_edges=tuple(canonical_edges_list),
            observed_nodes=tuple(observed_nodes_list),
            observed_edges=tuple(observed_edges_list),
            observed_proposals=tuple(observed_proposals_list),
            physical_node_count=phys_node_count,
            physical_edge_count=phys_edge_count,
            physical_proposal_count=phys_prop_count
        )

        scan_summary = ScanSummary(
            status=status,
            physical_population={
                "nodes": phys_node_count,
                "edges": phys_edge_count,
                "proposals": phys_prop_count
            },
            canonical_population={
                "nodes": len(canonical_nodes_list),
                "edges": len(canonical_edges_list),
            },
            nodes={
                "total_physical": phys_node_count,
                "canonical": len(canonical_nodes_list),
                "explicit": explicit_nodes_count,
                "synthetic_endpoint": synthetic_endpoint_nodes_count,
                "rejected": phys_node_count - len(canonical_nodes_list)
            },
            edges={
                "total_physical": phys_edge_count,
                "canonical": len(canonical_edges_list),
                "rejected": phys_edge_count - len(canonical_edges_list)
            },
            identity={
                "missing_node_ids": missing_node_ids_count,
                "missing_edge_ids": missing_edge_ids_count,
                "duplicate_node_ids": duplicate_node_ids_count,
                "duplicate_edge_ids": duplicate_edge_ids_count,
                "duplicate_semantic_edges": duplicate_semantic_edges_count
            },
            errors=tuple(errors)
        )

        return gt_snapshot, scan_summary