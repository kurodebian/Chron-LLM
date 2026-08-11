# scripts/integrate_contracts.py
import os


def integrate_sot_contracts():
    sot_file = "experiments/ir/chron-llm-spec-v0.2.spec"
    if not os.path.exists(sot_file):
        print(f"⚠️ {sot_file} not found. Creating placeholder or check path.")
        return

    with open(sot_file, "r", encoding="utf-8") as f:
        content = f.read()

    contract_block = """

// ===================================================================
// Universal Invariants & Global Contracts (Merged from basin.spec)
// ===================================================================

INV-PARTITION: forall n in Graph.nodes, exists unique b in Basin, n in b.nodes
INV-MASS: forall b in Basin, b.mass == len(b.nodes)
INV-RATIO: forall b in Basin, b.ratio == b.mass / len(Graph.nodes)
"""

    if "INV-PARTITION" not in content:
        content += contract_block
        with open(sot_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Successfully integrated universal contracts into {sot_file}")
    else:
        print(f"ℹ️ Universal contracts already present in {sot_file}")


if __name__ == "__main__":
    integrate_sot_contracts()
