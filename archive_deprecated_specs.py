#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

# 廃止・非推奨対象のファイルと統合先マッピング
DEPRECATED_FILES = {
    "graph-runtime/ir/prefill.spec": "graph-runtime/ir/chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec",
    "graph-runtime/ir/projection.spec": "graph-runtime/ir/chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec",
    "registry/ir/registry.spec": "docs/spec/ir/R2.0-B_C_World_Runtime_Observation_Contract_v1.0.spec",
    "world/ir/world.spec": "docs/spec/ir/R2.0-B_C_World_Runtime_Observation_Contract_v1.0.spec",
}

ARCHIVE_DIR = Path("archive/deprecated")

def archive_specs():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    for file_str, target in DEPRECATED_FILES.items():
        src_path = Path(file_str)
        if not src_path.exists():
            print(f"⚠️ スキップ (存在しません): {src_path}")
            continue

        dest_path = ARCHIVE_DIR / src_path.name
        
        # デプロケーション・ヘッダーの挿入
        content = src_path.read_text(encoding="utf-8")
        header = (
            f"// ============================================================================\n"
            f"// [DEPRECATED / SUPERSEDED]\n"
            f"// This file is no longer active. Logic has been migrated to:\n"
            f"//   {target}\n"
            f"// ============================================================================\n\n"
        )
        
        dest_path.write_text(header + content, encoding="utf-8")
        src_path.unlink() # 元ファイルを削除
        print(f"✅ アーカイブ完了: {src_path} -> {dest_path}")

if __name__ == "__main__":
    archive_specs()
