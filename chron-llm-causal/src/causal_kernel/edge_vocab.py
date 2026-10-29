"""Explicit causal-edge vocabulary (A3 / G-07 semantic normalization).

JOB:A3 MODE:SEMANTIC_NORMALIZATION OBJ:EXPLICIT_EDGE_VOCAB
Adopted vocabulary (directive 2026-10-29, extended by U1-U3 adjudications
2026-10-29: REQUIRES / REFINES / REFERENCES adopted verbatim, no collapse —
source 53.4.2 explicit non-identification rules REFERENCES != DEPENDS_ON,
DEPENDS_ON != REQUIRES are honored; REFINES adopted because the live
phase6 extractor already emits it):

    DEPENDS_ON  ENABLES  BLOCKS  CONTRADICTS  SUPPORTS
    DERIVES_FROM  CAUSES  MITIGATES  EQUIVALENT_TO  UNCLASSIFIED
    REQUIRES  REFINES  REFERENCES

Rules:
  NO_IMPLICIT_DEFAULT - a missing/unknown relation NEVER becomes depends_on;
    it becomes the UNCLASSIFIED sentinel (D-2 adjudication: sentinel +
    per-edge raw audit).
  RELABEL_ONLY        - normalization changes labels only. Edges are never
    dropped or added; node/edge counts are invariant.
  CYCLE != INVALID    - normalization is topology-blind; a cycle never
    invalidates or relabels an edge.
  EQUIVALENT_TO       - undirected candidate (direction is an artifact of
    writing order; see is_undirected_candidate).
  MAP                 - only depends_on projects to the frozen Lean
    CausalRecord.parentID; every other label has NO_LEAN_MAPPING.

Token case policy: in-vocabulary members keep the canonical lowercase token
(existing lineage/consumer strings stay byte-stable); the sentinel is the
uppercase string "UNCLASSIFIED", unmistakable against any data value.
"""

EDGE_VOCAB = frozenset({
    "DEPENDS_ON", "ENABLES", "BLOCKS", "CONTRADICTS", "SUPPORTS",
    "DERIVES_FROM", "CAUSES", "MITIGATES", "EQUIVALENT_TO", "UNCLASSIFIED",
    # U1-U3 (2026-10-29 adjudication: vocabulary adoption, RAWPRESERVE)
    "REQUIRES", "REFINES", "REFERENCES",
})

UNCLASSIFIED = "UNCLASSIFIED"

# canonical lowercase tokens for in-vocabulary values
_VOCAB_LOWER = frozenset({
    "depends_on", "enables", "blocks", "contradicts", "supports",
    "derives_from", "causes", "mitigates", "equivalent_to", "unclassified",
    # U1-U3 (2026-10-29 adjudication: vocabulary adoption, RAWPRESERVE)
    "requires", "refines", "references",
})

# Lean projection policy: exactly one label maps onto CausalRecord.parentID.
# Any other label (incl. UNCLASSIFIED) => NO_LEAN_MAPPING (None).
LEAN_EDGE_MAP = {"depends_on": "parentID"}

# CYCLE != INVALID: nothing in normalization may invalidate an edge because
# of graph topology.
CYCLE_INVALIDATES_EDGE = False


def normalize_relation(raw) -> str:
    """Map a raw relation label onto the adopted vocabulary.

    missing/empty    -> UNCLASSIFIED (NO_IMPLICIT_DEFAULT)
    in-vocabulary    -> canonical lowercase token
    out-of-vocabulary-> UNCLASSIFIED (per-edge raw audit retains the original)
    """
    if raw is None:
        return UNCLASSIFIED
    token = str(raw).strip().lower()
    if not token:
        return UNCLASSIFIED
    if token in _VOCAB_LOWER:
        return token
    return UNCLASSIFIED


def is_undirected_candidate(relation) -> bool:
    """EQUIVALENT_TO edges are undirected candidates."""
    return relation is not None and str(relation).strip().lower() == "equivalent_to"


def lean_edge_mapping(relation):
    """Lean projection: depends_on => 'parentID', everything else None."""
    if relation is None:
        return None
    return LEAN_EDGE_MAP.get(str(relation).strip().lower())
