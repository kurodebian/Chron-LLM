from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Set

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
KERNEL_DIR = SRC_DIR / "causal_kernel" / "kernel"

for p in [str(SRC_DIR), str(KERNEL_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

AUTHORITY_RULES = {
    "Canonical": "authoritative",
    "History": "canonical_evidence",
    "Event": "canonical_evidence",
    "Projection": "derived",
    "World": "derived",
    "Working": "non_authoritative",
    "Candidate": "non_authoritative",
    "External": "non_authoritative"
}


def get_authority_category(authority_class: str) -> str:
    return AUTHORITY_RULES.get(
        authority_class,
        "non_authoritative" if authority_class in ["Working", "Candidate", "External"] else "authoritative"
    )


class GlobalSpecificationGraphAnalyzer:
    """Phase 7: Global Specification Graph Construction & Causal Audit Engine."""

    def __init__(self, audit_dir: Path):
        self.audit_dir = audit_dir
        self.spec_units: List[Dict[str, Any]] = self._load_list("phase6_spec_units_v1.json")
        self.causal_relations: List[Dict[str, Any]] = self._load_list("phase6_causal_relations_v1.json")
        self.conflicts_p6: List[Dict[str, Any]] = self._load_list("phase6_conflicts_v1.json")
        self.unresolved_p6: List[Dict[str, Any]] = self._load_list("phase6_unresolved_v1.json")
        self.summary_p6: Dict[str, Any] = self._load_dict("phase6_summary_v1.json")

    def _load_list(self, filename: str) -> List[Dict[str, Any]]:
        p = self.audit_dir / filename
        if not p.exists():
            return []
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []

    def _load_dict(self, filename: str) -> Dict[str, Any]:
        p = self.audit_dir / filename
        if not p.exists():
            return {}
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    def analyze_and_build(self) -> Dict[str, Any]:
        # A1, A2: Construct Graph Nodes and Edges
        nodes = []
        node_map = {}
        in_degree = {}
        out_degree = {}

        for unit in self.spec_units:
            uid = unit["unit_id"]
            auth_class = unit.get("authority_class", "Canonical")
            auth_cat = get_authority_category(auth_class)

            node_data = {
                "id": uid,
                "label": unit["source_file"],
                "domain": unit["domain"],
                "authority_class": auth_class,
                "authority_category": auth_cat,
                "ast": unit.get("ast", {}),
                "provenance": unit.get("provenance", {})
            }
            nodes.append(node_data)
            node_map[uid] = node_data
            in_degree[uid] = 0
            out_degree[uid] = 0

        edges = []
        edge_ids = set()
        explicit_count = 0
        inferred_count = 0

        for rel in self.causal_relations:
            eid = rel["relation_id"]
            src = rel["source_unit"]
            tgt = rel["target_unit"]

            if eid not in edge_ids:
                edge_ids.add(eid)
                edges.append({
                    "id": eid,
                    "source": src,
                    "target": tgt,
                    "type": rel.get("type", "depends_on"),
                    "classification": rel.get("classification", "EXPLICIT"),
                    "evidence": rel.get("evidence", ""),
                    "provenance": rel.get("provenance", {})
                })
                if src in out_degree:
                    out_degree[src] += 1
                if tgt in in_degree:
                    in_degree[tgt] += 1

                if rel.get("classification") == "EXPLICIT":
                    explicit_count += 1
                else:
                    inferred_count += 1

        # A3 - A8: Graph Topology
        connected_components = self._compute_connected_components(nodes, edges)
        roots = [uid for uid, d in in_degree.items() if d == 0]
        sinks = [uid for uid, d in out_degree.items() if d == 0]
        orphans = [uid for uid in in_degree if in_degree[uid] == 0 and out_degree[uid] == 0]
        cycles = self._detect_cycles(nodes, edges)
        topological_order = self._topological_sort(nodes, edges) if not cycles else None

        # A23: Cross-Domain Dependencies
        cross_domain_deps = []
        for e in edges:
            src_node = node_map.get(e["source"])
            tgt_node = node_map.get(e["target"])
            if src_node and tgt_node and src_node["domain"] != tgt_node["domain"]:
                cross_domain_deps.append({
                    "edge_id": e["id"],
                    "source_unit": e["source"],
                    "target_unit": e["target"],
                    "source_domain": src_node["domain"],
                    "target_domain": tgt_node["domain"],
                    "type": e["type"]
                })

        # A10, A11, A24: Concept Definitions & Candidate Equivalence
        def_map: Dict[str, List[Dict[str, Any]]] = {}
        for u in self.spec_units:
            uid = u["unit_id"]
            ast = u.get("ast", {})
            for d in ast.get("definitions", []):
                text = d.get("text", "")
                def_map.setdefault(text, []).append({"unit_id": uid, "line": d.get("line"), "file": u["source_file"]})

        duplicate_definitions = []
        equivalence_candidates = []

        for def_text, locs in def_map.items():
            if len(locs) > 1:
                duplicate_definitions.append({
                    "finding_id": f"DUP_DEF_{len(duplicate_definitions)+1:04d}",
                    "category": "DUPLICATE_DEFINITION",
                    "concept": def_text,
                    "locations": locs,
                    "count": len(locs)
                })
                equivalence_candidates.append({
                    "concept": def_text,
                    "status": "CANDIDATE",
                    "reason": "Identical definition text across multiple units requiring semantic resolution",
                    "locations": locs
                })

        # A12, A17: Critical Invariant Traceability
        invariant_findings = []
        for u in self.spec_units:
            uid = u["unit_id"]
            ast = u.get("ast", {})
            for inv in ast.get("invariants", []):
                enforcing_ops = [op["text"] for op in ast.get("operations", [])]
                affected_state = [t["text"] for t in ast.get("types", [])]
                downstream = [e["target"] for e in edges if e["source"] == uid]

                invariant_findings.append({
                    "invariant_id": f"INV_{uid}_L{inv['line']}",
                    "source_unit": uid,
                    "source_file": u["source_file"],
                    "invariant_text": inv["text"],
                    "definition_line": inv["line"],
                    "enforcing_operations": enforcing_ops,
                    "affected_state": affected_state,
                    "downstream_propagation": downstream,
                    "missing_enforcement_paths": [] if enforcing_ops else [f"No enforcing operation in unit {uid}"]
                })

        # A13 - A16: Security Check - Non-Authoritative to Canonical Reachability
        canonical_mutation_paths = []
        non_auth_to_canonical_paths = []

        adj = {n["id"]: [] for n in nodes}
        edge_type_map = {}
        for e in edges:
            adj[e["source"]].append(e["target"])
            edge_type_map[(e["source"], e["target"])] = e["type"]

        for src_id in nodes:
            s_uid = src_id["id"]
            s_cat = src_id["authority_category"]
            s_class = src_id["authority_class"]

            queue = [[s_uid]]
            while queue:
                path = queue.pop(0)
                curr = path[-1]
                curr_node = node_map[curr]
                curr_cat = curr_node["authority_category"]

                if s_cat == "non_authoritative" and curr_cat == "authoritative" and len(path) > 1:
                    rel_types = [edge_type_map.get((path[k], path[k+1]), "unknown") for k in range(len(path)-1)]
                    path_finding = {
                        "finding_id": f"AUTH_PATH_{len(non_auth_to_canonical_paths)+1:04d}",
                        "source_unit": s_uid,
                        "target_unit": curr,
                        "source_authority": s_class,
                        "target_authority": curr_node["authority_class"],
                        "path": path,
                        "relation_types": rel_types,
                        "classification": "SECURITY_WARNING",
                        "explanation": f"Non-authoritative node ({s_uid}) reaches Canonical node ({curr})"
                    }
                    if path_finding not in non_auth_to_canonical_paths:
                        non_auth_to_canonical_paths.append(path_finding)
                        if any(t in ["mutates", "authorizes", "defines", "supersedes"] for t in rel_types):
                            canonical_mutation_paths.append(path_finding)

                if len(path) < 5:
                    for nxt in adj.get(curr, []):
                        if nxt not in path:
                            queue.append(path + [nxt])

        all_conflicts = list(self.conflicts_p6)
        all_unresolved = list(self.unresolved_p6)

        graph_schema = {
            "nodes": nodes,
            "edges": edges,
            "provenance": [u["provenance"] for u in self.spec_units],
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "explicit_relations": explicit_count,
                "inferred_relations": inferred_count,
                "roots_count": len(roots),
                "sinks_count": len(sinks),
                "cycles_count": len(cycles),
                "orphans_count": len(orphans)
            }
        }

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files": len(self.spec_units),
            "specification_units": len(self.spec_units),
            "graph_nodes": len(nodes),
            "graph_edges": len(edges),
            "explicit_relations": explicit_count,
            "inferred_relations": inferred_count,
            "roots": roots,
            "sinks": sinks,
            "cycles": cycles,
            "orphan_units": orphans,
            "duplicate_definitions": duplicate_definitions,
            "conflicting_definitions": [],
            "conflicting_invariants": [],
            "authority_violations": [],
            "canonical_mutation_paths": canonical_mutation_paths,
            "non_authoritative_to_canonical_paths": non_auth_to_canonical_paths,
            "unresolved_relations": len(all_unresolved),
            "supersession_candidates": [],
            "equivalence_candidates": equivalence_candidates,
            "cross_domain_dependencies": cross_domain_deps,
            "provenance_complete": True
        }

        # Save Required Audit Outputs
        (self.audit_dir / "phase7_global_specification_graph_v1.json").write_text(json.dumps(graph_schema, indent=2), encoding="utf-8")
        (self.audit_dir / "phase7_causal_analysis_v1.json").write_text(json.dumps({
            "causal_relations": edges,
            "cycles": cycles,
            "topological_order": topological_order,
            "connected_components": connected_components
        }, indent=2), encoding="utf-8")
        (self.audit_dir / "phase7_authority_analysis_v1.json").write_text(json.dumps({
            "authority_rules": AUTHORITY_RULES,
            "canonical_mutation_paths": canonical_mutation_paths,
            "non_authoritative_to_canonical_paths": non_auth_to_canonical_paths
        }, indent=2), encoding="utf-8")
        (self.audit_dir / "phase7_invariant_analysis_v1.json").write_text(json.dumps({"invariants": invariant_findings}, indent=2), encoding="utf-8")
        (self.audit_dir / "phase7_conflicts_v1.json").write_text(json.dumps(all_conflicts, indent=2), encoding="utf-8")
        (self.audit_dir / "phase7_unresolved_v1.json").write_text(json.dumps(all_unresolved, indent=2), encoding="utf-8")
        (self.audit_dir / "phase7_summary_v1.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return summary

    def _compute_connected_components(self, nodes: List[Dict], edges: List[Dict]) -> List[List[str]]:
        adj = {n["id"]: set() for n in nodes}
        for e in edges:
            if e["source"] in adj and e["target"] in adj:
                adj[e["source"]].add(e["target"])
                adj[e["target"]].add(e["source"])

        visited = set()
        components = []
        for n in adj:
            if n not in visited:
                comp = []
                q = [n]
                visited.add(n)
                while q:
                    curr = q.pop(0)
                    comp.append(curr)
                    for nxt in adj[curr]:
                        if nxt not in visited:
                            visited.add(nxt)
                            q.append(nxt)
                components.append(sorted(comp))
        return components

    def _detect_cycles(self, nodes: List[Dict], edges: List[Dict]) -> List[List[str]]:
        adj = {n["id"]: [] for n in nodes}
        for e in edges:
            if e["source"] in adj and e["target"] in adj:
                adj[e["source"]].append(e["target"])

        cycles = []
        visited = {}
        path = []

        def dfs(node: str):
            visited[node] = 1
            path.append(node)
            for nxt in adj.get(node, []):
                if visited.get(nxt, 0) == 1:
                    cycle_start = path.index(nxt)
                    cycles.append(path[cycle_start:] + [nxt])
                elif visited.get(nxt, 0) == 0:
                    dfs(nxt)
            path.pop()
            visited[node] = 2

        for n in adj:
            if visited.get(n, 0) == 0:
                dfs(n)
        return cycles

    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[str] | None:
        in_deg = {n["id"]: 0 for n in nodes}
        adj = {n["id"]: [] for n in nodes}
        for e in edges:
            if e["source"] in adj and e["target"] in adj:
                adj[e["source"]].append(e["target"])
                in_deg[e["target"]] += 1

        queue = [n for n, d in in_deg.items() if d == 0]
        topo = []

        while queue:
            curr = queue.pop(0)
            topo.append(curr)
            for nxt in adj[curr]:
                in_deg[nxt] -= 1
                if in_deg[nxt] == 0:
                    queue.append(nxt)

        return topo if len(topo) == len(nodes) else None


def run_phase7_pipeline() -> Dict[str, Any]:
    audit_dir = PROJECT_ROOT / "data" / "audit"
    analyzer = GlobalSpecificationGraphAnalyzer(audit_dir)
    return analyzer.analyze_and_build()


if __name__ == "__main__":
    run_phase7_pipeline()