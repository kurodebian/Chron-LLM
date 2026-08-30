import glob
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


@dataclass
class TraceabilityClaims:
    claimed_node_ids: Set[str] = field(default_factory=set)
    claimed_edge_keys: Set[Tuple[str, str, str]] = field(default_factory=set)
    node_sources: Dict[str, Set[str]] = field(default_factory=dict)
    malformed_entries: List[Dict[str, Any]] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)

    @property
    def claimed_node_count(self) -> int:
        return len(self.claimed_node_ids)

    @property
    def claimed_edge_count(self) -> int:
        return len(self.claimed_edge_keys)


class TraceabilityClaimExtractor:

    def __init__(
        self,
        traceability_files: List[str],
        delta1_dir: str = "data/delta1_normalized",
    ):
        self.traceability_files = traceability_files
        self.delta1_dir = delta1_dir
        self._d1_edges_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._load_delta1_cache()

    def _load_delta1_cache(self) -> None:
        """Delta-1 Normalized JSON の edges 配列をファイル名キーでキャッシュ"""
        if not os.path.exists(self.delta1_dir):
            return
        for path in glob.glob(os.path.join(self.delta1_dir, "*.json")):
            fname = os.path.basename(path)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and isinstance(
                        data.get("edges"), list
                    ):
                        self._d1_edges_cache[fname] = data["edges"]
            except Exception:
                pass

    def extract(self) -> TraceabilityClaims:
        claims = TraceabilityClaims()
        for file_path in self.traceability_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._process_traceability_data(data, file_path, claims)
                claims.source_files.append(file_path)
            except FileNotFoundError:
                claims.malformed_entries.append(
                    {"type": "FILE_NOT_FOUND", "file": file_path}
                )
            except json.JSONDecodeError as e:
                claims.malformed_entries.append(
                    {
                        "type": "JSON_DECODE_ERROR",
                        "file": file_path,
                        "error": str(e),
                    }
                )
        return claims

    @staticmethod
    def _normalize_claimed_node_id(node_id: Any) -> str:
        """
        Claim側 Node Identity を Semantic Node ID 空間へ正規化する。

        Semantic ID:
            INV_CanonicalImmutable

        Delta-1 physical composite key:
            component-001::INV_CanonicalImmutable::19

        3要素の物理複合キーの場合のみ、中央要素を Semantic Node ID として射影抽出する。
        """
        node_str = str(node_id).strip()
        if not node_str:
            return ""

        parts = node_str.split("::")
        if (
            len(parts) == 3
            and parts[0].strip()
            and parts[1].strip()
            and parts[2].strip().isdigit()
        ):
            return parts[1].strip()

        return node_str

    def _record_node_claim(
        self, node_id: Any, file_path: str, claims: TraceabilityClaims
    ) -> None:
        node_str = self._normalize_claimed_node_id(node_id)
        if not node_str:
            return

        claims.claimed_node_ids.add(node_str)
        if node_str not in claims.node_sources:
            claims.node_sources[node_str] = set()
        claims.node_sources[node_str].add(file_path)

    def _process_traceability_data(
        self, data: dict, file_path: str, claims: TraceabilityClaims
    ) -> None:
        if not isinstance(data, dict):
            return

        # Pattern A: Standard Mapping Format (node_mappings / edge_mappings)
        if "node_mappings" in data and isinstance(data["node_mappings"], list):
            for mapping in data["node_mappings"]:
                if isinstance(mapping, dict):
                    # Ground Truth 側の Semantic ID (source_original_id) を最優先取得
                    node_id = (
                        mapping.get("source_original_id")
                        or mapping.get("source_delta1_id")
                        or mapping.get("id")
                    )
                    if node_id:
                        self._record_node_claim(node_id, file_path, claims)

        if "edge_mappings" in data and isinstance(data["edge_mappings"], list):
            for mapping in data["edge_mappings"]:
                if not isinstance(mapping, dict):
                    continue

                s_file = mapping.get("source_file")
                idx = mapping.get("source_record_index")

                # 1. source_file と source_record_index による Delta-1 キャッシュの直接参照 (推測・暗黙補正なし)
                if s_file and isinstance(idx, int):
                    if s_file in self._d1_edges_cache:
                        gt_edges = self._d1_edges_cache[s_file]
                        if 0 <= idx < len(gt_edges):
                            e = gt_edges[idx]
                            src = e.get("from") or e.get("source")
                            dst = e.get("to") or e.get("target")
                            etype = (
                                e.get("relation")
                                or e.get("type")
                                or mapping.get("source_name_type")
                                or "UNDEFINED"
                            )
                            if src and dst:
                                claims.claimed_edge_keys.add(
                                    (str(src), str(dst), str(etype))
                                )
                                continue

                # 2. 直接指定型フォーマット (source / target / type または from / to / relation)
                src = mapping.get("source") or mapping.get("from")
                dst = mapping.get("target") or mapping.get("to")
                etype = (
                    mapping.get("type")
                    or mapping.get("relation")
                    or mapping.get("source_name_type")
                    or "UNDEFINED"
                )
                if src and dst:
                    claims.claimed_edge_keys.add(
                        (str(src), str(dst), str(etype))
                    )

        # Pattern B: Traditional nodes / proposals / edges list format
        for key in ("nodes", "proposals"):
            if key in data and isinstance(data[key], list):
                for node in data[key]:
                    if isinstance(node, dict):
                        node_id = (
                            node.get("source_original_id")
                            or node.get("source_delta1_id")
                            or node.get("delta1_id")
                            or node.get("id")
                        )
                        if node_id:
                            self._record_node_claim(node_id, file_path, claims)

        if "edges" in data and isinstance(data["edges"], list):
            for edge in data["edges"]:
                if isinstance(edge, dict):
                    src = edge.get("source") or edge.get("from")
                    dst = edge.get("target") or edge.get("to")
                    etype = (
                        edge.get("type") or edge.get("relation") or "UNDEFINED"
                    )
                    if src and dst:
                        claims.claimed_edge_keys.add(
                            (str(src), str(dst), str(etype))
                        )