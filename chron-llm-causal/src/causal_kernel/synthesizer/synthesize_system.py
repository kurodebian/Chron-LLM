#!/usr/bin/env python3
"""
Chron-LLM Causal Kernel - System Causal Synthesizer & Validator (v1.0 CI Ready)
Merges component causal graphs, extracts Delta-0 boundaries, and strictly validates
L1/L2 causal algebraic constraints against CAUSAL_SPECIFICATION_MATRIX.md.
"""

from __future__ import annotations
import os
import json
import glob
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple


def sanitize_id(raw_id: str) -> str:
    """Sanitizes strings to be safe for identifiers."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', raw_id)


def escape_mermaid_label(text: str) -> str:
    """Escapes quotes and brackets to prevent Mermaid syntax errors."""
    if not text:
        return ""
    escaped = str(text).replace('"', '#quot;').replace('[', '&#91;').replace(']', '&#93;')
    return repr(escaped)[1:-1]


class SystemCausalSynthesizer:
    ALLOWED_MORPISMS = {
        "CommitPipeline": {"authority_boundary", "operational", "constraint", "invariant"},
        "DerivePipeline": {"operational", "dependency", "constraint", "invariant"},
        "RuntimePipeline": {"operational", "dependency", "constraint", "invariant"},
        "Meta": {"defines"},
    }

    def __init__(self):
        self.global_nodes: Dict[str, Dict[str, Any]] = {}
        self.node_lookup: Dict[str, str] = {}
        self.edges: List[Dict[str, Any]] = []
        self.components: Set[str] = set()

    def load_master_or_component_files(self, input_path_or_pattern: str) -> None:
        """
        Loads input graph JSON files. Handles both single master graph files
        (e.g., causal_master_graph_v2.json) and component glob patterns.
        """
        files = sorted(glob.glob(input_path_or_pattern))
        if not files and os.path.exists(input_path_or_pattern):
            files = [input_path_or_pattern]

        if not files:
            raise FileNotFoundError(f"No files found matching: {input_path_or_pattern}")

        print(f"[Synthesizer] Loading {len(files)} graph specification file(s)...")

        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "nodes" in data:
                nodes_data = data["nodes"]
                edges_data = data.get("edges", [])
                
                if isinstance(nodes_data, dict):
                    nodes_data = list(nodes_data.values())
            else:
                continue

            comp_id = sanitize_id(data.get("component_id", Path(filepath).stem))
            self.components.add(comp_id)

            for node in nodes_data:
                raw_node_id = node.get("id", node.get("global_id", ""))
                safe_node_id = sanitize_id(raw_node_id)
                global_id = node.get("global_id", f"{comp_id}__{safe_node_id}")

                self.global_nodes[global_id] = {
                    "global_id": global_id,
                    "local_id": safe_node_id,
                    "component_id": node.get("component_id", comp_id),
                    "type": node.get("type", "Unknown"),
                    "name": node.get("name", safe_node_id),
                    "description": node.get("description", ""),
                    "is_boundary": node.get("is_boundary", False),
                    "properties": node.get("properties", {})
                }
                self.node_lookup[global_id.lower()] = global_id
                self.node_lookup[safe_node_id.lower()] = global_id

            for edge in edges_data:
                edge_copy = dict(edge)
                edge_copy.setdefault("from_component", comp_id)
                edge_copy.setdefault("to_component", comp_id)
                edge_copy.setdefault("delta_level", "DELTA_1" if edge_copy["from_component"] == edge_copy["to_component"] else "DELTA_0")
                self.edges.append(edge_copy)

    def verify_causal_core(
        self,
        target_pipeline: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validates L2 closure and L1 invariants (CAUSAL_SPECIFICATION_MATRIX.md v1.0).
        Supports filtering by target pipeline.
        Returns (is_valid, list_of_violation_report_dicts).
        """
        violations: List[Dict[str, Any]] = []

        for idx, edge in enumerate(self.edges):
            edge_id = edge.get("id", f"EDGE_{idx:04d}")
            pipeline = edge.get("pipeline")
            mtype = edge.get("morphism_type")

            if target_pipeline and pipeline != target_pipeline:
                continue

            # 1. Pipeline Morphism Authorization
            if pipeline in self.ALLOWED_MORPISMS:
                if mtype not in self.ALLOWED_MORPISMS[pipeline]:
                    violations.append({
                        "edge_id": edge_id,
                        "code": "ERR_L2_INVALID_MORPHISM",
                        "pipeline": pipeline,
                        "morphism_type": mtype,
                        "message": f"Morphism '{mtype}' is not permitted in pipeline '{pipeline}'."
                    })
            elif pipeline:
                violations.append({
                    "edge_id": edge_id,
                    "code": "ERR_L2_UNKNOWN_PIPELINE",
                    "pipeline": pipeline,
                    "morphism_type": mtype,
                    "message": f"Unknown pipeline context '{pipeline}'."
                })

            # 2. DerivePipeline Purity Axiom
            if pipeline == "DerivePipeline" and mtype == "authority_boundary":
                violations.append({
                    "edge_id": edge_id,
                    "code": "ERR_PURE_DERIVE_VIOLATION",
                    "pipeline": pipeline,
                    "morphism_type": mtype,
                    "message": "DerivePipeline must be strictly pure and cannot contain 'authority_boundary' morphisms."
                })

            # 3. Guard Invariant Requirement for Constraint Morphisms
            if mtype == "constraint":
                guards = edge.get("guard_invariant")
                if not guards:
                    violations.append({
                        "edge_id": edge_id,
                        "code": "ERR_MISSING_CONSTRAINT_GUARD",
                        "pipeline": pipeline,
                        "morphism_type": mtype,
                        "message": "Constraint morphism requires a non-empty 'guard_invariant' reference."
                    })

            # 4. Authority Guard Attachment Axiom (Two-Stage Property Resolution)
            if mtype == "authority_boundary":
                guards = edge.get("guard_invariant", [])
                if isinstance(guards, str):
                    guards = [guards]
                
                has_valid_auth = False
                for g in guards:
                    if not isinstance(g, str):
                        continue
                    
                    # Legacy Direct Token Check
                    if g.startswith("AUTH-"):
                        has_valid_auth = True
                        break

                    # Canonical Two-Stage Resolution: Invariant ID -> Node Lookup -> guard_token
                    node_key = self.node_lookup.get(g.lower(), g)
                    node = self.global_nodes.get(node_key)
                    
                    if not node:
                        for n in self.global_nodes.values():
                            if n.get("local_id") == g or n.get("global_id") == g:
                                node = n
                                break

                    if node:
                        token = node.get("properties", {}).get("guard_token", "")
                        if isinstance(token, str) and token.startswith("AUTH-"):
                            has_valid_auth = True
                            break

                if not has_valid_auth:
                    violations.append({
                        "edge_id": edge_id,
                        "code": "ERR_MISSING_AUTH_GUARD",
                        "pipeline": pipeline,
                        "morphism_type": mtype,
                        "message": "Authority boundary morphism must reference an 'AUTH-*' guard invariant."
                    })

        is_valid = len(violations) == 0
        return is_valid, violations

    def build_summary_stats(self) -> Dict[str, Any]:
        """Calculates system topology stats."""
        delta1_count = sum(1 for e in self.edges if e.get("delta_level") == "DELTA_1")
        delta0_count = sum(1 for e in self.edges if e.get("delta_level") == "DELTA_0")
        return {
            "total_components": len(self.components),
            "total_nodes": len(self.global_nodes),
            "total_edges": len(self.edges),
            "delta_1_internal_edges": delta1_count,
            "delta_0_boundary_edges": delta0_count,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Chron-LLM Causal Kernel Validator & Synthesizer (CI/CD Ready)"
    )
    parser.add_argument("--input", type=str, default="data/graphs/causal_master_graph_v2.json",
                        help="Path or glob pattern for master graph or component specs")
    parser.add_argument("--pipeline", type=str, choices=["CommitPipeline", "DerivePipeline", "RuntimePipeline", "Meta"],
                        default=None, help="Filter validation strictly to a single pipeline")
    parser.add_argument("--out_report_json", type=str, default=None,
                        help="Export structured validation violation report to JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with non-zero code (exit 1) on validation failure for CI integration")

    args = parser.parse_args()

    synthesizer = SystemCausalSynthesizer()
    try:
        synthesizer.load_master_or_component_files(args.input)
    except Exception as e:
        print(f"[Error] Failed to load graph: {e}")
        sys.exit(1)

    # Verification Phase
    filter_desc = f" [{args.pipeline}]" if args.pipeline else ""
    print(f"\n[Validator] Executing Causal Core v1.0 Algebraic Verification{filter_desc}...")
    is_valid, violations = synthesizer.verify_causal_core(target_pipeline=args.pipeline)

    # Export Violation Report if requested
    if args.out_report_json:
        report_data = {
            "input_source": args.input,
            "target_pipeline_filter": args.pipeline,
            "is_valid": is_valid,
            "violation_count": len(violations),
            "violations": violations
        }
        os.makedirs(os.path.dirname(os.path.abspath(args.out_report_json)), exist_ok=True)
        with open(args.out_report_json, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"[Validator] Violation report exported -> {args.out_report_json}")

    # Display Results
    stats = synthesizer.build_summary_stats()
    print("\n" + "="*55)
    print("      CHRON-LLM CAUSAL CORE VALIDATION SUMMARY")
    print("="*55)
    print(f" Target Input        : {args.input}")
    print(f" Total Nodes / Edges : {stats['total_nodes']} / {stats['total_edges']}")
    print(f" Pipeline Filter     : {args.pipeline or 'ALL (Full Coverage)'}")
    print(f" Validation Status   : {'PASSED (Valid Causal Core)' if is_valid else 'FAILED (Violations Found)'}")
    print(f" Violations Count    : {len(violations)}")
    print("="*55)

    if not is_valid:
        print("\n[Violations Detail]")
        for v in violations:
            print(f"  - [{v['code']}] Edge: {v['edge_id']} | {v['message']}")
        print("="*55 + "\n")
        
        if args.strict:
            sys.exit(1)
    else:
        print("\n[Success] All L1/L2 morphism and pipeline closure axioms hold.\n")


if __name__ == "__main__":
    main()