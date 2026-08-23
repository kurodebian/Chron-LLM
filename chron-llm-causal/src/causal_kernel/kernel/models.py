"""
src/causal_kernel/kernel/models.py
----------------------------------
正規化マスターグラフ v2.0 データ構造モデル定義（柔軟対応版）
"""

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field, model_validator


class NodeCategory(str, Enum):
    INVARIANT = "Invariant"
    OPERATION = "Operation"
    STORAGE = "Storage"
    STATE = "State"
    EVENT = "Event"


class CausalRelationType(str, Enum):
    CONSTRAINS = "constrains"
    TRANSFORMS = "transforms"
    DEPENDS_ON = "depends_on"
    PRODUCES = "produces"
    CONFLICTS_WITH = "conflicts_with"


class CausalNode(BaseModel):
    id: str = Field(..., description="Node Unique ID")
    label: str = Field(..., description="人間が読めるラベル")
    category: str = Field(default="State", description="ノードカテゴリ")
    description: str = Field("", description="詳細仕様")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def flex_parse_node(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # label 補完: label -> name -> id
            if "label" not in data or not data["label"]:
                data["label"] = data.get("name") or data.get("id") or "unnamed_node"
            # category 補完: category -> type -> "State"
            if "category" not in data or not data["category"]:
                data["category"] = data.get("type") or "State"
        return data


class CausalEdge(BaseModel):
    id: str = Field(..., description="Edge ID")
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    relation: str = Field(default="depends_on", description="因果関係種別")
    evidence: str = Field("", description="根拠テキスト")
    source_proposals: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    class Config:
        populate_by_name = True

    @model_validator(mode="before")
    @classmethod
    def flex_parse_edge(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # id 自動生成 (存在しない場合)
            if "id" not in data or not data["id"]:
                src = data.get("from", "src")
                dst = data.get("to", "dst")
                data["id"] = f"E_{src}_{dst}"
            # relation 補完: relation -> type -> "depends_on"
            if "relation" not in data or not data["relation"]:
                data["relation"] = data.get("type") or data.get("relation_type") or "depends_on"
        return data


class MasterGraphContainer(BaseModel):
    nodes: Dict[str, CausalNode]
    edges: List[CausalEdge]
    version: str = "2.0"

    @model_validator(mode="before")
    @classmethod
    def normalize_nodes(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_nodes = data.get("nodes")
            # JSON側がリスト形式 (List) の場合、ノードの "id" をキーにした辞書 (Dict) に変換する
            if isinstance(raw_nodes, list):
                nodes_dict = {}
                for idx, n in enumerate(raw_nodes):
                    if isinstance(n, dict):
                        node_id = n.get("id") or f"N{idx+1:03d}"
                        nodes_dict[node_id] = n
                    else:
                        nodes_dict[f"N{idx+1:03d}"] = n
                data["nodes"] = nodes_dict
        return data