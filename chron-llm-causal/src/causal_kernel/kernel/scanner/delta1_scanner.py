import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Set, Dict, Tuple

@dataclass
class Delta1GroundTruth:
    """
    Independent Ground Truth generated from Delta-1 normalized data.
    Does NOT depend on Traceability claims.
    """
    raw_node_occurrences: int = 0
    unique_node_ids: Set[str] = field(default_factory=set)
    duplicate_node_ids: List[str] = field(default_factory=list)
    
    raw_edge_occurrences: int = 0
    unique_edge_keys: Set[Tuple[str, str, str]] = field(default_factory=set) # (src, dst, type)
    duplicate_edge_keys: List[Tuple[str, str, str]] = field(default_factory=list)
    
    parse_errors: List[Dict] = field(default_factory=list)
    files_scanned: List[str] = field(default_factory=list)
    
    @property
    def unique_node_count(self) -> int:
        return len(self.unique_node_ids)
    
    @property
    def unique_edge_count(self) -> int:
        return len(self.unique_edge_keys)

class IndependentDelta1Scanner:
    """
    Scans Delta-1 normalized JSON files to generate Ground Truth.
    STRICT RULE: Must not read any Traceability or Audit artifacts.
    """
    
    def __init__(self, delta1_normalized_dir: str):
        self.delta1_normalized_dir = delta1_normalized_dir
        
    def scan(self) -> Delta1GroundTruth:
        gt = Delta1GroundTruth()
        
        if not os.path.exists(self.delta1_normalized_dir):
            gt.parse_errors.append({
                "type": "DIRECTORY_NOT_FOUND",
                "path": self.delta1_normalized_dir
            })
            return gt

        # Identify JSON files in the normalized directory
        json_files = []
        for root, dirs, files in os.walk(self.delta1_normalized_dir):
            for file in files:
                if file.endswith(".json"):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            gt.parse_errors.append({
                "type": "NO_FILES_FOUND",
                "path": self.delta1_normalized_dir
            })
            return gt

        # Use defaultdict for efficient counting
        seen_node_ids = defaultdict(int)
        seen_edge_keys = defaultdict(int)

        for file_path in json_files:
            relative_path = os.path.relpath(file_path, self.delta1_normalized_dir)
            gt.files_scanned.append(relative_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._process_single_file(data, file_path, gt, seen_node_ids, seen_edge_keys)
                
            except json.JSONDecodeError as e:
                gt.parse_errors.append({
                    "type": "JSON_DECODE_ERROR",
                    "file": relative_path,
                    "error": str(e)
                })
            except Exception as e:
                gt.parse_errors.append({
                    "type": "PROCESSING_ERROR",
                    "file": relative_path,
                    "error": str(e)
                })
        
        # Calculate duplicates based on global seen sets
        gt.duplicate_node_ids = list(k for k, v in seen_node_ids.items() if v > 1)
        gt.duplicate_edge_keys = list(k for k, v in seen_edge_keys.items() if v > 1)
        
        return gt

    def _process_single_file(self, data: dict, file_path: str, gt: Delta1GroundTruth, 
                             seen_node_ids: Dict[str, int], seen_edge_keys: Dict[Tuple, int]):
        """
        Processes a single normalized JSON file.
        """
        if not isinstance(data, dict):
            return

        # --- Nodes ---
        # "nodes" キーだけでなく "proposals" 等の配下にあるノード要素もスキャン対象とする
        node_container_keys = ["nodes", "proposals"]
        for key in node_container_keys:
            nodes = data.get(key, [])
            if not isinstance(nodes, list):
                continue

            for node in nodes:
                if not isinstance(node, dict):
                    continue

                gt.raw_node_occurrences += 1
                node_id = node.get("id") or node.get("node_id")
                
                if node_id is None:
                    gt.parse_errors.append({
                        "type": "MISSING_NODE_ID",
                        "file": file_path,
                        "node_data": str(node)[:100]
                    })
                    continue
                
                node_id_str = str(node_id)
                gt.unique_node_ids.add(node_id_str)
                seen_node_ids[node_id_str] += 1

        # --- Edges ---
        edges = data.get("edges", [])
        if isinstance(edges, list):
            for edge in edges:
                if not isinstance(edge, dict):
                    continue

                gt.raw_edge_occurrences += 1
                src = edge.get("source") or edge.get("from")
                dst = edge.get("target") or edge.get("to")
                etype = edge.get("type") or edge.get("relation") or "UNDEFINED"
                
                if src is None or dst is None:
                    gt.parse_errors.append({
                        "type": "MALFORMED_EDGE",
                        "file": file_path,
                        "edge_data": str(edge)[:100]
                    })
                    continue
                
                edge_key = (str(src), str(dst), str(etype))
                gt.unique_edge_keys.add(edge_key)
                seen_edge_keys[edge_key] += 1