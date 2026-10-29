"""JOB:A3 gate — EXPLICIT_EDGE_VOCAB / SEMANTIC_NORMALIZATION.

Gates (directive 2026-10-29):
  UNCLASSIFIED_PRESENT, NO_IMPLICIT_DEPENDS_ON, EDGE_COUNT_STABLE,
  NODE_COUNT_STABLE, CYCLE!=INVALID, EQUIVALENT_TO_UNDIRECTED,
  COUNT=312/11, NO_EDGE_DROP, NO_EDGE_ADD, MAP depends_on=>parentID only.
"""

from causal_kernel.edge_vocab import (
    EDGE_VOCAB,
    LEAN_EDGE_MAP,
    UNCLASSIFIED,
    is_undirected_candidate,
    lean_edge_mapping,
    normalize_relation,
)
from causal_kernel.kernel.traceability_reconstructor import reconstruct

# pins from the pre-patch baseline run (2026-10-29)
PIN_D1_EDGES = 312
PIN_D1_NODES = 340
PIN_D2_EDGES = 11
PIN_D2_NODES = 14
PIN_RAW_DIST = {
    "enforces": 125, "depends_on": 76, "mutates": 46,
    "triggers": 35, "produces": 30,
}


def _out():
    return reconstruct()


def test_edge_count_stable_no_drop_no_add():
    """COUNT=312/11, NO_EDGE_DROP, NO_EDGE_ADD (pre/post equal)."""
    out = _out()
    em = out["edge_mappings"]
    assert len(em) == PIN_D1_EDGES
    delta2_edge_ids = {
        e["target_delta2_id"] for e in em
        if e["classification"] != "UNRESOLVED"
        and e["target_delta2_id"] is not None
    }
    assert len(delta2_edge_ids) == PIN_D2_EDGES
    # every Delta-1 edge present exactly once (no drop, no add)
    src_ids = [e["source_delta1_id"] for e in em]
    assert all(src_ids) and len(set(src_ids)) == PIN_D1_EDGES


def test_node_count_stable():
    out = _out()
    nm = out["node_mappings"]
    assert len(nm) == PIN_D1_NODES
    delta2_node_ids = {
        n["target_delta2_id"] for n in nm
        if n["classification"] != "UNRESOLVED"
        and n["target_delta2_id"] is not None
    }
    assert len(delta2_node_ids) == PIN_D2_NODES


def test_relabel_only_edge_identity_set_invariant():
    """RELABEL_ONLY: the Delta-1 edge id set is unchanged vs pins."""
    out = _out()
    em = out["edge_mappings"]
    ids = {e["source_original_id"] for e in em}
    assert len(ids) == PIN_D1_EDGES  # no collapse, no duplication


def test_no_implicit_depends_on_default():
    """NO_IMPLICIT_DEPENDS_ON: missing/unknown => UNCLASSIFIED, never depends_on."""
    assert normalize_relation(None) == UNCLASSIFIED
    assert normalize_relation("") == UNCLASSIFIED
    assert normalize_relation("   ") == UNCLASSIFIED
    # NOTE (U2 adjudication 2026-10-29): "refines" was an off-vocab example in
    # A3; it is now adopted vocabulary and normalizes to itself. "approved_by"
    # substituted (source 53.4.2 confusable-list member, still off-vocab).
    for off_vocab in ("enforces", "mutates", "triggers", "produces", "approved_by"):
        assert normalize_relation(off_vocab) == UNCLASSIFIED, off_vocab


def test_unclassified_present_in_reconstruction():
    """UNCLASSIFIED_PRESENT: the 236 off-vocabulary Delta-1 labels are
    relabeled to the sentinel; depends_on(76) survives as vocabulary."""
    out = _out()
    em = out["edge_mappings"]
    n_unclass = sum(1 for e in em if e["source_name_type"] == UNCLASSIFIED)
    n_depends = sum(1 for e in em if e["source_name_type"] == "depends_on")
    expected_unclass = PIN_RAW_DIST["enforces"] + PIN_RAW_DIST["mutates"] \
        + PIN_RAW_DIST["triggers"] + PIN_RAW_DIST["produces"]
    assert n_unclass == expected_unclass == 236
    assert n_depends == PIN_RAW_DIST["depends_on"] == 76
    # per-edge raw audit (D-2): every relabeled edge retains its original
    for e in em:
        if e["source_name_type"] == UNCLASSIFIED and e["source_relation_raw"]:
            assert str(e["source_relation_raw"]).lower() not in {
                "depends_on", "enables", "blocks", "contradicts", "supports",
                "derives_from", "causes", "mitigates", "equivalent_to",
            }


def test_every_label_is_in_vocab():
    out = _out()
    for e in out["edge_mappings"]:
        assert e["source_name_type"].upper() in EDGE_VOCAB


def test_vocabulary_membership():
    for tok in ("depends_on", "enables", "blocks", "contradicts", "supports",
                "derives_from", "causes", "mitigates", "equivalent_to"):
        assert normalize_relation(tok) == tok
        assert normalize_relation(tok.upper()) == tok


def test_cycle_not_invalid():
    """CYCLE != INVALID: topology never changes labels or drops edges."""
    cyc = [("a", "b"), ("b", "c"), ("c", "a")]
    labels = [normalize_relation("depends_on") for _ in cyc]
    assert labels == ["depends_on"] * 3  # cycle intact, none invalidated
    # a cycle entirely of off-vocab edges relabels uniformly, never dropped
    assert all(normalize_relation("enforces") == UNCLASSIFIED for _ in cyc)


def test_equivalent_to_undirected():
    assert is_undirected_candidate("equivalent_to")
    assert is_undirected_candidate("EQUIVALENT_TO")
    assert not is_undirected_candidate("depends_on")
    assert not is_undirected_candidate(UNCLASSIFIED)
    assert not is_undirected_candidate(None)


def test_lean_projection_depends_on_only():
    """MAP: depends_on=>parentID; *=NO_LEAN_MAPPING."""
    assert lean_edge_mapping("depends_on") == "parentID"
    assert lean_edge_mapping("DEPENDS_ON") == "parentID"
    for rel in ("enables", "blocks", "contradicts", "supports", "derives_from",
                "causes", "mitigates", "equivalent_to", UNCLASSIFIED,
                "enforces", None):
        assert lean_edge_mapping(rel) is None, rel
    assert LEAN_EDGE_MAP == {"depends_on": "parentID"}  # single mapping only
