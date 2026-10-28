#!/usr/bin/env python3
# tools/mdsheets_dm2_client.py
"""
OpenAI-compatible chat client for the p2-dm2 md_sheets extraction run.

Contract slice implemented here:
    (client (api openai) (temp 0) (seed 0) (grammar auto))

Design rules:
  - stdlib only (urllib); no third-party dependency.
  - The client records the EXACT request payload and the EXACT raw
    response content so the runner can persist both as provenance
    ("prov request raw").
  - No output repair of any kind: content is returned verbatim.
  - "grammar auto": grammar constraints are applied only when the
    backend advertises support (probed once via /props) AND a grammar
    file exists; otherwise the request is sent without grammar and the
    decision is recorded per call. No silent behavior.
  - No secrets are ever placed in the payload or logs. If an
    api_key is configured it is sent only as the Authorization header
    and is never written to any artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"
DEFAULT_TIMEOUT = 180.0
DEFAULT_MAX_TOKENS = 2048


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OpenAIChatConfig:
    base_url: str = DEFAULT_BASE_URL
    model: str | None = None  # None -> resolve from /v1/models
    temperature: float = 0.0
    seed: int = 0
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout: float = DEFAULT_TIMEOUT
    api_key: str | None = None  # only from env; never persisted
    grammar_path: str | None = None  # "grammar auto" candidate file

    @staticmethod
    def from_env(**overrides: Any) -> "OpenAIChatConfig":
        values: dict[str, Any] = {
            "base_url": os.environ.get(
                "MDSHEETS_DM2_BASE_URL", DEFAULT_BASE_URL
            ),
            "model": os.environ.get("MDSHEETS_DM2_MODEL") or None,
            "api_key": os.environ.get("MDSHEETS_DM2_API_KEY") or None,
            "grammar_path": os.environ.get("MDSHEETS_DM2_GRAMMAR") or None,
        }
        _timeout = os.environ.get("MDSHEETS_DM2_TIMEOUT")
        if _timeout and _timeout.strip():
            # transport-only knob (read timeout); validation authority
            # untouched. Large units at measured ~110 tok/s decode can
            # exceed the 180s default inside one completion.
            values["timeout"] = float(_timeout)
        values.update({k: v for k, v in overrides.items() if v is not None})
        return OpenAIChatConfig(**values)


@dataclass(frozen=True)
class ChatObservation:
    raw_output: str
    request_payload: dict[str, Any]
    metadata: dict[str, Any]
    # convenience accessors used by the runner
    @property
    def prompt_sha256(self) -> str:
        return self.metadata["prompt_sha256"]

    @property
    def raw_output_sha256(self) -> str:
        return self.metadata["raw_output_sha256"]


class OpenAIBackendError(RuntimeError):
    pass


def _http_json(
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    api_key: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:2000]
        except Exception:
            pass
        raise OpenAIBackendError(
            f"HTTP {exc.code} from {url}: {detail}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OpenAIBackendError(f"backend unreachable at {url}: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise OpenAIBackendError(
            f"non-JSON response from {url}: {body[:200]!r}"
        ) from exc


def resolve_model(config: OpenAIChatConfig) -> tuple[str, dict[str, Any]]:
    """Resolve model id and probe grammar capability (grammar auto)."""
    models_doc = _http_json(
        f"{config.base_url}/models",
        api_key=config.api_key,
        timeout=config.timeout,
    )
    model_ids = [
        entry.get("id")
        for entry in models_doc.get("data", [])
        if isinstance(entry, dict) and entry.get("id")
    ]
    if not model_ids:
        raise OpenAIBackendError(
            f"no models advertised at {config.base_url}/models"
        )
    model: str = config.model or str(model_ids[0])
    probe: dict[str, Any] = {
        "advertised_models": model_ids,
        "resolved_model": model,
        "props_probe": None,
        "grammar_advertised": False,
    }
    try:
        # llama.cpp-style servers expose /props at the server root, not
        # under the /v1 OpenAI-compat prefix; derive the root from base_url.
        server_root = re.sub(r"/v\d+/?$", "", config.base_url) or config.base_url
        props = _http_json(
            f"{server_root}/props",
            api_key=config.api_key,
            timeout=config.timeout,
        )
        probe["props_probe"] = props
        blob = json.dumps(props)
        if "grammar" in blob.lower():
            probe["grammar_advertised"] = True
    except OpenAIBackendError as exc:
        probe["props_probe"] = {"error": str(exc)}
    return model, probe


def call_openai_chat(
    prompt: str,
    config: OpenAIChatConfig,
    *,
    model: str | None = None,
    grammar_probe: dict[str, Any] | None = None,
    max_tokens: int | None = None,
) -> ChatObservation:
    """
    One OpenAI-compatible chat completion call.

    Returns raw assistant content verbatim plus the exact request
    payload for provenance. Raises OpenAIBackendError on transport or
    protocol failure. ``max_tokens`` overrides config.max_tokens per
    call when given (unit-size-scaled budget; recorded in metadata).
    """
    if model is None:
        model, grammar_probe = resolve_model(config)

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config.temperature,
        "seed": config.seed,
        "max_tokens": max_tokens if max_tokens is not None else config.max_tokens,
        "stream": False,
    }

    grammar_mode = {"requested": "auto", "applied": "none", "reason": "not_configured"}
    if config.grammar_path and os.path.isfile(config.grammar_path):
        grammar_text = open(config.grammar_path, encoding="utf-8").read()
        advertised = bool(grammar_probe and grammar_probe.get("grammar_advertised"))
        if advertised:
            payload["grammar"] = grammar_text
            grammar_mode = {
                "requested": "auto",
                "applied": "grammar_field",
                "reason": "backend_advertised_grammar",
            }
        else:
            grammar_mode = {
                "requested": "auto",
                "applied": "none",
                "reason": "grammar_file_present_but_backend_not_grammar_capable",
            }
    elif grammar_probe is not None:
        grammar_mode = {
            "requested": "auto",
            "applied": "none",
            "reason": "no_grammar_file_configured",
        }

    response = _http_json(
        f"{config.base_url}/chat/completions",
        payload,
        api_key=config.api_key,
        timeout=config.timeout,
    )

    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenAIBackendError(
            f"malformed chat completion response: {json.dumps(response)[:400]!r}"
        ) from exc
    if not isinstance(content, str):
        raise OpenAIBackendError("assistant content is not a string")

    metadata: dict[str, Any] = {
        "api": "openai",
        "endpoint": f"{config.base_url}/chat/completions",
        "model": model,
        "sampling_parameters": {
            "temperature": config.temperature,
            "seed": config.seed,
            "max_tokens": config.max_tokens,
        },
        "grammar_mode": grammar_mode,
        "grammar_probe": grammar_probe,
        "prompt_sha256": sha256_text(prompt),
        "prompt_chars": len(prompt),
        "raw_output_sha256": sha256_text(content),
        "raw_output_chars": len(content),
        "finish_reason": response["choices"][0].get("finish_reason"),
        "usage": response.get("usage"),
    }

    return ChatObservation(
        raw_output=content,
        request_payload=payload,
        metadata=metadata,
    )
