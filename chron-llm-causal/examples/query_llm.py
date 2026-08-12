import os
from causal_kernel.extractor.cae_extractor import generate_causal_mermaid


def main():
    # バックエンドの判定 (llamacpp / ollama)
    backend = os.environ.get("LLM_BACKEND", "llamacpp").lower()

    # バックエンドに応じた Host / Model の決定
    if backend == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b")
    else:  # default: llamacpp
        host = os.environ.get("LLAMA_HOST", "http://127.0.0.1:8080")
        model = os.environ.get("LLAMA_MODEL", "qwen2.5-32b")

    sample_context = """
    OP Commit PRE は c.parent-id に依存する。
    OP Commit が実行されると Canonical' 状態が更新され、INV Mutate(Canonical) が満たされる。
    OPS: commit は WAL.store に依存し、WAL への正常記録が行われることで INV: 8. DETERMINISM が保証される。
    """

    print(f"=== LLM ({backend}) から因果 JSON 抽出 & Mermaid 生成中 ===")
    print(f"  Host   : {host}")
    print(f"  Model  : {model}")
    print("--------------------------------------------------")

    mermaid_code = generate_causal_mermaid(
        sample_context, host=host, model=model, backend=backend
    )

    print("\n--- 生成された Mermaid コード ---")
    print(mermaid_code)

    # .mmd ファイルとして保存
    output_path = "output_causal_graph.mmd"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    print(f"\n[{output_path}] に保存完了しました。")


if __name__ == "__main__":
    main()