# run_gap_analysis.py
import sys
from pathlib import Path
from src.causal_kernel.kernel.validator.schema_validator import SchemaValidator

def main():
    validator = SchemaValidator(schema_dir="schemas")

    # 実ファイルの正確なパスと対応するスキーマ定義
    target_files = [
        ("data/delta1_normalized/causal_extract_core_v1.json", "delta1_extraction"),
        ("data/delta1_normalized/causal_extract_core_v2.json", "delta1_extraction"),
        ("data/graphs/causal_master_graph_v2.json", "delta2_mastergraph"),
        ("delta1_delta2_traceability.json", "traceability"),
        ("data/audit/delta1_delta2_traceability_v1.json", "traceability"),
    ]

    print("=== Real Data Schema Gap Analysis ===\n")
    
    for filepath_str, schema_type in target_files:
        filepath = Path(filepath_str)

        if not filepath.exists():
            print(f"[SKIP] {filepath_str} (File not found)")
            continue

        is_valid, errors = validator.validate_file(str(filepath), schema_type)

        if is_valid:
            print(f"[\033[32mVALID\033[0m] {filepath_str} -> Schema: {schema_type}")
        else:
            print(f"[\033[31mINVALID\033[0m] {filepath_str} -> Schema: {schema_type}")
            print(f"  Total Errors: {len(errors)}")
            for err in errors[:10]:
                print(f"  └─ Path: {err['path']}")
                print(f"     Error: {err['message']}")
            if len(errors) > 10:
                print(f"  └─ ... and {len(errors) - 10} more errors.")
            print()

if __name__ == "__main__":
    main()