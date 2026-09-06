"""
FRR Global Integrity Validator (v1.2-Strict-Contract)
Chron-LLM Causal Kernel / Traceability Suite

Implements FR-INV-01 .. FR-INV-10.

Design principles:
- Fail closed.
- rule_type and source_type are distinct dimensions.
- RFC 8785 JCS is used for canonicalization.
- ruleset_hash is SHA-256(JCS(rules)).
- Ed25519 signs the JCS canonical package:
    {
        "ruleset_hash": ...,
        "integrity": {"algorithm": "Ed25519"},
        "rules": [...]
    }
- Pattern overlap is exact for the supported pattern language.
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import enum
import hashlib
import binascii

import rfc8785
import jsonschema

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    ed25519 = None
    CRYPTOGRAPHY_AVAILABLE = False


# ============================================================================
# Severity / report models
# ============================================================================

class IntegritySeverity(enum.Enum):
    INVALID = "RULESET_INVALID"
    REDUNDANT = "RULESET_REDUNDANT"
    CONFLICT = "RULESET_CONFLICT"
    MISSING = "RULESET_MISSING"
    UNAVAILABLE = "SYSTEM_ERROR"


@dataclass(frozen=True)
class CanonicalTargetUniverse:
    """
    Canonical target namespaces are intentionally disjoint by entity type.
    """

    node_ids: Set[str] = field(default_factory=set)
    edge_ids: Set[str] = field(default_factory=set)
    spec_ids: Set[str] = field(default_factory=set)
    authority_ids: Set[str] = field(default_factory=set)

    def exists_in_any_universe(self, target_id: str) -> bool:
        return (
            target_id in self.node_ids
            or target_id in self.edge_ids
            or target_id in self.spec_ids
            or target_id in self.authority_ids
        )

    def resolve_typed_target(
        self,
        source_type: str,
        target_id: str,
    ) -> Tuple[bool, bool]:
        """
        Returns:
            (exists_typed, exists_anywhere)
        """

        exists_any = self.exists_in_any_universe(target_id)

        if source_type == "NODE":
            exists_typed = target_id in self.node_ids
        elif source_type == "EDGE":
            exists_typed = target_id in self.edge_ids
        elif source_type == "SPEC":
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
    status: str
    total_rules_scanned: int
    schema_valid_rules_count: int
    integrity_valid_rules_count: int
    violations: List[IntegrityViolation]

    @property
    def has_fatal_errors(self) -> bool:
        return any(
            v.severity in (
                IntegritySeverity.INVALID,
                IntegritySeverity.CONFLICT,
                IntegritySeverity.MISSING,
                IntegritySeverity.UNAVAILABLE,
            )
            for v in self.violations
        )


# ============================================================================
# Schemas
# ============================================================================

FRR_RULE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "FRR Rule",
    "type": "object",

    "required": [
        "rule_id",
        "rule_type",
        "source_type",
        "component_id",
        "record_scope",
        "normalized_pattern",
        "target_id",
        "evidence_ref",
    ],

    "additionalProperties": False,

    "properties": {
        "rule_id": {
            "type": "string",
            "minLength": 1,
        },

        # Rule-table / semantic operation domain.
        "rule_type": {
            "type": "string",
            "enum": [
                "ALIAS",
                "TRANSFORM",
                "RELATION_NORMALIZATION",
                "SPEC_BINDING",
                "AUTHORITY",
            ],
        },

        # Target entity type.
        "source_type": {
            "type": "string",
            "enum": [
                "NODE",
                "EDGE",
                "SPEC",
                "AUTHORITY",
            ],
        },

        "component_id": {
            "type": "string",
            "minLength": 1,
        },

        "record_scope": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "scope_type",
            ],

            "properties": {
                "scope_type": {
                    "type": "string",
                    "enum": [
                        "ALL",
                        "EXACT_RECORD_INDICES",
                    ],
                },

                "record_indices": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {
                        "type": "integer",
                        "minimum": 0,
                    },
                },
            },

            "allOf": [
                {
                    "if": {
                        "properties": {
                            "scope_type": {
                                "const": "EXACT_RECORD_INDICES",
                            },
                        },
                        "required": ["scope_type"],
                    },
                    "then": {
                        "required": ["record_indices"],
                    },
                },
                {
                    "if": {
                        "properties": {
                            "scope_type": {
                                "const": "ALL",
                            },
                        },
                        "required": ["scope_type"],
                    },
                    "then": {
                        "not": {
                            "required": ["record_indices"],
                        },
                    },
                },
            ],
        },

        "normalized_pattern": {
            "type": "object",

            "oneOf": [
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "type",
                        "value",
                    ],
                    "properties": {
                        "type": {
                            "const": "EXACT",
                        },
                        "value": {
                            "type": "string",
                        },
                    },
                },

                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "type",
                        "prefix",
                    ],
                    "properties": {
                        "type": {
                            "const": "PREFIX",
                        },
                        "prefix": {
                            "type": "string",
                        },
                    },
                },

                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "type",
                        "suffix",
                    ],
                    "properties": {
                        "type": {
                            "const": "SUFFIX",
                        },
                        "suffix": {
                            "type": "string",
                        },
                    },
                },

                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "type",
                        "prefix",
                        "allowed_chars",
                    ],
                    "properties": {
                        "type": {
                            "const": "PREFIX_CHARSET",
                        },
                        "prefix": {
                            "type": "string",
                        },
                        "allowed_chars": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 1,
                            },
                        },
                        "min_suffix_len": {
                            "type": "integer",
                            "minimum": 0,
                        },
                    },
                },
            ],
        },

        "target_id": {
            "type": "string",
            "minLength": 1,
        },

        "evidence_ref": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },
    },
}


FRR_PACKAGE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "FRR Ruleset Package",
    "type": "object",

    "required": [
        "ruleset_hash",
        "integrity",
        "rules",
    ],

    "additionalProperties": False,

    "properties": {
        "ruleset_hash": {
            "type": "string",
            "pattern": "^[0-9a-fA-F]{64}$",
        },

        "integrity": {
            "type": "object",
            "additionalProperties": False,

            "required": [
                "algorithm",
                "signature",
            ],

            "properties": {
                "algorithm": {
                    "type": "string",
                    "const": "Ed25519",
                },

                "signature": {
                    "type": "string",
                    "pattern": "^[0-9a-fA-F]{128}$",
                },
            },
        },

        "rules": {
            "type": "array",
            "items": FRR_RULE_SCHEMA,
        },
    },
}


RULE_VALIDATOR = jsonschema.Draft202012Validator(FRR_RULE_SCHEMA)
PACKAGE_VALIDATOR = jsonschema.Draft202012Validator(FRR_PACKAGE_SCHEMA)


# ============================================================================
# RFC 8785 JCS helpers
# ============================================================================

def jcs_bytes(obj: Any) -> bytes:
    """
    RFC 8785 JSON Canonicalization Scheme.
    """
    result = rfc8785.dumps(obj)

    if not isinstance(result, bytes):
        raise TypeError("rfc8785.dumps() must return bytes")

    return result


def canonicalize_scope(scope: Dict[str, Any]) -> bytes:
    """
    Canonical scope representation.

    record_indices are normalized as a sorted unique sequence.
    """
    normalized = dict(scope)

    if "record_indices" in normalized:
        normalized["record_indices"] = sorted(
            set(normalized["record_indices"])
        )

    return jcs_bytes(normalized)


def canonicalize_pattern(pattern: Dict[str, Any]) -> bytes:
    """
    Canonical pattern representation.

    allowed_chars are normalized as sorted unique characters.
    """
    normalized = dict(pattern)

    if "allowed_chars" in normalized:
        normalized["allowed_chars"] = sorted(
            set(normalized["allowed_chars"])
        )

    return jcs_bytes(normalized)


def compute_ruleset_hash(rules: List[Dict[str, Any]]) -> str:
    """
    FR-INV-02:
        SHA-256(JCS(rules))
    """
    return hashlib.sha256(jcs_bytes(rules)).hexdigest()


def build_signature_payload(
    ruleset_package: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Exact Ed25519 signing payload.

    integrity.signature itself is excluded.
    """
    return {
        "ruleset_hash": ruleset_package["ruleset_hash"],
        "integrity": {
            "algorithm": ruleset_package["integrity"]["algorithm"],
        },
        "rules": ruleset_package["rules"],
    }


