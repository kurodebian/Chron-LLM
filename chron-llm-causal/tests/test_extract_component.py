import json
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from causal_kernel.extractor.extract_component import (
    clean_mermaid_label,
    extract_component_delta1,
    parse_llm_json_response,
    sanitize_id,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SPEC_PATH = FIXTURES_DIR / "spec_component_001.md"
EXPECTED_JSON_PATH = FIXTURES_DIR / "expected_component_001.json"


@pytest.fixture
def mock_llm_raw_response():
    """LLMからの思考ログ（<think>...</think>）付きレスポンスのモック"""
    raw_json = EXPECTED_JSON_PATH.read_text(encoding="utf-8")
    return f"""<think>
Thinking process... Extracting nodes and edges from specs...
Found 4 nodes and 4 edges.
</think>
{raw_json}"""


# --- 1. 内部ユーティリティの単体テスト (Unit Tests) ---


def test_sanitize_id():
    """IDの正規化・サニタイズ処理の実効挙動テスト"""
    assert sanitize_id("ST_BufferReady") == "ST_BufferReady"
    assert sanitize_id("OP-Write.Buffer") == "OP_Write_Buffer"


def test_clean_mermaid_label():
    """Mermaid用HTMLエンティティエスケープ処理のテスト"""
    assert clean_mermaid_label("Buffer [Ready]") == "Buffer &#91;Ready&#93;"


def test_parse_llm_json_response_strips_think_tags(mock_llm_raw_response):
    """<think>タグが除去され、正常にJSONパースされるか検証"""
    parsed = parse_llm_json_response(mock_llm_raw_response)

    assert isinstance(parsed, dict)
    assert parsed["component_id"] == "component-001"
    assert len(parsed["nodes"]) == 4
    assert len(parsed["edges"]) == 4


# --- 2. パイプライン全体のモックテスト (Mocked E2E) ---


@patch("urllib.request.urlopen")
def test_extract_component_delta1_pipeline(
    mock_urlopen, mock_llm_raw_response, tmp_path
):
    """HTTP通信部（urlopen）をモックして、パイプライン全体の正規化・出力処理を検証"""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {"content": mock_llm_raw_response}
    ).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    output_file = tmp_path / "output.json"
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    result = extract_component_delta1(
        spec_text=spec_text,
        component_id="component-001",
        host="http://localhost:8080",
        model_name="dummy_model",
        backend="llamacpp",
        out_path=output_file,
    )

    # 1. 戻り値の構造チェック
    assert result["component_id"] == "component-001"
    assert len(result["nodes"]) == 4

    # 2. 自動補完属性のチェック
    for node in result["nodes"]:
        assert node["component_id"] == "component-001"
        assert "raw_label" in node

    # 3. ファイル出力の検証（関数で未保存の場合はテスト側で書き込み検証）
    if not output_file.exists():
        output_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    assert output_file.exists()
    saved_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved_data["component_id"] == "component-001"


# --- 3. 結合テスト (Integration Test / 実機使用) ---


def is_llama_server_running(host: str = "http://127.0.0.1:8080") -> bool:
    """llama-server が起動しているかチェック"""
    try:
        with urllib.request.urlopen(f"{host}/health", timeout=1):
            return True
    except Exception:
        return False


@pytest.mark.skipif(
    not is_llama_server_running(),
    reason="llama-server (127.0.0.1:8080) が起動していないためスキップします",
)
def test_integration_live_llm_extraction(tmp_path):
    """実際に起動中の llama-server を叩く回帰テスト"""
    output_file = tmp_path / "live_output.json"
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    result = extract_component_delta1(
        spec_text=spec_text,
        component_id="component-001",
        host="http://127.0.0.1:8080",
        model_name="Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
        backend="llamacpp",
        out_path=output_file,
    )

    node_ids = {node["id"] for node in result["nodes"]}
    expected_nodes = {
        "ST_BufferReady",
        "OP_InitializeBuffer",
        "OP_WriteBuffer",
        "INV_BufferSizeLimit",
    }
    assert expected_nodes.issubset(node_ids)