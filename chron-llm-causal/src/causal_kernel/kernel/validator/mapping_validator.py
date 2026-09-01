"""MappingValidator: Delta1 と Delta2 間のマッピング意味論および構造的整合性を検証するバリデータ。"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class MappingValidator:
    """Delta1 ↔ Delta2 マッピングの一般化された独立検証ロジック。"""

    ALLOWED_MAPPING_STATUSES: Set[str] = {
        "PRESERVED",
        "AGGREGATED",
        "COLLAPSED",
        "ABSORBED",
        "UNRESOLVED",
        "RESOLVED",
        "AMBIGUOUS",
        "1:1",
        "N:1",
        "1:N",
        "ABSTRACTION",
    }

    # Delta2 の Target ID 存在が必須となるステータス。
    #
    # AGGREGATED / COLLAPSED は accounting 上の分類であり、
    # Canonical な Delta-2 Target を持たないため、Target ID は None
    # であることを正当な状態として許容する。
    #
    # ABSORBED / UNRESOLVED / AMBIGUOUS についても
    # Target ID なしを正当として許容する。
    TARGET_REQUIRED_STATUSES: Set[str] = {
        "PRESERVED",
        "RESOLVED",
        "1:1",
        "N:1",
        "1:N",
        "ABSTRACTION",
    }

    def __init__(
        self,
        delta1_nodes: Optional[Set[str]] = None,
        delta2_nodes: Optional[Set[str]] = None,
        delta1_edges: Optional[Set[str]] = None,
        delta2_edges: Optional[Set[str]] = None,
    ):
        self.delta1_nodes = delta1_nodes
        self.delta2_nodes = delta2_nodes
        self.delta1_edges = delta1_edges
        self.delta2_edges = delta2_edges

    def validate(self, mapping_data: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(mapping_data, dict):
            return ValidationResult(
                is_valid=False,
                errors=["Mapping data must be a dictionary"],
            )

        # 1. Node Mappings の検証
        if "node_mappings" in mapping_data:
            self._validate_mapping_list(
                mapping_data["node_mappings"],
                mapping_type="node_mappings",
                source_id_key="source_delta1_id",
                target_id_key="target_delta2_id",
                known_sources=self.delta1_nodes,
                known_targets=self.delta2_nodes,
                errors=errors,
                warnings=warnings,
            )

        # 2. Edge Mappings の検証
        if "edge_mappings" in mapping_data:
            self._validate_mapping_list(
                mapping_data["edge_mappings"],
                mapping_type="edge_mappings",
                source_id_key="source_delta1_id",
                target_id_key="target_delta2_id",
                known_sources=self.delta1_edges,
                known_targets=self.delta2_edges,
                errors=errors,
                warnings=warnings,
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_mapping_list(
        self,
        mappings: Any,
        mapping_type: str,
        source_id_key: str,
        target_id_key: str,
        known_sources: Optional[Set[str]],
        known_targets: Optional[Set[str]],
        errors: List[str],
        warnings: List[str],
    ) -> None:
        if not isinstance(mappings, list):
            errors.append(f"'{mapping_type}' must be a list")
            return

        seen_pairs: Set[Tuple[str, str]] = set()

        for idx, item in enumerate(mappings):
            prefix = f"{mapping_type}[{idx}]"

            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue

            # A. Source ID 抽出と存在検証
            source_id = (
                item.get(source_id_key)
                or item.get("source_id")
                or item.get("delta1_id")
            )

            if not source_id or not isinstance(source_id, str):
                errors.append(
                    f"{prefix}: missing or non-string source Delta1 ID"
                )
            else:
                if (
                    known_sources is not None
                    and source_id not in known_sources
                ):
                    errors.append(
                        f"{prefix}: source ID '{source_id}' "
                        f"not found in Delta1 specification"
                    )

            # B. 分類・ステータスの取得
            status = str(
                item.get("classification")
                or item.get("status")
                or item.get("mapping_type")
                or ""
            ).upper()

            if not status:
                errors.append(
                    f"{prefix}: missing mapping classification/status"
                )
            elif status not in self.ALLOWED_MAPPING_STATUSES:
                errors.append(
                    f"{prefix}: invalid mapping classification/status "
                    f"'{status}'"
                )

            # C. Target ID 必須性と参照整合性チェック
            target_id = (
                item.get(target_id_key)
                or item.get("target_id")
                or item.get("delta2_id")
            )

            if status in self.TARGET_REQUIRED_STATUSES:
                if not target_id or not isinstance(target_id, str):
                    errors.append(
                        f"{prefix}: classification '{status}' "
                        f"requires a valid target Delta2 ID"
                    )
                elif (
                    known_targets is not None
                    and target_id not in known_targets
                ):
                    errors.append(
                        f"{prefix}: target ID '{target_id}' "
                        f"not found in Delta2 graph"
                    )

            elif target_id and isinstance(target_id, str):
                # AGGREGATED / COLLAPSED / ABSORBED / UNRESOLVED /
                # AMBIGUOUS 等で Target ID が明示されている場合でも、
                # 指定された ID 自体が存在するなら参照整合性を検証する。
                if (
                    known_targets is not None
                    and target_id not in known_targets
                ):
                    errors.append(
                        f"{prefix}: target ID '{target_id}' "
                        f"not found in Delta2 graph"
                    )

            # D. 重複マッピング検出:
            # (source_id, target_id) の完全一致のみ拒否。
            #
            # AGGREGATED / COLLAPSED 等は target_id=None が正当なので、
            # ここでは Target ID を持つ関係のみ対象とする。
            if (
                source_id
                and target_id
                and status in self.TARGET_REQUIRED_STATUSES
            ):
                pair = (source_id, target_id)

                if pair in seen_pairs:
                    errors.append(
                        f"{prefix}: duplicate mapping relationship for "
                        f"source '{source_id}' -> target '{target_id}'"
                    )

                seen_pairs.add(pair)

            # E. Mapping Evidence 存在判定
            evidence = (
                item.get("evidence")
                or item.get("mapping_evidence")
                or item.get("proof")
            )

            if evidence is None or (
                isinstance(evidence, (str, list, dict))
                and len(evidence) == 0
            ):
                errors.append(
                    f"{prefix}: missing or empty mapping evidence"
                )

            # F. E0 × VERIFIED の論理矛盾判定
            evidence_level = str(
                item.get("evidence_strength")
                or item.get("evidence_level")
                or ""
            ).upper()

            verification_status = str(
                item.get("verification_status")
                or item.get("status_verification")
                or ""
            ).upper()

            if (
                evidence_level == "E0"
                and verification_status
                in {"VERIFIED", "APPROVED", "CONFIRMED"}
            ):
                errors.append(
                    f"{prefix}: logical contradiction - "
                    f"cannot be VERIFIED with E0 evidence strength"
                )