# ============================================================================
# Pattern language
# ============================================================================

def _pc_prefix(pattern: Dict[str, Any]) -> str:
    return pattern["prefix"]


def _pc_allowed(pattern: Dict[str, Any]) -> Set[str]:
    return set(pattern["allowed_chars"])


def _pc_min_suffix_len(pattern: Dict[str, Any]) -> int:
    return int(pattern.get("min_suffix_len", 0))


def _prefix_charset_language_accepts(
    pattern: Dict[str, Any],
    candidate: str,
) -> bool:
    """
    Exact membership test for:

        PREFIX_CHARSET(prefix, allowed_chars, min_suffix_len)

    Language:

        prefix + one or more/zero additional characters,
        where:
          - first character after prefix is in allowed_chars
          - total suffix length >= min_suffix_len

    Note:
    min_suffix_len is interpreted as the minimum number of characters
    following prefix. The first suffix character is constrained by
    allowed_chars.
    """

    prefix = _pc_prefix(pattern)
    allowed = _pc_allowed(pattern)
    min_suffix_len = _pc_min_suffix_len(pattern)

    if not candidate.startswith(prefix):
        return False

    suffix = candidate[len(prefix):]

    if len(suffix) < min_suffix_len:
        return False

    # A PREFIX_CHARSET always requires the first suffix character.
    if not suffix:
        return False

    return suffix[0] in allowed


