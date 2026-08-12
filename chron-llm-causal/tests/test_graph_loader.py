"""
tests/test_graph_loader.py
--------------------------
GraphLoader および Validator の単体テスト
"""

from pathlib import Path
import pytest
from causal_kernel.kernel.graph_loader import CausalGraphLoader


def test_graph_loader_and_validator():
    graph_path = Path("data/graphs/causal_master_graph_v2.json")
    if not graph_path.exists():
        pytest.skip("causal_master_graph_v2.json が存在しないためスキップします")

    loader = CausalGraphLoader(graph_path)
    graph = loader.load()

    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0

    report = loader.validate()
    assert "is_valid" in report
    assert "violations" in report