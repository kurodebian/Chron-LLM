"""
FRR Global Integrity Validator (v1.2-Strict-Contract)
Chron-LLM Causal Kernel / Traceability Suite

Guarantees Global Integrity Invariants (FR-INV-01 .. FR-INV-10)
with zero fail-open paths, strict cryptographic digest checking,
deterministic pattern overlap detection, and 5-table cross-consistency.
"""

from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import enum
import hashlib
import base64
import rfc8785
import jsonschema

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class IntegritySeverity(enum.Enum):
    INVALID = "RULESET_INVALID"      # Schema, Non-Dict, Rule ID Dup, Crypto Failure
    REDUNDANT = "RULESET_REDUNDANT"  # Semantic Key Collision (K_sem)
    CONFLICT = "RULESET_CONFLICT"    # Mapping Collision, Scope/Pattern Overlap, Cross-Table Inconsistency
    MISSING = "RULESET_MISSING"      # Unresolved Target / Missing Evidence
    UNAVAILABLE = "SYSTEM_ERROR"     # Missing Required Universe / Evidence Store / Verification Key


@dataclass(frozen=True)
class CanonicalTargetUniverse:
    node_ids: Set[str] = field(default_factory=set)
    edge_ids: Set[str] = field(default_factory=set)
    spec_ids: Set[str] = field(default_factory=set)
    authority_ids: Set[str] = field(default_factory=set)

    def exists_in_any_universe(self, target_id: str) -> bool:
        return (target_id in self.node_ids or
                target_id in self.edge_ids or
                target_id in self.spec_ids or
                target_id in self.authority_ids)

    def resolve_typed_target(self, source_type: str, target_id: str) -> Tuple[bool, bool]:
        """
        Returns (exists_typed, exists_anywhere)
        """
        exists_any = self.exists_in_any_universe(target_id)
        if source_type in ("NODE", "ALIAS", "TRANSFORM"):
            exists_typed = target_id in self.node_ids
        elif source_type in ("EDGE", "RELATION_NORMALIZATION"):
            exists_typed = target_id in self.edge_ids
        elif source_type == "SPEC_BINDING":
            exists_typed = target_id in self.spec_ids
        elif source_type == "AUTHORITY":
            exists_typed = target_id in self.authority_ids
        else:
            exists_typed = False
        return exists_typed, exists_any


@dataclass(frozen=True)
class IntegrityViolation:
    rule_id: str
    invariant_id: str
    severity: IntegritySeverity
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GlobalIntegrityReport:
    status: str  # "PASS", "WARN", "FAIL"
    total_rules_scanned: int
    schema_valid_rules_count: int
    integrity_valid_rules_count: int
    violations: List[IntegrityViolation]

    @property
    def has_fatal_errors(self) -> bool:
        return any(
            v.severity in (IntegritySeverity.INVALID, IntegritySeverity.CONFLICT,
                           IntegritySeverity.MISSING, IntegritySeverity.UNAVAILABLE)
            for v in self.violations
        )


# --- Schemas ---