def check_pattern_overlap(
    p1: Dict[str, Any],
    p2: Dict[str, Any],
) -> bool:
    """
    Exact deterministic intersection test for the supported languages:

        EXACT
        PREFIX
        PREFIX_CHARSET
        SUFFIX

    Returns True iff there exists at least one string accepted by both
    patterns.

    Raises ValueError for unsupported pattern types.
    """

    t1 = p1["type"]
    t2 = p2["type"]

    supported = {
        "EXACT",
        "PREFIX",
        "PREFIX_CHARSET",
        "SUFFIX",
    }

    if t1 not in supported or t2 not in supported:
        raise ValueError(
            f"Unsupported pattern type pair: {t1} vs {t2}"
        )

    # ------------------------------------------------------------------
    # EXACT × EXACT
    # ------------------------------------------------------------------
    if t1 == "EXACT" and t2 == "EXACT":
        return p1["value"] == p2["value"]

    # ------------------------------------------------------------------
    # EXACT × PREFIX
    # ------------------------------------------------------------------
    if t1 == "EXACT" and t2 == "PREFIX":
        return p1["value"].startswith(p2["prefix"])

    if t1 == "PREFIX" and t2 == "EXACT":
        return check_pattern_overlap(p2, p1)

    # ------------------------------------------------------------------
    # EXACT × PREFIX_CHARSET
    # ------------------------------------------------------------------
    if t1 == "EXACT" and t2 == "PREFIX_CHARSET":
        return _prefix_charset_language_accepts(
            p2,
            p1["value"],
        )

    if t1 == "PREFIX_CHARSET" and t2 == "EXACT":
        return check_pattern_overlap(p2, p1)

    # ------------------------------------------------------------------
    # EXACT × SUFFIX
    # ------------------------------------------------------------------
    if t1 == "EXACT" and t2 == "SUFFIX":
        return p1["value"].endswith(p2["suffix"])

    if t1 == "SUFFIX" and t2 == "EXACT":
        return check_pattern_overlap(p2, p1)

    # ------------------------------------------------------------------
    # PREFIX × PREFIX
    # ------------------------------------------------------------------
    if t1 == "PREFIX" and t2 == "PREFIX":
        a = p1["prefix"]
        b = p2["prefix"]

        return a.startswith(b) or b.startswith(a)

    # ------------------------------------------------------------------
    # PREFIX × PREFIX_CHARSET
    # ------------------------------------------------------------------
    if t1 == "PREFIX" and t2 == "PREFIX_CHARSET":
        prefix = p1["prefix"]
        pc_prefix = p2["prefix"]
        allowed = _pc_allowed(p2)
        min_suffix_len = _pc_min_suffix_len(p2)

        # Case 1:
        # PREFIX is strictly inside the PC prefix.
        #
        # Example:
        #   PREFIX("abc")
        #   PC("abcd", allowed={"x"})
        #
        # Every PREFIX string starts "abc", but PC requires "abcd..."
        # so overlap exists only if the PREFIX language can supply the
        # required next character and satisfy min_suffix_len.
        if pc_prefix.startswith(prefix):
            required = pc_prefix[len(prefix):]

            # PREFIX must contain the entire required extension.
            # Since PREFIX accepts arbitrary continuation, this is possible
            # provided the PC prefix itself satisfies its own first
            # post-prefix character constraint.
            if not required:
                # Equal prefix is handled below.
                return True

            if required[0] not in allowed:
                return False

            if min_suffix_len > 0 and len(required) < min_suffix_len:
                # PREFIX can extend after pc_prefix, therefore it can
                # satisfy min_suffix_len.
                return True

            return True

        # Case 2:
        # PREFIX is longer than the PC prefix.
        #
        # Example:
        #   PREFIX("abcd")
        #   PC("ab", allowed={"x"})
        #
        # The character at position len("ab") is fixed to "c".
        # It must belong to the charset.
        if prefix.startswith(pc_prefix):
            extension = prefix[len(pc_prefix):]

            if not extension:
                return True

            if extension[0] not in allowed:
                return False

            # The fixed extension already contributes to the PC suffix.
            # If it is shorter than min_suffix_len, PREFIX can extend
            # arbitrarily, so overlap remains possible.
            return True

        return False

    if t1 == "PREFIX_CHARSET" and t2 == "PREFIX":
        return check_pattern_overlap(p2, p1)

    # ------------------------------------------------------------------
    # PREFIX × SUFFIX
    # ------------------------------------------------------------------
    if t1 == "PREFIX" and t2 == "SUFFIX":
        # Overlap is always non-empty over an unconstrained string alphabet.
        return True

    if t1 == "SUFFIX" and t2 == "PREFIX":
        return True

    # ------------------------------------------------------------------
    # PREFIX_CHARSET × PREFIX_CHARSET
    # ------------------------------------------------------------------
    if t1 == "PREFIX_CHARSET" and t2 == "PREFIX_CHARSET":
        a = p1["prefix"]
        b = p2["prefix"]

        aa = _pc_allowed(p1)
        ab = _pc_allowed(p2)

        min_a = _pc_min_suffix_len(p1)
        min_b = _pc_min_suffix_len(p2)

        # Equal prefixes:
        #
        # Both languages constrain the first suffix character.
        # Therefore an intersection exists iff the allowed character
        # sets intersect.
        if a == b:
            if not (aa & ab):
                return False

            # Arbitrary continuation can satisfy both minimum lengths.
            return True

        # a is a prefix of b.
        #
        # Example:
        #   PC1 = "ab"  allowed={"x"}
        #   PC2 = "abc" allowed={"y"}
        #
        # The first suffix character required by PC1 is fixed by the
        # next character of b ("c"). Therefore "c" must be allowed by
        # PC1.
        if b.startswith(a):
            extension = b[len(a):]

            if not extension:
                return True

            first_required = extension[0]

            if first_required not in aa:
                return False

            # Once b is reached, PC2 constrains the next character.
            # We can choose a character in ab and extend arbitrarily.
            return bool(ab)

        # b is a prefix of a.
        if a.startswith(b):
            extension = a[len(b):]

            if not extension:
                return True

            first_required = extension[0]

            if first_required not in ab:
                return False

            return bool(aa)

        return False

    # ------------------------------------------------------------------
    # PREFIX_CHARSET × SUFFIX
    # ------------------------------------------------------------------
    if t1 == "PREFIX_CHARSET" and t2 == "SUFFIX":
        # PC accepts arbitrarily long continuations after its constrained
        # first suffix character. Therefore a string can always be chosen
        # that also ends with the required suffix.
        return True

    if t1 == "SUFFIX" and t2 == "PREFIX_CHARSET":
        return True

    # ------------------------------------------------------------------
    # SUFFIX × SUFFIX
    # ------------------------------------------------------------------
    if t1 == "SUFFIX" and t2 == "SUFFIX":
        a = p1["suffix"]
        b = p2["suffix"]

        return a.endswith(b) or b.endswith(a)

    raise ValueError(
        f"Unhandled pattern comparison pair: {t1} vs {t2}"
    )


