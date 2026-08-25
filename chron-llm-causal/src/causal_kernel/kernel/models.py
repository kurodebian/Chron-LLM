"""
src/causal_kernel/kernel/models.py
----------------------------------
因果カーネル Python内部表現モデル定義 (Pydantic V2 対応)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Delta1GraphNode(BaseModel):
    id: str
    label: str
    category: Optional[str] = None
    description: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None


class Delta1GraphEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_: str = Field(..., alias="from")
    to: str
    relation: Optional[str] = None
    evidence: Optional[str] = None
    confidence: Optional[float] = None


class Delta1Graph(BaseModel):
    schema_version: Optional[str] = None
    source_extraction_id: Optional[str] = None
    nodes: List[Delta1GraphNode]
    edges: List[Delta1GraphEdge]


class Delta2MasterGraphNode(BaseModel):
    id: str
    global_id: str
    local_id: str
    type: str
    name: str
    description: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class Delta2MasterGraphEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_: str = Field(..., alias="from")
    to: str
    pipeline: str
    morphism_type: str
    guard_invariant: List[str] = Field(default_factory=list)
    delta_level: str


class Delta2MasterGraph(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nodes: List[Delta2MasterGraphNode]
    edges: List[Delta2MasterGraphEdge]