FRR_RULE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "rule_id", "source_type", "component_id",
        "record_scope", "normalized_pattern", "target_id", "evidence_ref"
    ],
    "additionalProperties": False,
    "properties": {
        "rule_id": {"type": "string", "minLength": 1},
        "source_type": {
            "type": "string",
            "enum": ["NODE", "EDGE", "ALIAS", "TRANSFORM", "RELATION_NORMALIZATION", "SPEC_BINDING", "AUTHORITY"]
        },
        "component_id": {"type": "string", "minLength": 1},
        "target_id": {"type": "string", "minLength": 1},
        "evidence_ref": {"type": "string", "minLength": 1},
        "record_scope": {
            "type": "object",
            "additionalProperties": False,
            "required": ["scope_type"],
            "properties": {
                "scope_type": {"type": "string", "enum": ["ALL", "EXACT_RECORD_INDICES"]},
                "record_indices": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"type": "integer", "minimum": 0}
                }
            },
            "allOf": [
                {
                    "if": {"properties": {"scope_type": {"const": "EXACT_RECORD_INDICES"}}},
                    "then": {"required": ["record_indices"]}
                },
                {
                    "if": {"properties": {"scope_type": {"const": "ALL"}}},
                    "then": {"not": {"required": ["record_indices"]}}
                }
            ]
        },
        "normalized_pattern": {
            "type": "object",
            "oneOf": [
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["type", "value"],
                    "properties": {
                        "type": {"const": "EXACT"},
                        "value": {"type": "string"}
                    }
                },
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["type", "prefix"],
                    "properties": {
                        "type": {"const": "PREFIX"},
                        "prefix": {"type": "string"}
                    }
                },
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["type", "suffix"],
                    "properties": {
                        "type": {"const": "SUFFIX"},
                        "suffix": {"type": "string"}
                    }
                },
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["type", "prefix", "allowed_chars"],
                    "properties": {
                        "type": {"const": "PREFIX_CHARSET"},
                        "prefix": {"type": "string"},
                        "allowed_chars": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {"type": "string", "minLength": 1, "maxLength": 1}
                        },
                        "min_suffix_len": {"type": "integer", "minimum": 0}
                    }
                }
            ]
        }
    }
}

FRR_PACKAGE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["ruleset_hash", "integrity", "rules"],
    "additionalProperties": False,
    "properties": {
        "ruleset_hash": {"type": "string", "minLength": 64, "maxLength": 64},
        "integrity": {
            "type": "object",
            "required": ["algorithm", "signature"],
            "additionalProperties": False,
            "properties": {
                "algorithm": {"type": "string", "const": "Ed25519"},
                "signature": {"type": "string", "minLength": 1}
            }
        },
        "rules": {
            "type": "array",
            "items": FRR_RULE_SCHEMA
        }
    }
}

RULE_VALIDATOR = jsonschema.Draft202012Validator(FRR_RULE_SCHEMA)
PACKAGE_VALIDATOR = jsonschema.Draft202012Validator(FRR_PACKAGE_SCHEMA)


def check_pattern_overlap(p1: Dict[str, Any], p2: Dict[str, Any]) -> bool:
    """Fully deterministic pattern overlap calculation without conservative fallback."""
    t1, t2 = p1["type"], p2["type"]
    
    # Normalize pair order alphabetically by type for unambiguous matching logic
    if t1 > t2:
        p1, p2 = p2, p1
        t1, t2 = p1["type"], p2["type"]

    if t1 == "EXACT" and t2 == "EXACT":
        return p1["value"] == p2["value"]
    
    if t1 == "EXACT" and t2 == "PREFIX":
        return p1["value"].startswith(p2["prefix"])
    
    if t1 == "EXACT" and t2 == "PREFIX_CHARSET":
        val = p1["value"]
        prefix = p2["prefix"]
        if not val.startswith(prefix):
            return False
        suffix = val[len(prefix):]
        if len(suffix) < p2.get("min_suffix_len", 0):
            return False
        allowed = set(p2["allowed_chars"])
        return all(c in allowed for c in suffix)

    if t1 == "EXACT" and t2 == "SUFFIX":
        return p1["value"].endswith(p2["suffix"])

    if t1 == "PREFIX" and t2 == "PREFIX":
        return p1["prefix"].startswith(p2["prefix"]) or p2["prefix"].startswith(p1["prefix"])

    if t1 == "PREFIX" and t2 == "PREFIX_CHARSET":
        return p1["prefix"].startswith(p2["prefix"]) or p2["prefix"].startswith(p1["prefix"])

    if t1 == "PREFIX" and t2 == "SUFFIX":
        return True  # Unbounded prefix and suffix can always overlap

    if t1 == "PREFIX_CHARSET" and t2 == "PREFIX_CHARSET":
        pr1, pr2 = p1["prefix"], p2["prefix"]
        if not (pr1.startswith(pr2) or pr2.startswith(pr1)):
            return False
        if p1.get("min_suffix_len", 0) > 0 and p2.get("min_suffix_len", 0) > 0:
            if set(p1["allowed_chars"]).isdisjoint(set(p2["allowed_chars"])):
                return False
        return True

    if t1 == "PREFIX_CHARSET" and t2 == "SUFFIX":
        return True

    if t1 == "SUFFIX" and t2 == "SUFFIX":
        return p1["suffix"].endswith(p2["suffix"]) or p2["suffix"].endswith(p1["suffix"])

    raise ValueError(f"Unhandled pattern comparison pair: {t1} vs {t2}")


