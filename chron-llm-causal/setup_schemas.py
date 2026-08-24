import os
import json

delta1_extraction = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "delta1-extraction.schema.json",
    "title": "Delta1 Extraction Record",
    "description": "Raw extraction results from Phase B/Step 1. Contains proposals, not validated graph structures.",
    "type": "object",
    "required": ["document_ids", "extraction_type", "proposals"],
    "additionalProperties": False,
    "properties": {
        "$schema": { "type": "string" },
        "schema_version": { "type": "string" },
        "document_ids": {
            "type": "array",
            "items": { "type": "string" }
        },
        "extraction_type": {
            "type": "string",
            "enum": ["causal_dependency"]
        },
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "source", "target", "evidence"],
                "additionalProperties": False,
                "properties": {
                    "id": { "type": "string" },
                    "type": { "type": "string" },
                    "claim_type": {
                        "description": "Normalized type from step0_ssot.ClaimType. Optional for legacy data.",
                        "type": "string",
                        "enum": ["UNIT", "REQUIRES", "DEPENDS_ON"]
                    },
                    "source": { "type": "string" },
                    "target": { "type": "string" },
                    "direction": { "type": "string" },
                    "evidence": { "type": "string" },
                    "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
                    "related_invariants": {
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "notes": { "type": "string" },
                    "parse_status": {
                        "type": "string",
                        "enum": ["VALID_CLAIM", "BLANK_LINE", "COMMENT_LINE", "NOT_A_CANDIDATE", "INVALID_CONTEXT", "INVALID_GRAMMAR"]
                    }
                }
            }
        },
        "key_invariants_detected": {
            "type": "array",
            "items": { "type": "string" }
        },
        "authority_boundaries": {
            "type": "array",
            "items": { "type": "string" }
        },
        "open_questions": {
            "type": "array",
            "items": { "type": "string" }
        }
    }
}

delta1_graph = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "delta1-graph.schema.json",
    "title": "Delta1 Graph",
    "description": "Intermediate graph structure generated from Delta1 Extraction. Pre-integration with Delta2.",
    "type": "object",
    "required": ["nodes", "edges"],
    "properties": {
        "$schema": { "type": "string" },
        "schema_version": { "type": "string" },
        "source_extraction_id": { "type": "string" },
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "label"],
                "properties": {
                    "id": { "type": "string" },
                    "label": { "type": "string" },
                    "category": { "type": "string" },
                    "description": { "type": "string" },
                    "provenance": { "type": "object" }
                }
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "from", "to"],
                "properties": {
                    "id": { "type": "string" },
                    "from": { "type": "string" },
                    "to": { "type": "string" },
                    "relation": { "type": "string" },
                    "evidence": { "type": "string" },
                    "confidence": { "type": "number" }
                }
            }
        }
    }
}

delta2_mastergraph = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "delta2-mastergraph.schema.json",
    "title": "Delta2 MasterGraph",
    "description": "Integrated and normalized master graph.",
    "type": "object",
    "required": ["nodes", "edges"],
    "properties": {
        "$schema": { "type": "string" },
        "schema_version": { "type": "string" },
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "name"],
                "properties": {
                    "id": { "type": "string" },
                    "global_id": { "type": "string" },
                    "local_id": { "type": "string" },
                    "type": {
                        "type": "string",
                        "enum": [
                            "invariant", "operation", "state", "authority",
                            "function", "type_def", "component"
                        ]
                    },
                    "name": { "type": "string" },
                    "description": { "type": "string" },
                    "properties": { "type": "object" },
                    "provenance": { "type": "object" }
                }
            }
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "from", "to"],
                "properties": {
                    "id": { "type": "string" },
                    "from": { "type": "string" },
                    "to": { "type": "string" },
                    "pipeline": { "type": "string" },
                    "morphism_type": {
                        "type": "string",
                        "enum": [
                            "authority_boundary", "causal_flow", "data_dependency",
                            "invariant", "dependency", "constraint", "defines"  # <-- 追加
                        ]
                    },
                    "guard_invariant": {
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "delta_level": { "type": "string" }
                }
            }
        }
    }
}

traceability = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "traceability.schema.json",
    "title": "Delta1 to Delta2 Traceability",
    "description": "Verification of mapping from Delta1 artifacts to Delta2 MasterGraph.",
    "type": "object",
    "properties": {
        "$schema": { "type": "string" },
        "audit_version": { "type": "string" },
        "status": { "type": "string" },
        "canonical_freeze": { "type": "string" },
        "target_mastergraph": { "type": "string" },
        "machine_checks": { "type": "object" },
        "delta2_nodes_provenance": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "delta2_node_id": { "type": "string" },
                    "source_delta1_node_ids": {
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "provenance_complete": { "type": "boolean" }
                }
            }
        },
        "delta2_edges_provenance": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "delta2_edge_id": { "type": "string" },
                    "source_delta1_edge_ids": {
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "provenance_complete": { "type": "boolean" }
                }
            }
        }
    }
}

os.makedirs("schemas", exist_ok=True)
files = {
    "schemas/delta1-extraction.schema.json": delta1_extraction,
    "schemas/delta1-graph.schema.json": delta1_graph,
    "schemas/delta2-mastergraph.schema.json": delta2_mastergraph,
    "schemas/traceability.schema.json": traceability
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    print(f"Updated: {path}")