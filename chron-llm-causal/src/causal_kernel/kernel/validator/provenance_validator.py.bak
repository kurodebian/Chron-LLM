"""ProvenanceValidator: Canonical Traceability の Provenance 記録の構造的・意味的整合性を検証するバリデータ。"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ProvenanceValidator:
    """Canonical Traceability (delta1_delta2_traceability.json) の Provenance 記録を検証する。

    検証対象:
    - delta2_nodes_provenance / delta2_edges_provenance の配列構造
    - delta2_node_id / delta2_edge_id の存在および MasterGraph との整合性
    - source_delta1_nodes_count / source_delta1_edges_count の非負整数判定 (>= 0)
    - provenance_complete (boolean) の型および count との整合性 (complete == True のとき count > 0)
    """

    def __init__(self, master_graph: Optional[Dict[str, Any]] = None):
        self.master_graph = master_graph
        self._valid_node_ids: Set[str] = set()
        self._valid_edge_ids: Set[str] = set()

        if master_graph:
            if "nodes" in master_graph and isinstance(master_graph["nodes"], list):
                self._valid_node_ids = {
                    n.get("id") or n.get("node_id")
                    for n in master_graph["nodes"]
                    if isinstance(n, dict)
                }
            elif "nodes" in master_graph and isinstance(master_graph["nodes"], dict):
                self._valid_node_ids = set(master_graph["nodes"].keys())

            if "edges" in master_graph and isinstance(master_graph["edges"], list):
                self._valid_edge_ids = {
                    e.get("id") or e.get("edge_id")
                    for e in master_graph["edges"]
                    if isinstance(e, dict)
                }
            elif "edges" in master_graph and isinstance(master_graph["edges"], dict):
                self._valid_edge_ids = set(master_graph["edges"].keys())

    def validate(self, traceability_data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(traceability_data, dict):
            return ValidationResult(
                is_valid=False,
                errors=["Traceability data must be a dictionary"],
            )

        # 1. Node Provenance の検証
        if "delta2_nodes_provenance" not in traceability_data:
            errors.append("Missing required root key: 'delta2_nodes_provenance'")
        else:
            node_prov = traceability_data["delta2_nodes_provenance"]
            if not isinstance(node_prov, list):
                errors.append("'delta2_nodes_provenance' must be a list")
            else:
                self._validate_node_provenance_entries(node_prov, errors)

        # 2. Edge Provenance の検証
        if "delta2_edges_provenance" not in traceability_data:
            errors.append("Missing required root key: 'delta2_edges_provenance'")
        else:
            edge_prov = traceability_data["delta2_edges_provenance"]
            if not isinstance(edge_prov, list):
                errors.append("'delta2_edges_provenance' must be a list")
            else:
                self._validate_edge_provenance_entries(edge_prov, errors)

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def _validate_node_provenance_entries(
        self, entries: List[Any], errors: List[str]
    ) -> None:
        for idx, item in enumerate(entries):
            prefix = f"delta2_nodes_provenance[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue

            node_id = item.get("delta2_node_id")
            if not node_id or not isinstance(node_id, str):
                errors.append(f"{prefix}: 'delta2_node_id' must be a non-empty string")
            elif self.master_graph and node_id not in self._valid_node_ids:
                errors.append(
                    f"{prefix}: referenced node_id '{node_id}' does not exist in MasterGraph"
                )

            count = item.get("source_delta1_nodes_count")
            if count is None or type(count) is not int:
                errors.append(
                    f"{prefix}: 'source_delta1_nodes_count' must be an integer"
                )
            elif count < 0:
                errors.append(
                    f"{prefix}: 'source_delta1_nodes_count' cannot be negative (got {count})"
                )

            complete = item.get("provenance_complete")
            if complete is None or type(complete) is not bool:
                errors.append(f"{prefix}: 'provenance_complete' must be a boolean")
            elif complete and isinstance(count, int) and count == 0:
                errors.append(
                    f"{prefix}: 'provenance_complete' is True but source count is 0"
                )

    def _validate_edge_provenance_entries(
        self, entries: List[Any], errors: List[str]
    ) -> None:
        for idx, item in enumerate(entries):
            prefix = f"delta2_edges_provenance[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue

            edge_id = item.get("delta2_edge_id")
            if not edge_id or not isinstance(edge_id, str):
                errors.append(f"{prefix}: 'delta2_edge_id' must be a non-empty string")
            elif self.master_graph and edge_id not in self._valid_edge_ids:
                errors.append(
                    f"{prefix}: referenced edge_id '{edge_id}' does not exist in MasterGraph"
                )

            count = item.get("source_delta1_edges_count")
            if count is None or type(count) is not int:
                errors.append(
                    f"{prefix}: 'source_delta1_edges_count' must be an integer"
                )
            elif count < 0:
                errors.append(
                    f"{prefix}: 'source_delta1_edges_count' cannot be negative (got {count})"
                )

            complete = item.get("provenance_complete")
            if complete is None or type(complete) is not bool:
                errors.append(f"{prefix}: 'provenance_complete' must be a boolean")
            elif complete and isinstance(count, int) and count == 0:
                errors.append(
                    f"{prefix}: 'provenance_complete' is True but source count is 0"
                )