# ============================================================================
# Scope language
# ============================================================================

def check_scope_overlap(
    s1: Dict[str, Any],
    s2: Dict[str, Any],
) -> bool:
    """
    Exact overlap for the record-scope language.
    """

    t1 = s1["scope_type"]
    t2 = s2["scope_type"]

    if t1 == "ALL" or t2 == "ALL":
        return True

    if (
        t1 == "EXACT_RECORD_INDICES"
        and t2 == "EXACT_RECORD_INDICES"
    ):
        return not set(s1["record_indices"]).isdisjoint(
            set(s2["record_indices"])
        )

    raise ValueError(
        f"Unhandled scope comparison: {t1} vs {t2}"
    )


# ============================================================================
# Validator
# ============================================================================

class FRRIntegrityValidator:

    FIVE_TABLE_TYPES = {
        "ALIAS",
        "TRANSFORM",
        "RELATION_NORMALIZATION",
        "SPEC_BINDING",
        "AUTHORITY",
    }

    def __init__(
        self,
        target_universe: Optional[CanonicalTargetUniverse] = None,
        verification_key: Optional[Any] = None,
        known_evidence_ids: Optional[Set[str]] = None,
    ):
        self.target_universe = target_universe
        self.verification_key = verification_key
        self.known_evidence_ids = known_evidence_ids

    # ------------------------------------------------------------------
    # FR-INV-02 signature verification
    # ------------------------------------------------------------------

    def _verify_signature(
        self,
        ruleset_package: Dict[str, Any],
    ) -> Optional[str]:

        if not CRYPTOGRAPHY_AVAILABLE:
            return "Cryptography library unavailable."

        if self.verification_key is None:
            return "TrustedVerificationKey is None."

        signature_hex = ruleset_package["integrity"]["signature"]

        try:
            signature = bytes.fromhex(signature_hex)
        except ValueError as exc:
            return f"Signature is not valid hexadecimal: {exc}"

        payload = build_signature_payload(ruleset_package)
        canonical_bytes = jcs_bytes(payload)

        try:
            self.verification_key.verify(
                signature,
                canonical_bytes,
            )
        except Exception as exc:
            return f"Ed25519 Verification Failed: {exc}"

        return None

    # ------------------------------------------------------------------
    # Validation entry point
    # ------------------------------------------------------------------

    def validate_ruleset_package(
        self,
        ruleset_package: Any,
    ) -> GlobalIntegrityReport:

        violations: List[IntegrityViolation] = []

        # ==============================================================
        # Fail-Closed Prerequisites
        # ==============================================================

        if not isinstance(ruleset_package, dict):
            return GlobalIntegrityReport(
                status="FAIL",
                total_rules_scanned=0,
                schema_valid_rules_count=0,
                integrity_valid_rules_count=0,
                violations=[
                    IntegrityViolation(
                        "GLOBAL",
                        "FR-INV-01",
                        IntegritySeverity.INVALID,
                        "Package root must be a dict.",
                    )
                ],
            )

        if self.target_universe is None:
            violations.append(
                IntegrityViolation(
                    "GLOBAL",
                    "FR-INV-07",
                    IntegritySeverity.UNAVAILABLE,
                    "TargetUniverse is None.",
                )
            )

        if self.known_evidence_ids is None:
            violations.append(
                IntegrityViolation(
                    "GLOBAL",
                    "FR-INV-10",
                    IntegritySeverity.UNAVAILABLE,
                    "EvidenceStore is None.",
                )
            )

        if self.verification_key is None:
            violations.append(
                IntegrityViolation(
                    "GLOBAL",
                    "FR-INV-02",
                    IntegritySeverity.UNAVAILABLE,
                    "TrustedVerificationKey is None.",
                )
            )

        if not CRYPTOGRAPHY_AVAILABLE:
            violations.append(
                IntegrityViolation(
                    "GLOBAL",
                    "FR-INV-02",
                    IntegritySeverity.UNAVAILABLE,
                    "Required cryptographic library is unavailable.",
                )
            )

        if violations:
            return GlobalIntegrityReport(
                status="FAIL",
                total_rules_scanned=0,
                schema_valid_rules_count=0,
                integrity_valid_rules_count=0,
                violations=violations,
            )

        # ==============================================================
        # FR-INV-01: Package Schema
        # ==============================================================

        pkg_errors = list(
            PACKAGE_VALIDATOR.iter_errors(ruleset_package)
        )

        if pkg_errors:
            first = pkg_errors[0]

            return GlobalIntegrityReport(
                status="FAIL",
                total_rules_scanned=0,
                schema_valid_rules_count=0,
                integrity_valid_rules_count=0,
                violations=[
                    IntegrityViolation(
                        "GLOBAL",
                        "FR-INV-01",
                        IntegritySeverity.INVALID,
                        f"Package Schema Error: {first.message}",
                        {
                            "path": list(first.path),
                        },
                    )
                ],
            )

        # ==============================================================
        # FR-INV-02: Cryptographic Integrity
        # ==============================================================

        raw_rules = ruleset_package["rules"]
        expected_hash = ruleset_package["ruleset_hash"]

        computed_hash = compute_ruleset_hash(raw_rules)

        if computed_hash != expected_hash:
            return GlobalIntegrityReport(
                status="FAIL",
                total_rules_scanned=len(raw_rules),
                schema_valid_rules_count=0,
                integrity_valid_rules_count=0,
                violations=[
                    IntegrityViolation(
                        "GLOBAL",
                        "FR-INV-02",
                        IntegritySeverity.INVALID,
                        (
                            "Hash mismatch: "
                            f"expected={expected_hash}, "
                            f"computed={computed_hash}"
                        ),
                    )
                ],
            )

        signature_error = self._verify_signature(
            ruleset_package
        )

        if signature_error is not None:
            return GlobalIntegrityReport(
                status="FAIL",
                total_rules_scanned=len(raw_rules),
                schema_valid_rules_count=0,
                integrity_valid_rules_count=0,
                violations=[
                    IntegrityViolation(
                        "GLOBAL",
                        "FR-INV-02",
                        IntegritySeverity.INVALID,
                        signature_error,
                    )
                ],
            )

        # ==============================================================
        # Stage 1:
        # Individual rule integrity
        #
        # FR-INV-01
        # FR-INV-03a
        # FR-INV-07
        # FR-INV-08
        # FR-INV-10
        # ==============================================================

        schema_valid_rules: List[Dict[str, Any]] = []
        seen_rule_ids: Set[str] = set()

        for idx, rule in enumerate(raw_rules):

            if not isinstance(rule, dict):
                violations.append(
                    IntegrityViolation(
                        f"INDEX_{idx}",
                        "FR-INV-01",
                        IntegritySeverity.INVALID,
                        f"Rule at index {idx} is not an object.",
                    )
                )
                continue

            rule_errors = list(
                RULE_VALIDATOR.iter_errors(rule)
            )

            if rule_errors:
                first = rule_errors[0]

                violations.append(
                    IntegrityViolation(
                        rule.get(
                            "rule_id",
                            f"INDEX_{idx}",
                        ),
                        "FR-INV-01",
                        IntegritySeverity.INVALID,
                        f"Rule Schema Error: {first.message}",
                        {
                            "path": list(first.path),
                        },
                    )
                )
                continue

            rule_id = rule["rule_id"]

            # ----------------------------------------------------------
            # FR-INV-03a: unique rule_id
            # ----------------------------------------------------------

            if rule_id in seen_rule_ids:
                violations.append(
                    IntegrityViolation(
                        rule_id,
                        "FR-INV-03a",
                        IntegritySeverity.INVALID,
                        f"Duplicate rule_id '{rule_id}'.",
                    )
                )
                continue

            seen_rule_ids.add(rule_id)

            # ----------------------------------------------------------
            # FR-INV-07 / FR-INV-08
            # ----------------------------------------------------------

            source_type = rule["source_type"]
            target_id = rule["target_id"]

            exists_typed, exists_any = (
                self.target_universe.resolve_typed_target(
                    source_type,
                    target_id,
                )
            )

            if not exists_any:
                violations.append(
                    IntegrityViolation(
                        rule_id,
                        "FR-INV-07",
                        IntegritySeverity.MISSING,
                        (
                            f"Target '{target_id}' does not exist "
                            "in any canonical target universe."
                        ),
                    )
                )
            elif not exists_typed:
                violations.append(
                    IntegrityViolation(
                        rule_id,
                        "FR-INV-08",
                        IntegritySeverity.CONFLICT,
                        (
                            f"Target '{target_id}' exists, but is "
                            f"not valid for source_type "
                            f"'{source_type}'."
                        ),
                    )
                )

            # ----------------------------------------------------------
            # FR-INV-10: every evidence_ref must exist
            # ----------------------------------------------------------

            for evidence_ref in rule["evidence_ref"]:
                if evidence_ref not in self.known_evidence_ids:
                    violations.append(
                        IntegrityViolation(
                            rule_id,
                            "FR-INV-10",
                            IntegritySeverity.MISSING,
                            (
                                f"Evidence '{evidence_ref}' "
                                "not found in EvidenceStore."
                            ),
                        )
                    )

            schema_valid_rules.append(rule)

        # ==============================================================
        # Stage 2:
        # Cross-rule invariants
        #
        # FR-INV-03b
        # FR-INV-04
        # FR-INV-05
        # FR-INV-06
        # FR-INV-09
        # ==============================================================

        semantic_key_map: Dict[
            Tuple[str, str, bytes, bytes, str],
            str,
        ] = {}

        active_rules: List[
            Tuple[
                str,                 # rule_id
                str,                 # rule_type
                str,                 # source_type
                str,                 # component_id
                Dict[str, Any],      # scope
                Dict[str, Any],      # pattern
                str,                 # target_id
            ]
        ] = []

        for rule in schema_valid_rules:

            rule_id = rule["rule_id"]
            rule_type = rule["rule_type"]
            source_type = rule["source_type"]
            component_id = rule["component_id"]
            target_id = rule["target_id"]
            scope = rule["record_scope"]
            pattern = rule["normalized_pattern"]

            canonical_scope = canonicalize_scope(scope)
            canonical_pattern = canonicalize_pattern(pattern)

            # ----------------------------------------------------------
            # FR-INV-03b
            #
            # K_sem =
            # (
            #   source_type,
            #   component_id,
            #   canonical_scope,
            #   canonical_pattern,
            #   target_id
            # )
            # ----------------------------------------------------------

            semantic_key = (
                source_type,
                component_id,
                canonical_scope,
                canonical_pattern,
                target_id,
            )

            if semantic_key in semantic_key_map:
                violations.append(
                    IntegrityViolation(
                        rule_id,
                        "FR-INV-03b",
                        IntegritySeverity.REDUNDANT,
                        (
                            "Semantic Key collision with rule "
                            f"'{semantic_key_map[semantic_key]}'."
                        ),
                    )
                )
            else:
                semantic_key_map[semantic_key] = rule_id

            # ----------------------------------------------------------
            # Compare with previously active rules.
            # ----------------------------------------------------------

            for (
                ex_id,
                ex_rule_type,
                ex_source_type,
                ex_component_id,
                ex_scope,
                ex_pattern,
                ex_target_id,
            ) in active_rules:

                # Different components have disjoint input domains.
                if ex_component_id != component_id:
                    continue

                scope_overlaps = check_scope_overlap(
                    scope,
                    ex_scope,
                )

                if not scope_overlaps:
                    continue

                pattern_overlaps = check_pattern_overlap(
                    pattern,
                    ex_pattern,
                )

                if not pattern_overlaps:
                    continue

                # ------------------------------------------------------
                # At this point:
                #
                # same component
                # AND
                # overlapping scope
                # AND
                # overlapping pattern
                #
                # FR-INV-06 establishes the deterministic overlap.
                # The actual conflict classification follows.
                # ------------------------------------------------------

                same_rule_type = (
                    rule_type == ex_rule_type
                )

                same_target = (
                    source_type == ex_source_type
                    and target_id == ex_target_id
                )

                # ------------------------------------------------------
                # FR-INV-09
                #
                # Cross-table collision is invalid whenever the
                # rule_type differs, INCLUDING when target identity
                # happens to be the same.
                # ------------------------------------------------------

                if not same_rule_type:
                    violations.append(
                        IntegrityViolation(
                            rule_id,
                            "FR-INV-09",
                            IntegritySeverity.CONFLICT,
                            (
                                "Cross-table collision: "
                                f"{rule_type} overlaps "
                                f"{ex_rule_type} on the same "
                                "component/scope/pattern domain."
                            ),
                            {
                                "existing_rule_id": ex_id,
                                "existing_rule_type": ex_rule_type,
                                "existing_target_id": ex_target_id,
                                "current_target_id": target_id,
                                "same_target": same_target,
                            },
                        )
                    )

                    continue

                # ------------------------------------------------------
                # Same rule_type + same typed target:
                #
                # Allowed at this stage. Exact semantic duplication
                # is already handled by FR-INV-03b.
                # ------------------------------------------------------

                if same_target:
                    continue

                # ------------------------------------------------------
                # FR-INV-04
                #
                # ALIAS / TRANSFORM conflicting targets.
                # ------------------------------------------------------

                if rule_type in {
                    "ALIAS",
                    "TRANSFORM",
                }:
                    violations.append(
                        IntegrityViolation(
                            rule_id,
                            "FR-INV-04",
                            IntegritySeverity.CONFLICT,
                            (
                                "Single-domain target conflict: "
                                f"{rule_type} rule overlaps rule "
                                f"'{ex_id}' but resolves to a "
                                "different target."
                            ),
                            {
                                "existing_target_id": ex_target_id,
                                "current_target_id": target_id,
                            },
                        )
                    )

                # ------------------------------------------------------
                # FR-INV-05
                #
                # RELATION_NORMALIZATION conflicting targets.
                # ------------------------------------------------------

                elif rule_type == "RELATION_NORMALIZATION":
                    violations.append(
                        IntegrityViolation(
                            rule_id,
                            "FR-INV-05",
                            IntegritySeverity.CONFLICT,
                            (
                                "Relation normalization conflict: "
                                "overlapping scope/pattern resolves "
                                "to different targets."
                            ),
                            {
                                "existing_target_id": ex_target_id,
                                "current_target_id": target_id,
                            },
                        )
                    )

            active_rules.append(
                (
                    rule_id,
                    rule_type,
                    source_type,
                    component_id,
                    scope,
                    pattern,
                    target_id,
                )
            )

        # ==============================================================
        # Final status
        # ==============================================================

        has_fatal = any(
            v.severity in (
                IntegritySeverity.INVALID,
                IntegritySeverity.CONFLICT,
                IntegritySeverity.MISSING,
                IntegritySeverity.UNAVAILABLE,
            )
            for v in violations
        )

        status = "FAIL" if has_fatal else (
            "WARN" if violations else "PASS"
        )

        integrity_valid_count = 0

        for rule in schema_valid_rules:
            rule_id = rule["rule_id"]

            if not any(
                v.rule_id == rule_id
                and v.severity in (
                    IntegritySeverity.INVALID,
                    IntegritySeverity.CONFLICT,
                    IntegritySeverity.MISSING,
                )
                for v in violations
            ):
                integrity_valid_count += 1

        return GlobalIntegrityReport(
            status=status,
            total_rules_scanned=len(raw_rules),
            schema_valid_rules_count=len(schema_valid_rules),
            integrity_valid_rules_count=integrity_valid_count,
            violations=violations,
        )