class FRRIntegrityValidator:
    def __init__(
        self,
        target_universe: Optional[CanonicalTargetUniverse] = None,
        verification_key: Optional[Any] = None,
        known_evidence_ids: Optional[Set[str]] = None
    ):
        self.target_universe = target_universe
        self.verification_key = verification_key
        self.known_evidence_ids = known_evidence_ids

    def validate_ruleset_package(self, ruleset_package: Any) -> GlobalIntegrityReport:
        violations: List[IntegrityViolation] = []

        # Fail-Closed Prerequisites
        if not isinstance(ruleset_package, dict):
            return GlobalIntegrityReport(
                status="FAIL", total_rules_scanned=0, schema_valid_rules_count=0,
                integrity_valid_rules_count=0,
                violations=[IntegrityViolation("GLOBAL", "FR-INV-01", IntegritySeverity.INVALID, "Package root must be a dict.")]
            )

        if self.target_universe is None:
            violations.append(IntegrityViolation("GLOBAL", "FR-INV-07", IntegritySeverity.UNAVAILABLE, "TargetUniverse is None."))
        if self.known_evidence_ids is None:
            violations.append(IntegrityViolation("GLOBAL", "FR-INV-10", IntegritySeverity.UNAVAILABLE, "EvidenceStore (known_evidence_ids) is None."))
        if self.verification_key is None:
            violations.append(IntegrityViolation("GLOBAL", "FR-INV-02", IntegritySeverity.UNAVAILABLE, "TrustedVerificationKey is None: Fail-Closed enforced."))

        if any(v.severity == IntegritySeverity.UNAVAILABLE for v in violations):
            return GlobalIntegrityReport("FAIL", 0, 0, 0, violations)

        # -------------------------------------------------------------------
        # FR-INV-01: Root Package Schema Check
        # -------------------------------------------------------------------
        pkg_errors = list(PACKAGE_VALIDATOR.iter_errors(ruleset_package))
        if pkg_errors:
            violations.append(IntegrityViolation("GLOBAL", "FR-INV-01", IntegritySeverity.INVALID, f"Package Schema Error: {pkg_errors[0].message}"))
            return GlobalIntegrityReport("FAIL", 0, 0, 0, violations)

        # -------------------------------------------------------------------
        # FR-INV-02: Cryptographic Hash & Signature Verification
        # -------------------------------------------------------------------
        expected_hash = ruleset_package["ruleset_hash"]
        raw_signature = ruleset_package["integrity"]["signature"]

        clean_package = {k: v for k, v in ruleset_package.items() if k not in ("ruleset_hash", "integrity")}
        canonical_bytes = rfc8785.dumps(clean_package)
        computed_hash = hashlib.sha256(canonical_bytes).hexdigest()

        if computed_hash != expected_hash:
            violations.append(IntegrityViolation("GLOBAL", "FR-INV-02", IntegritySeverity.INVALID, f"Hash Mismatch: expected {expected_hash}, computed {computed_hash}"))

        if not CRYPTOGRAPHY_AVAILABLE:
            violations.append(IntegrityViolation("GLOBAL", "FR-INV-02", IntegritySeverity.INVALID, "Cryptography library unavailable."))
        else:
            try:
                sig_bytes = base64.b64decode(raw_signature, validate=True)
                digest = hashlib.sha256(canonical_bytes).digest()
                self.verification_key.verify(sig_bytes, digest)
            except Exception as e:
                violations.append(IntegrityViolation("GLOBAL", "FR-INV-02", IntegritySeverity.INVALID, f"Ed25519 Verification Failed: {str(e)}"))

        # -------------------------------------------------------------------
        # Stage 1: Individual Rule Integrity (FR-INV-01, 03a, 07, 08, 10)
        # -------------------------------------------------------------------
        raw_rules = ruleset_package["rules"]
        schema_valid_rules: List[Dict[str, Any]] = []
        seen_rule_ids: Set[str] = set()

        for idx, rule in enumerate(raw_rules):
            if not isinstance(rule, dict):
                violations.append(IntegrityViolation(f"INDEX_{idx}", "FR-INV-01", IntegritySeverity.INVALID, f"Rule at index {idx} is non-dict."))
                continue

            r_id = rule.get("rule_id", f"INDEX_{idx}")

            # FR-INV-03a: Global Rule ID Uniqueness
            if r_id in seen_rule_ids:
                violations.append(IntegrityViolation(r_id, "FR-INV-03a", IntegritySeverity.INVALID, f"Duplicate rule_id '{r_id}'."))
                continue
            seen_rule_ids.add(r_id)

            # FR-INV-07 vs FR-INV-08 Strict Disambiguation
            stype = rule["source_type"]
            target_id = rule["target_id"]
            exists_typed, exists_any = self.target_universe.resolve_typed_target(stype, target_id)

            if not exists_any:
                violations.append(IntegrityViolation(r_id, "FR-INV-07", IntegritySeverity.MISSING, f"Target '{target_id}' does not exist in any canonical universe."))
            elif not exists_typed:
                violations.append(IntegrityViolation(r_id, "FR-INV-08", IntegritySeverity.CONFLICT, f"Target '{target_id}' exists but is invalid for source_type '{stype}'."))

            # FR-INV-10: Evidence Existence Check
            ev_ref = rule["evidence_ref"]
            if ev_ref not in self.known_evidence_ids:
                violations.append(IntegrityViolation(r_id, "FR-INV-10", IntegritySeverity.MISSING, f"Evidence '{ev_ref}' not found in EvidenceStore."))

            schema_valid_rules.append(rule)

        # -------------------------------------------------------------------
        # Stage 2: Cross-Rule & 5-Table Invariants (FR-INV-03b, 04, 05, 06, 09)
        # -------------------------------------------------------------------
        semantic_key_map: Dict[Tuple[str, str, bytes, bytes, str], str] = {}
        cross_table_domain_map: Dict[Tuple[str, bytes, bytes], List[Tuple[str, str, str]]] = defaultdict(list)
        active_rules: List[Tuple[str, str, str, Dict[str, Any], Dict[str, Any], str]] = []
        integrity_valid_count = 0

        FIVE_TABLE_TYPES = {"ALIAS", "TRANSFORM", "SPEC_BINDING", "RELATION_NORMALIZATION", "AUTHORITY"}

        for rule in schema_valid_rules:
            r_id = rule["rule_id"]
            stype = rule["source_type"]
            comp_id = rule["component_id"]
            target_id = rule["target_id"]

            norm_scope = dict(rule["record_scope"])
            if "record_indices" in norm_scope:
                norm_scope["record_indices"] = sorted(list(set(norm_scope["record_indices"])))

            norm_pattern = dict(rule["normalized_pattern"])
            if "allowed_chars" in norm_pattern:
                norm_pattern["allowed_chars"] = sorted(list(set(norm_pattern["allowed_chars"])))

            scope_jcs = rfc8785.dumps(norm_scope)
            pattern_jcs = rfc8785.dumps(norm_pattern)

            # FR-INV-03b: Semantic Rule Redundancy
            k_sem = (stype, comp_id, scope_jcs, pattern_jcs, target_id)
            if k_sem in semantic_key_map:
                violations.append(IntegrityViolation(r_id, "FR-INV-03b", IntegritySeverity.REDUNDANT, f"Redundant with rule '{semantic_key_map[k_sem]}'." ))
            else:
                semantic_key_map[k_sem] = r_id

            domain_key = (comp_id, scope_jcs, pattern_jcs)

            # FR-INV-04 / 05: Single Source Type Direct Mapping Conflict
            for exist_stype, exist_target, exist_rid in cross_table_domain_map[domain_key]:
                if exist_stype == stype and exist_target != target_id:
                    inv = "FR-INV-04" if stype in ("ALIAS", "TRANSFORM") else ("FR-INV-05" if stype == "RELATION_NORMALIZATION" else "FR-INV-09")
                    violations.append(IntegrityViolation(r_id, inv, IntegritySeverity.CONFLICT, f"Conflicting target '{target_id}' vs '{exist_target}' in rule '{exist_rid}'."))

            # FR-INV-09: 5-Table Inter-Table Cross-Consistency Check
            if stype in FIVE_TABLE_TYPES:
                for exist_stype, exist_target, exist_rid in cross_table_domain_map[domain_key]:
                    if exist_stype in FIVE_TABLE_TYPES and exist_stype != stype and exist_target != target_id:
                        violations.append(IntegrityViolation(r_id, "FR-INV-09", IntegritySeverity.CONFLICT, f"Cross-Table Conflict: {stype} maps to '{target_id}' while {exist_stype} ({exist_rid}) maps to '{exist_target}'."))

            cross_table_domain_map[domain_key].append((stype, target_id, r_id))

            # FR-INV-06: Scope Overlap AND Pattern Overlap Conflict
            curr_scope = rule["record_scope"]
            curr_pattern = rule["normalized_pattern"]
            for ex_id, ex_stype, ex_comp, ex_scope, ex_pattern, ex_target in active_rules:
                if ex_comp == comp_id and ex_target != target_id:
                    scope_overlaps = False
                    if curr_scope["scope_type"] == "ALL" or ex_scope["scope_type"] == "ALL":
                        scope_overlaps = True
                    elif curr_scope["scope_type"] == "EXACT_RECORD_INDICES" and ex_scope["scope_type"] == "EXACT_RECORD_INDICES":
                        if not set(curr_scope["record_indices"]).isdisjoint(set(ex_scope["record_indices"])):
                            scope_overlaps = True

                    if scope_overlaps and check_pattern_overlap(curr_pattern, ex_pattern):
                        violations.append(IntegrityViolation(r_id, "FR-INV-06", IntegritySeverity.CONFLICT, f"Scope/Pattern overlap ambiguity with rule '{ex_id}' on component '{comp_id}' mapping to different targets."))

            active_rules.append((r_id, stype, comp_id, curr_scope, curr_pattern, target_id))

            if not any(v.rule_id == r_id and v.severity in (IntegritySeverity.INVALID, IntegritySeverity.CONFLICT, IntegritySeverity.MISSING) for v in violations):
                integrity_valid_count += 1

        has_fatal = any(v.severity in (IntegritySeverity.INVALID, IntegritySeverity.CONFLICT, IntegritySeverity.MISSING, IntegritySeverity.UNAVAILABLE) for v in violations)
        status = "FAIL" if has_fatal else ("WARN" if violations else "PASS")

        return GlobalIntegrityReport(
            status=status,
            total_rules_scanned=len(raw_rules),
            schema_valid_rules_count=len(schema_valid_rules),
            integrity_valid_rules_count=integrity_valid_count,
            violations=violations
        )