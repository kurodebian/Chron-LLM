# scripts/fix_delta1_edge_ids.py

import hashlib
import json
from pathlib import Path

DATA_DIR = Path("data/delta1_normalized")
CANONICAL_SEP = "\x1f"

def compute_canonical_edge_id(
    component_id: str,
    from_id: str,
    to_id: str,
    relation: str,
) -> str:
    """
    Canonical Edge ID:

        E_{component_id}_{SHA256[:8]}

    Hash material:

        component_id
        US (0x1f)
        from_id
        US (0x1f)
        to_id
        US (0x1f)
        relation
    """
    material = (
        f"{component_id}"
        f"{CANONICAL_SEP}"
        f"{from_id}"
        f"{CANONICAL_SEP}"
        f"{to_id}"
        f"{CANONICAL_SEP}"
        f"{relation}"
    )

    digest = hashlib.sha256(
        material.encode("utf-8")
    ).hexdigest()[:8]

    return f"E_{component_id}_{digest}"

def main():
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Delta-1 normalized directory not found: {DATA_DIR}"
        )

    updated_files = 0
    updated_edges = 0
    total_edges = 0

    all_edge_ids = []

    for path in sorted(DATA_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        component_id = data.get("component_id", path.stem)
        edges = data.get("edges", [])

        modified = False

        for edge in edges:
            total_edges += 1

            from_id = edge.get("from", "")
            to_id = edge.get("to", "")
            relation = edge.get("relation", "")

            canonical_id = compute_canonical_edge_id(
                component_id,
                from_id,
                to_id,
                relation,
            )

            if edge.get("id") != canonical_id:
                edge["id"] = canonical_id
                modified = True
                updated_edges += 1

            all_edge_ids.append(canonical_id)

        if modified:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            updated_files += 1

    # --------------------------------------------------
    # Contract validation
    # --------------------------------------------------

    unique_edge_ids = set(all_edge_ids)

    if len(unique_edge_ids) != total_edges:
        duplicates = sorted(
            edge_id
            for edge_id in unique_edge_ids
            if all_edge_ids.count(edge_id) > 1
        )

        raise AssertionError(
            "Canonical Edge ID uniqueness violation: "
            f"{len(unique_edge_ids)} unique IDs / "
            f"{total_edges} edges. "
            f"Duplicates: {duplicates}"
        )

    expected_total = 312

    if total_edges != expected_total:
        raise AssertionError(
            f"Delta-1 Edge population mismatch: "
            f"{total_edges} != expected {expected_total}"
        )

    # --------------------------------------------------
    # Result
    # --------------------------------------------------

    print(
        f"Normalized {updated_edges} edges "
        f"across {updated_files} files."
    )

    print(
        f"Canonical Edge Count: {total_edges}"
    )

    print(
        f"Unique Canonical Edge IDs: {len(unique_edge_ids)}"
    )

    print(
        "CHECK PASSED: "
        "312/312 edges have unique canonical IDs."
    )

if __name__ == "__main__":
    main()