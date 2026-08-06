# scripts/ci_spec_lint.py
import os
import re
import sys

def lint_specs():
    errors = 0
    forbidden_imports = ["basin.spec", "chron-llm-r1-dynamical-analysis-experiment-spec-v0.1.spec"]
    
    # 1. 3cluster.spec でのローカル型再定義の禁止チェック
    target_fixture = "experiments/ir/3cluster.spec"
    if os.path.exists(target_fixture):
        with open(target_fixture, "r", encoding="utf-8") as f:
            content = f.read()
            # Role =, Node =, type Node, struct Edge などの定義が残っていないか検知
            if re.search(r'^(Role|Relation|Node|Edge|Graph|Basin)\s*(=|\bstruct\b|\btype\b)', content, re.MULTILINE):
                print(f"❌ [LINT ERROR] {target_fixture} contains forbidden local type re-definitions!")
                errors += 1

    # 2. 非推奨ファイルのインポート禁止チェック（archive は走査対象外）
    for root, dirs, files in os.walk("."):
        if "archive" in root.split(os.sep):
            continue
            
        for file in files:
            if file.endswith(".spec"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    for fb in forbidden_imports:
                        # import "basin.spec" のような実際のインポート宣言のみを厳密に検知（コメントは無視）
                        pattern = r'import\s+["\'].*?' + re.escape(fb) + r'["\']'
                        if re.search(pattern, text):
                            print(f"❌ [LINT ERROR] File {path} imports deprecated spec: {fb}")
                            errors += 1

    if errors > 0:
        print(f"\n❌ Spec Lint Failed with {errors} error(s).")
        sys.exit(1)
    else:
        print("✅ All spec lint checks passed successfully! No legacy dependencies or type re-definitions found.")

if __name__ == "__main__":
    lint_specs()