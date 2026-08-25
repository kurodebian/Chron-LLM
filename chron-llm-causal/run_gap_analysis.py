# run_gap_analysis.py
from pathlib import Path
from src.causal_kernel.kernel.validator.schema_validator import SchemaValidator

def main():
    validator = SchemaValidator(schema_dir="schemas")

    # 全4契約を網羅する全実データターゲット (計8ファイル)
    target_files = [
        # Delta1Extraction
        ("data/delta1_normalized/causal_extract_core_v1.json", "delta1_extraction"),
        ("data/delta1_normalized/causal_extract_core_v2.json", "delta1_extraction"),
        # Delta1Graph (中間グラフ構造 3ファイル)
        ("data/audit/phase6_dependency_graph_v1.json", "delta1_graph"),
        ("data/audit/phase7_global_causal_graph_v1.json", "delta1_graph"),
        ("data/audit/phase7_global_specification_graph_v1.json", "delta1_graph"),
        # Delta2MasterGraph (Canonical 統合グラフ)
        ("data/graphs/causal_master_graph_v2.json", "delta2_mastergraph"),
        # Traceability (監査契約 2ファイル)
        ("delta1_delta2_traceability.json", "traceability"),
        ("data/audit/delta1_delta2_traceability_v1.json", "traceability"),
    ]

    print("=== Real Data Schema Gap Analysis (All 4 Contracts) ===\n")
    
    total_valid = 0
    for filepath_str, schema_type in target_files:
        filepath = Path(filepath_str)

        if not filepath.exists():
            print(f"[SKIP] {filepath_str} (File not found)")
            continue

        is_valid, errors = validator.validate_file(str(filepath), schema_type)

        if is_valid:
            print(f"[\033[32mVALID\033[0m] {filepath_str} -> Schema: {schema_type}")
            total_valid += 1
        else:
            print(f"[\033[31mINVALID\033[0m] {filepath_str} -> Schema: {schema_type}")
            for err in errors[:5]:
                print(f"  └─ Path: {err['path']} | Error: {err['message']}")
            print()

    print(f"\nResult: {total_valid}/{len(target_files)} passed.")

if __name__ == "__main__":
    main()