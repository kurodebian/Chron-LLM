# scripts/refactor_cluster_schema.py
import os
import re

def refactor_spec():
    target_file = "experiments/ir/3cluster.spec"
    if not os.path.exists(target_file):
        print(f"❌ Target {target_file} not found.")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. ローカル型定義（structやtypeによる Node, Edge, Basin, Graph などの定義ブロック）をコメントアウトまたは除去
    # ※手動で完全に削除しても良いが、安全に正規表現で型定義ブロックを置換・無効化する
    # ここでは分かりやすく、SOT参照への移行を前提とした正規化を行う

    # 2. フィールド名・型名の正規化置換
    content = re.sub(r'\bstrength\b', 'str', content)
    content = re.sub(r'\brelation\b', 'rel', content)
    content = re.sub(r'\bSymbol\b', 'ID', content)
    
    # 3. SOTインポート宣言の追加（ファイルの先頭に挿入）
    import_header = 'import "chron-llm-spec-v0.2.spec" as SOT;\n\n'
    if import_header.strip() not in content:
        content = import_header + content

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"✅ Successfully refactored schema in {target_file}")

if __name__ == "__main__":
    refactor_spec()