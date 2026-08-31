"""Canonical Traceability Provenance validator.

F4 Canonical Traceability Schema と完全に同期し、
Delta-2 element -> Delta-1 authoritative record の
semantic provenance を独立検証する。
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ProvenanceValidator:
    """Canonical Traceability の Provenance を検証する。

    Canonical Record Identity:
        Node: {component_id}:{raw_id}:{record_index}
        Edge: {component_id}:{canonical_id}:{record_index}

    count フィールドは Canonical Contract に存在しないため、
    source_delta1_*_ids の len() を唯一の件数情報として扱う。
    """

    CANONICAL_RECORD_ID_PATTERN = re.compile(
        r"^[^:]+:[^:]+:[0-9]+$"
    )

    def __init__(
        self,
        master_graph: Optional[Dict[str, Any]] = None,
    ):
        self.master_graph = master_graph

        self._valid_node_ids: Set[str] = set()
        self._valid_edge_ids: Set[str] = set()

        if not master_graph:
            return

        nodes = master_graph.get("nodes")
        if isinstance(nodes, list):
            self._valid_node_ids = {
                node.get("id") or node.get("node_id")
                for node in nodes
                if isinstance(node, dict)
                and isinstance(
                    node.get("id") or node.get("node_id"),
                    str,
                )
            }
        elif isinstance(nodes, dict):
            self._valid_node_ids = set(nodes.keys())

        edges = master_graph.get("edges")
        if isinstance(edges, list):
            self._valid_edge_ids = {
                edge.get("id") or edge.get("edge_id")
                for edge in edges
                if isinstance(edge, dict)
                and isinstance(
                    edge.get("id") or edge.get("edge_id"),
                    str,
                )
            }
        elif isinstance(edges, dict):
            self._valid_edge_ids = set(edges.keys())

    def validate(
        self,
        traceability_data: Dict[str, Any],
    ) -> ValidationResult:

        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(traceability_data, dict):
            return ValidationResult(
                is_valid=False,
                errors=[
                    "Traceability data must be a dictionary"
                ],
            )

        # --------------------------------------------------
        # Node Provenance
        # --------------------------------------------------

        if "delta2_nodes_provenance" not in traceability_data:
            errors.append(
                "Missing required root key: "
                "'delta2_nodes_provenance'"
            )
        else:
            entries = traceability_data[
                "delta2_nodes_provenance"
            ]

            if not isinstance(entries, list):
                errors.append(
                    "'delta2_nodes_provenance' must be a list"
                )
            else:
                self._validate_node_provenance_entries(
                    entries,
                    errors,
                )

        # --------------------------------------------------
        # Edge Provenance
        # --------------------------------------------------

        if "delta2_edges_provenance" not in traceability_data:
            errors.append(
                "Missing required root key: "
                "'delta2_edges_provenance'"
            )
        else:
            entries = traceability_data[
                "delta2_edges_provenance"
            ]

            if not isinstance(entries, list):
                errors.append(
                    "'delta2_edges_provenance' must be a list"
                )
            else:
                self._validate_edge_provenance_entries(
                    entries,
                    errors,
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # ======================================================
    # Node Provenance
    # ======================================================

    def _validate_node_provenance_entries(
        self,
        entries: List[Any],
        errors: List[str],
    ) -> None:

        seen_delta2_ids: Set[str] = set()

        for idx, item in enumerate(entries):

            prefix = (
                f"delta2_nodes_provenance[{idx}]"
            )

            if not isinstance(item, dict):
                errors.append(
                    f"{prefix} must be an object"
                )
                continue

            # ----------------------------------------------
            # Delta-2 node ID
            # ----------------------------------------------

            node_id = item.get("delta2_node_id")

            if (
                not isinstance(node_id, str)
                or not node_id.strip()
            ):
                errors.append(
                    f"{prefix}: "
                    "'delta2_node_id' must be a "
                    "non-empty string"
                )
            else:
                if (
                    self.master_graph
                    and node_id not in self._valid_node_ids
                ):
                    errors.append(
                        f"{prefix}: referenced node_id "
                        f"'{node_id}' does not exist "
                        "in MasterGraph"
                    )

                if node_id in seen_delta2_ids:
                    errors.append(
                        f"{prefix}: duplicate "
                        f"delta2_node_id '{node_id}'"
                    )

                seen_delta2_ids.add(node_id)

            # ----------------------------------------------
            # Canonical Delta-1 Node Record IDs
            # ----------------------------------------------

            source_ids = item.get(
                "source_delta1_node_ids"
            )

            self._validate_source_record_ids(
                source_ids,
                "source_delta1_node_ids",
                prefix,
                errors,
            )

            # ----------------------------------------------
            # provenance_complete
            # ----------------------------------------------

            complete = item.get("provenance_complete")

            if type(complete) is not bool:
                errors.append(
                    f"{prefix}: "
                    "'provenance_complete' must be a boolean"
                )
            elif complete and isinstance(source_ids, list):
                if len(source_ids) == 0:
                    errors.append(
                        f"{prefix}: "
                        "'provenance_complete' is True "
                        "but source_delta1_node_ids is empty"
                    )

    # ======================================================
    # Edge Provenance
    # ======================================================

    def _validate_edge_provenance_entries(
        self,
        entries: List[Any],
        errors: List[str],
    ) -> None:

        seen_delta2_ids: Set[str] = set()

        for idx, item in enumerate(entries):

            prefix = (
                f"delta2_edges_provenance[{idx}]"
            )

            if not isinstance(item, dict):
                errors.append(
                    f"{prefix} must be an object"
                )
                continue

            # ----------------------------------------------
            # Delta-2 edge ID
            # ----------------------------------------------

            edge_id = item.get("delta2_edge_id")

            if (
                not isinstance(edge_id, str)
                or not edge_id.strip()
            ):
                errors.append(
                    f"{prefix}: "
                    "'delta2_edge_id' must be a "
                    "non-empty string"
                )
            else:
                if (
                    self.master_graph
                    and edge_id not in self._valid_edge_ids
                ):
                    errors.append(
                        f"{prefix}: referenced edge_id "
                        f"'{edge_id}' does not exist "
                        "in MasterGraph"
                    )

                if edge_id in seen_delta2_ids:
                    errors.append(
                        f"{prefix}: duplicate "
                        f"delta2_edge_id '{edge_id}'"
                    )

                seen_delta2_ids.add(edge_id)

            # ----------------------------------------------
            # Canonical Delta-1 Edge Record IDs
            # ----------------------------------------------

            source_ids = item.get(
                "source_delta1_edge_ids"
            )

            self._validate_source_record_ids(
                source_ids,
                "source_delta1_edge_ids",
                prefix,
                errors,
            )

            # ----------------------------------------------
            # provenance_complete
            # ----------------------------------------------

            complete = item.get("provenance_complete")

            if type(complete) is not bool:
                errors.append(
                    f"{prefix}: "
                    "'provenance_complete' must be a boolean"
                )
            elif complete and isinstance(source_ids, list):
                if len(source_ids) == 0:
                    errors.append(
                        f"{prefix}: "
                        "'provenance_complete' is True "
                        "but source_delta1_edge_ids is empty"
                    )

    # ======================================================
    # Canonical Record Identity
    # ======================================================

    def _validate_source_record_ids(
        self,
        source_ids: Any,
        field_name: str,
        prefix: str,
        errors: List[str],
    ) -> None:

        if not isinstance(source_ids, list):
            errors.append(
                f"{prefix}: "
                f"'{field_name}' must be a list"
            )
            return

        seen_ids: Set[str] = set()

        for source_idx, source_id in enumerate(source_ids):

            source_prefix = (
                f"{prefix}.{field_name}[{source_idx}]"
            )

            if (
                not isinstance(source_id, str)
                or not source_id.strip()
            ):
                errors.append(
                    f"{source_prefix}: "
                    "must be a non-empty string"
                )
                continue

            if not self.CANONICAL_RECORD_ID_PATTERN.fullmatch(
                source_id
            ):
                errors.append(
                    f"{source_prefix}: invalid "
                    "Canonical Record Identity "
                    f"'{source_id}'"
                )

            if source_id in seen_ids:
                errors.append(
                    f"{source_prefix}: duplicate "
                    f"source Delta-1 record identity "
                    f"'{source_id}'"
                )

            seen_ids.add(source_id)