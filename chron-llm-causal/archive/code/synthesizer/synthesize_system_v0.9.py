#!/usr/bin/env python3
"""
Chron-LLM Causal Kernel - System Causal Synthesizer
Merges multiple Delta-1 component causal graphs into a unified System Causal Network
and extracts Delta-0 boundary interfaces and cross-component edges.
"""

import os
import json
import glob
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set


def sanitize_id(raw_id: str) -> str:
    """Sanitizes strings to be safe for identifiers."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', raw_id)


def escape_mermaid_label(text: str) -> str:
    """Escapes quotes and brackets to prevent Mermaid syntax errors."""
    if not text:
        return ""
    escaped = str(text).replace('"', '#quot;').replace('[', '&#91;').replace(']', '&#93;')
    escaped = repr(escaped)[1:-1]  # escape newlines and unprintable characters
    return escaped


class SystemCausalSynthesizer:
    def __init__(self):
        # global_node_id -> Node Dict
        self.global_nodes: Dict[str, Dict[str, Any]] = {}
        # lookup_key -> global_node_id (for fuzzy/canonical matching)
        self.node_lookup: Dict[str, str] = {}
        # List of unified edges
        self.edges: List[Dict[str, Any]] = []
        # Registered components metadata
        self.components: Set[str] = set()

    def load_component_files(self, input_pattern: str) -> None:
        """Loads all component spec JSON files matching the input file pattern."""
        files = sorted(glob.glob(input_pattern))
        if not files:
            raise FileNotFoundError(f"No JSON files matched pattern: {input_pattern}")

        print(f"[Synthesizer] Found {len(files)} component spec JSON files.")

        # Pass 1: Index all explicit Delta-1 nodes across all components
        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            comp_id = sanitize_id(data.get("component_id", Path(filepath).stem))
            self.components.add(comp_id)

            nodes = data.get("nodes", [])
            print(f"  - Loading {comp_id} ({len(nodes)} nodes)...")

            for node in nodes:
                raw_node_id = node.get("id", "")
                safe_node_id = sanitize_id(raw_node_id)
                global_id = f"{comp_id}__{safe_node_id}"

                node_entry = {
                    "global_id": global_id,
                    "local_id": safe_node_id,
                    "component_id": comp_id,
                    "type": node.get("type", "Unknown"),
                    "name": node.get("name", safe_node_id),
                    "description": node.get("description", ""),
                    "is_boundary": False
                }

                self.global_nodes[global_id] = node_entry

                # Register lookup keys for matching
                self.node_lookup[global_id.lower()] = global_id
                self.node_lookup[safe_node_id.lower()] = global_id
                self.node_lookup[f"{comp_id}_{safe_node_id}".lower()] = global_id
                self.node_lookup[f"{comp_id}:{safe_node_id}".lower()] = global_id

        # Pass 2: Extract and categorize edges (Delta-1 vs Delta-0)
        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            comp_id = sanitize_id(data.get("component_id", Path(filepath).stem))
            edges = data.get("edges", [])

            for edge in edges:
                raw_from = edge.get("from", "")
                raw_to = edge.get("to", "")
                edge_type = edge.get("type", "depends_on")
                description = edge.get("description", "")

                from_global = self._resolve_node_reference(raw_from, current_comp=comp_id)
                to_global = self._resolve_node_reference(raw_to, current_comp=comp_id)

                from_comp = self.global_nodes[from_global]["component_id"]
                to_comp = self.global_nodes[to_global]["component_id"]

                # Categorize Delta Level
                if from_comp == to_comp:
                    delta_level = "DELTA_1"  # Internal edge
                else:
                    delta_level = "DELTA_0"  # Inter-component boundary edge
                    self.global_nodes[from_global]["is_boundary"] = True
                    self.global_nodes[to_global]["is_boundary"] = True

                self.edges.append({
                    "from": from_global,
                    "to": to_global,
                    "from_component": from_comp,
                    "to_component": to_comp,
                    "type": edge_type,
                    "delta_level": delta_level,
                    "description": description
                })

    def _resolve_node_reference(self, raw_ref: str, current_comp: str) -> str:
        """Resolves a raw edge reference to its canonical global node ID."""
        safe_ref = sanitize_id(raw_ref)
        
        # 1. Check exact key matches
        candidates = [
            f"{current_comp}__{safe_ref}".lower(),
            safe_ref.lower(),
            f"{current_comp}_{safe_ref}".lower()
        ]

        for cand in candidates:
            if cand in self.node_lookup:
                return self.node_lookup[cand]

        # 2. Check if reference explicitly embeds another component ID
        for comp in self.components:
            if safe_ref.lower().startswith(comp.lower()):
                suffix = safe_ref[len(comp):].lstrip("_")
                key = f"{comp}__{suffix}".lower()
                if key in self.node_lookup:
                    return self.node_lookup[key]

        # 3. If unresolved, register as External Boundary Interface Node (Delta-0 Interface)
        ext_comp = "EXTERNAL_BOUNDARY"
        ext_global_id = f"{ext_comp}__{safe_ref}"

        if ext_global_id not in self.global_nodes:
            self.global_nodes[ext_global_id] = {
                "global_id": ext_global_id,
                "local_id": safe_ref,
                "component_id": ext_comp,
                "type": "ExternalInterface",
                "name": raw_ref,
                "description": "Auto-created boundary interface for cross-component reference",
                "is_boundary": True
            }
            self.node_lookup[ext_global_id.lower()] = ext_global_id
            self.node_lookup[safe_ref.lower()] = ext_global_id

        return ext_global_id

    def build_summary_stats(self) -> Dict[str, Any]:
        """Calculates system graph topology metrics and cross-component coupling matrix."""
        delta1_count = sum(1 for e in self.edges if e["delta_level"] == "DELTA_1")
        delta0_count = sum(1 for e in self.edges if e["delta_level"] == "DELTA_0")

        coupling_matrix: Dict[str, Dict[str, int]] = {}
        for edge in self.edges:
            if edge["delta_level"] == "DELTA_0":
                src = edge["from_component"]
                dst = edge["to_component"]
                coupling_matrix.setdefault(src, {}).setdefault(dst, 0)
                coupling_matrix[src][dst] += 1

        return {
            "total_components": len(self.components),
            "total_nodes": len(self.global_nodes),
            "total_edges": len(self.edges),
            "delta_1_internal_edges": delta1_count,
            "delta_0_boundary_edges": delta0_count,
            "cross_component_coupling_matrix": coupling_matrix
        }

    def export_json(self, output_path: str) -> None:
        """Saves the unified system causal graph as a structured JSON file."""
        stats = self.build_summary_stats()
        output_data = {
            "system_name": "Chron-LLM Unified Causal Network",
            "summary_stats": stats,
            "nodes": list(self.global_nodes.values()),
            "edges": self.edges
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"[Synthesizer] Unified system JSON exported -> {output_path}")

    def export_mermaid(self, output_path: str) -> None:
        """Generates a structured Mermaid diagram file with subgraphs and Delta-0 edge highlights."""
        lines = ["flowchart TD"]

        # Define edge styles for different edge types
        edge_styles = {
            "depends_on": "-->",
            "mutates": "==>",
            "enforces": "-.->",
            "triggers": "-- triggers -->",
            "produces": "-->"
        }

        # Group nodes by component
        nodes_by_comp: Dict[str, List[Dict[str, Any]]] = {}
        for node in self.global_nodes.values():
            nodes_by_comp.setdefault(node["component_id"], []).append(node)

        # Build Subgraphs per Component
        for comp_id, nodes in nodes_by_comp.items():
            comp_label = escape_mermaid_label(comp_id)
            lines.append(f'    subgraph {comp_id} ["Component: {comp_label}"]')
            for n in nodes:
                gid = n["global_id"]
                label = escape_mermaid_label(f"[{n['type']}] {n['name']}")
                
                # Shape variations based on node type
                if n["type"].lower() == "state":
                    node_def = f'        {gid}[("{label}")]'
                elif n["type"].lower() == "operation":
                    node_def = f'        {gid}["{label}"]'
                elif n["type"].lower() == "invariant":
                    node_def = f'        {gid}{{"{label}"}}'
                else:
                    node_def = f'        {gid}[/{label}/]'

                lines.append(node_def)
            lines.append("    end\n")

        # Add Edges
        for idx, edge in enumerate(self.edges):
            src = edge["from"]
            dst = edge["to"]
            etype = edge["type"]
            arrow = edge_styles.get(etype, "-->")
            
            lines.append(f"    {src} {arrow} {dst}")

            # Highlight Delta-0 boundary edges using linkStyle
            if edge["delta_level"] == "DELTA_0":
                lines.append(f"    linkStyle {idx} stroke:#ff0055,stroke-width:3px,color:#ff0055;")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[Synthesizer] System Mermaid diagram exported -> {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Chron-LLM Delta-0/Delta-1 Causal Network Synthesizer")
    parser.add_argument("--input_pattern", type=str, default="output/component_specs/component-*.json",
                        help="Glob pattern for component spec JSON files")
    parser.add_argument("--out_json", type=str, default="output/system_causal_network.json",
                        help="Output path for unified system JSON")
    parser.add_argument("--out_mermaid", type=str, default="output/system_causal_network.mmd",
                        help="Output path for system Mermaid diagram")

    args = parser.parse_args()

    synthesizer = SystemCausalSynthesizer()
    synthesizer.load_component_files(args.input_pattern)
    synthesizer.export_json(args.out_json)
    synthesizer.export_mermaid(args.out_mermaid)

    # Print summary to stdout
    stats = synthesizer.build_summary_stats()
    print("\n" + "="*50)
    print("      SYSTEM CAUSAL NETWORK SYNTHESIS SUMMARY")
    print("="*50)
    print(f" Total Components      : {stats['total_components']}")
    print(f" Total Global Nodes    : {stats['total_nodes']}")
    print(f" Total Internal (Δ1)   : {stats['delta_1_internal_edges']} edges")
    print(f" Total Boundary (Δ0)   : {stats['delta_0_boundary_edges']} edges")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()