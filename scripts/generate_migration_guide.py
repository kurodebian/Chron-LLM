# scripts/generate_migration_guide.py
import os

def generate_guide():
    docs_dir = "docs"
    os.makedirs(docs_dir, exist_ok=True)
    file_path = os.path.join(docs_dir, "migration-v0.1-to-v0.2.md")
    
    content = """# Migration Guide: v0.1 to v0.2 Specification

This guide outlines the migration path from deprecated v0.1 specifications (`basin.spec`, `chron-llm-r1-dynamical-analysis-experiment-spec-v0.1.spec`) to the Single Source of Truth (SOT) `chron-llm-spec-v0.2.spec`.

## 1. Overview of Deprecations
- **`basin.spec`**: Legacy basin/attractor traversal logic. Universal invariants (`INV-PARTITION`, `INV-MASS`, `INV-RATIO`) and `build-basin-structure` have been absorbed into `chron-llm-spec-v0.2.spec`.
- **`chron-llm-r1-dynamical-analysis-experiment-spec-v0.1.spec`**: Preliminary dynamical analysis contract. Deterministic mapping and SCC-based cycle detection have evolved into stochastic trajectory modeling.

## 2. Function & Operation Mapping Table

| v0.1 Function / Concept | v0.2 SOT Equivalent / Destination | Migration Notes |
|-------------------------|----------------------------------|-----------------|
| `build-basin-map` | `chron-llm-spec-v0.2.spec` (Basin integration) | Absorbed into SOT Basin type constraints and global normalization rules. |
| `find-cycle` | `chron-llm-spec-v0.2.spec` (`CycleResult` / SCC modules) | Migrated to stochastic trajectory modeling and stability metric evaluation. |
| `rollout*` | `chron-llm-spec-v0.2.spec` (`Trajectory`, `EventSelection`) | Upgraded from deterministic maps to stochastic trajectory modeling. |
| `build-basin-structure` | `chron-llm-spec-v0.2.spec` (Basin invariants) | Universal invariants merged into SOT. Note: `INV Basin.ratio == Basin.mass / len(Graph.nodes)`. |

## 3. Breaking Changes & Normalization Rules
- **Basin Ratio Normalization**: 
  - v0.1: Used local `len(nodes)` calculation.
  - v0.2: Enforces global normalization: `INV Basin.ratio == Basin.mass / len(Graph.nodes)`. Update any instance-level calculations accordingly.
- **Field Mappings**:
  - `strength` → `str`
  - `relation` → `rel`
  - `Symbol` → `ID`
  - Node references in edges/basins must use ID-based referencing (`ID`) instead of direct struct references.
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Generated migration guide: {file_path}")

if __name__ == "__main__":
    generate_guide()