# scripts/archive_specs.py
import os

def archive_legacy_specs():
    # アーカイブ先の定義
    archive_dir = "specs/archive/v0.1"
    os.makedirs(archive_dir, exist_ok=True)
    
    # 実環境のパス（experiments/ir/ 配下）に合わせる
    legacy_files = [
        "experiments/ir/basin.spec",
        "experiments/ir/chron-llm-r1-dynamical-analysis-experiment-spec-v0.1.spec"
    ]
    
    for src_path in legacy_files:
        if os.path.exists(src_path):
            with open(src_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 非推奨アノテーションの付与
            annotated_content = f"// @deprecated - Superceded by chron-llm-spec-v0.2.spec\n\n" + content
            
            # ファイル名のみを抽出してアーカイブ先パスを構築
            file_name = os.path.basename(src_path)
            dest_path = os.path.join(archive_dir, file_name)
            
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(annotated_content)
                
            os.remove(src_path)
            print(f"✅ Archived and annotated: {src_path} -> {dest_path}")
        else:
            print(f"⚠️ Warning: {src_path} not found, skipping.")

if __name__ == "__main__":
    archive_legacy_specs()