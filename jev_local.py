#!/usr/bin/env python3
"""JEV-style typed classifier for the Chron-LLM pipeline, on the local llama.cpp server.

Ports pi's classifier contract (docs/models.md#use-classifier-models, docs/codemode.md):

    classify(state, questions) -> answers

  question types
    choice : {type:"choice", instructions, criteria:{label: meaning}}     -> {choice, probabilities, confidence}
    score  : {type:"score",  instructions, criteria:[levels, lowest first]} -> {score, confidence}
    bool   : {type:"bool",   instructions, criteria:{true:..., false:...}}  -> {probability}

Nothing free-form is parsed: the model answers with ONE option letter, and the
answer distribution over labels becomes the probability/confidence field.

Two scoring backends:
  sample  (default, works on this server)  draw N single-token samples at temperature T,
                                            count label frequencies -> probabilities.
  logprob (needs a raw llama-server exposing /completion with logprobs) read the
                                            next-token logprob mass, divide logits by T, softmax.

Measured on this machine (qwen3.8-flash-next-iq3_xxs @ http://172.18.0.1:8080):
  - /completion and /v1/completions -> 404, logprobs -> null, so `logprob` mode is unavailable here.
  - thinking must be OFF or max_tokens=1 only yields a reasoning token:
        chat_template_kwargs: {"enable_thinking": false}   (or reasoning_effort: "none")
  - one label request ~= 0.13 s.

Usage:
    python3 jev_local.py --demo
    python3 jev_local.py --pair pair_results/pair_12.json --samples 12
    python3 jev_local.py --component component_contexts/component-003.json
    python3 jev_local.py --all --out jev_labels.json
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import os
import urllib.request
from collections import Counter
from pathlib import Path

BASE_URL = os.environ.get("LLAMA_BASE_URL", "")
API_KEY = os.environ.get("LLAMA_API_KEY") or ""
MODEL_ID = os.environ.get("LLAMA_MODEL", "")
CACHE_PATH = Path("jev_cache.json")

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
THINKING_OFF = {"chat_template_kwargs": {"enable_thinking": False}}


# ------------------------------------------------------------ discovery -----

def _load_config() -> tuple[str, str, str]:
    """Fill in base url / api key / model id from env, then pi's stored config."""
    global API_KEY, MODEL_ID, BASE_URL
    auth = Path.home() / ".pi" / "agent" / "auth.json"
    store = Path.home() / ".pi" / "agent" / "models-store.json"
    if auth.exists():
        try:
            entry = json.loads(auth.read_text()).get("llama.cpp") or {}
            API_KEY = API_KEY or entry.get("key") or ""
            BASE_URL = BASE_URL or (entry.get("env") or {}).get("LLAMA_BASE_URL") or ""
        except Exception:
            pass
    if store.exists():
        try:
            data = json.loads(store.read_text())
            providers = data.get("providers") if isinstance(data.get("providers"), dict) else data
            for provider in providers.values():
                for model in (provider or {}).get("models", []):
                    if model.get("api") == "openai-completions":
                        MODEL_ID = MODEL_ID or model.get("id", "")
                        BASE_URL = BASE_URL or model.get("baseUrl", "")
                        return API_KEY, MODEL_ID, BASE_URL
        except Exception:
            pass
    BASE_URL = BASE_URL or "http://172.18.0.1:8080"
    return API_KEY, MODEL_ID, BASE_URL


def _v1(base: str) -> str:
    base = base.rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


# --------------------------------------------------------------- prompt -----

def render_question(question_id: str, question: dict) -> tuple[str, dict]:
    kind = question["type"]
    if kind == "choice":
        labels = list(question["criteria"].keys())
        letters = LETTERS[: len(labels)]
        body = "\n".join(f"- {letters[i]}: {label} -- {question['criteria'][label]}" for i, label in enumerate(labels))
        spec = {"id": question_id, "kind": kind, "labels": labels, "letters": letters}
    elif kind == "score":
        levels = list(question["criteria"])
        letters = LETTERS[: len(levels)]
        body = "\n".join(f"- {letters[i]}: level {i} -- {level}" for i, level in enumerate(levels))
        spec = {"id": question_id, "kind": kind, "labels": levels, "letters": letters}
    elif kind == "bool":
        letters = "TF"
        body = (
            f"- T: true -- {question['criteria']['true']}\n"
            f"- F: false -- {question['criteria']['false']}"
        )
        spec = {"id": question_id, "kind": kind, "labels": ["true", "false"], "letters": letters}
    else:
        raise ValueError(f"unknown question type: {kind}")

    block = f"### {question_id}\nType: {kind}\n{question['instructions']}\n{body}"
    prompt = (
        "You are a classifier. Answer with exactly one option letter and nothing else: "
        "no explanation, no punctuation, no code fence, no restating the label.\n\n"
        f"## State\n{json.dumps(question['state'], ensure_ascii=False, sort_keys=True)}\n\n"
        f"## Question\n{block}\n\n## Answer\n"
    )
    return prompt, spec


# --------------------------------------------------------------- client -----

def _post(path: str, payload: dict, base: str, api_key: str) -> dict:
    req = urllib.request.Request(
        f"{_v1(base)}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.loads(response.read().decode())


def sample_letter(prompt: str, temperature: float, seed: int, base: str, api_key: str, model_id: str) -> str:
    """One request -> one option letter. Thinking is forced off; otherwise the
    single token is a reasoning token and content comes back null."""
    base_payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1,
        "temperature": temperature,
        "seed": seed,
    }
    for extra in (THINKING_OFF, {"reasoning_effort": "none"}, {}):
        try:
            data = _post("/chat/completions", {**base_payload, **extra}, base, api_key)
        except Exception:
            continue
        message = (data.get("choices") or [{}])[0].get("message") or {}
        text = message.get("content")
        if text:
            return text.strip()
    return ""


def _softmax(values: list[float]) -> list[float]:
    top = max(values)
    exps = [math.exp(v - top) for v in values]
    total = sum(exps)
    return [e / total for e in exps] if total > 0 else [1.0 / len(values)] * len(values)


def _answer_from_probs(spec: dict, probs: list[float]) -> dict:
    best = max(range(len(probs)), key=lambda i: probs[i])
    if spec["kind"] == "choice":
        return {
            "type": "choice",
            "choice": spec["labels"][best],
            "probabilities": {label: round(p, 4) for label, p in zip(spec["labels"], probs)},
            "confidence": round(probs[best], 4),
        }
    if spec["kind"] == "score":
        return {
            "type": "score",
            "score": round(sum(i * p for i, p in enumerate(probs)), 3),
            "levels": [round(p, 4) for p in probs],
            "confidence": round(max(probs), 4),
        }
    return {"type": "bool", "probability": round(probs[0], 4)}


def _score_logprobs(spec: dict, top_logprobs: list[dict], temperature: float) -> dict:
    logits = {}
    for entry in top_logprobs:
        token = (entry.get("token") or "").strip()
        if token in spec["letters"] and token not in logits:
            logits[token] = float(entry.get("logprob", 0.0))
    raw = [logits.get(letter, -20.0) for letter in spec["letters"]]
    return _answer_from_probs(spec, _softmax([value / max(temperature, 1e-6) for value in raw]))


def classify(
    state: dict,
    questions: dict,
    *,
    mode: str = "sample",
    samples: int = 8,
    temperature: float = 0.8,
    use_cache: bool = True,
) -> dict:
    api_key, model_id, base = _load_config()
    if not model_id:
        raise SystemExit("no model id: set LLAMA_MODEL, or let pi write ~/.pi/agent/models-store.json")

    cache: dict = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text())
        except Exception:
            cache = {}

    answers: dict[str, dict] = {}
    hits = misses = 0
    for question_id, question in questions.items():
        question = {**question, "state": state}
        prompt, spec = render_question(question_id, question)
        key = hashlib.sha256(
            json.dumps(
                {"model": model_id, "mode": mode, "samples": samples, "temperature": temperature, "prompt": prompt},
                sort_keys=True,
            ).encode()
        ).hexdigest()
        if use_cache and key in cache:
            answers[question_id] = cache[key]
            hits += 1
            continue

        if mode == "logprob":
            data = _post(
                "/completion",
                {
                    "model": model_id,
                    "prompt": prompt,
                    "max_tokens": 1,
                    "temperature": 1.0,
                    "logprobs": True,
                    "top_logprobs": 32,
                },
                base,
                api_key,
            )
            top = ((data.get("choices") or [{}])[0].get("logprobs") or {}).get("top_logprobs") or []
            if not top:
                raise SystemExit("no logprobs from /completion; use --mode sample on this server")
            answer = _score_logprobs(spec, top, temperature)
        else:
            draws = samples if temperature > 0 else 1
            counts: Counter[str] = Counter()
            for i in range(draws):
                letter = sample_letter(prompt, temperature, 42 + i, base, api_key, model_id)[:1]
                if letter in spec["letters"]:
                    counts[letter] += 1
            total = sum(counts.values()) or 1
            probs = [counts.get(letter, 0) / total for letter in spec["letters"]]
            answer = _answer_from_probs(spec, probs)
            answer["samples"] = total
            answer["counts"] = {
                spec["labels"][spec["letters"].index(letter)]: count for letter, count in counts.items()
            }

        answers[question_id] = answer
        cache[key] = answer
        misses += 1

    if use_cache:
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    return {"model": model_id, "mode": mode, "cache": f"{hits} hit / {misses} miss", "answers": answers}


# ------------------------------------------------------------- questions ----

# Labels are taken from the pipeline's own closed vocabulary (measured over
# pair_results/pair_*.json), so answers aggregate against existing output.
PAIR_QUESTIONS = {
    "relationship": {
        "type": "choice",
        "instructions": "What is the normative relationship between the two specification documents?",
        "criteria": {
            "EXACT_DUPLICATE": "The same contract restated; neither side adds normative content",
            "PARTIAL_OVERLAP": "Substantial shared content, but the two differ in guarantees or mechanism",
            "PARENT_CHILD": "One document is the normative parent; the other refines or specializes it",
            "SUPERSEDED": "One document replaces the other; the older one is obsolete",
            "INDEPENDENT": "Different concerns with no normative overlap",
        },
    },
    "recommended_action": {
        "type": "choice",
        "instructions": "Which single action should the pipeline take on this pair?",
        "criteria": {
            "KEEP_BOTH": "Keep both documents unchanged",
            "MERGE_B_INTO_A": "Fold document B's content into document A",
            "MERGE_A_INTO_B": "Fold document A's content into document B",
            "KEEP_A_DELETE_B": "Keep A and delete B as redundant",
            "DEPRECATE_OBSOLETE": "Mark the obsolete side deprecated instead of deleting it",
        },
    },
    "invariant_conflict": {
        "type": "bool",
        "instructions": "Do the two documents assert invariants that cannot both hold at runtime?",
        "criteria": {
            "true": "At least one invariant pair is mutually exclusive, e.g. mutable shared state versus immutable snapshots",
            "false": "No mutually exclusive invariant pair is present",
        },
    },
    "merge_safety": {
        "type": "score",
        "instructions": "How safe is it to merge these documents automatically, without a human decision?",
        "criteria": [
            "must not be merged, semantics would be lost",
            "merge only with a manual review of the diff",
            "merge is safe after renaming or aliasing",
            "merge is safe as-is, one document is a strict superset",
        ],
    },
}

COMPONENT_QUESTIONS = {
    "phase": {
        "type": "choice",
        "instructions": "Which Chron phase does this component belong to?",
        "criteria": {
            "A": "Constitution or normative rules",
            "B": "Schema and data contracts",
            "C": "Runtime behaviour and kernel semantics",
            "D": "Tooling, automation, or verification only",
        },
    },
    "ready_to_implement": {
        "type": "bool",
        "instructions": "Is this component specified precisely enough to implement without further questions?",
        "criteria": {
            "true": "Types, invariants, and ownership are all explicit",
            "false": "At least one of types, invariants, or ownership is missing or ambiguous",
        },
    },
    "risk": {
        "type": "score",
        "instructions": "How much risk does implementing this component as written carry for source-of-truth consistency?",
        "criteria": [
            "no risk",
            "low risk, a local fix is enough",
            "medium risk, other components must change too",
            "high risk, it could fork a source of truth",
        ],
    },
}


# ------------------------------------------------------------------ cli -----

# Fields that would leak the answer back into the classifier: the state must be
# the evidence only, never the label the pipeline already produced.
LEAKY_KEYS = (
    "relationship",
    "recommended_action",
    "suggested_action",
    "recommendation",
    "action",
    "decision",
    "integration_rationale",
    "rationale",
    "phase_alignment",
)


def _strip_labels(item):
    if isinstance(item, dict):
        return {
            key: _strip_labels(value)
            for key, value in item.items()
            if key not in LEAKY_KEYS
        }
    if isinstance(item, list):
        return [_strip_labels(entry) for entry in item]
    return item


def _load_pair(path: Path) -> dict:
    data = json.loads(path.read_text())
    results = data.get("results") or data.get("processed_pairs") or [data]
    if isinstance(results, dict):
        results = [results]
    return {"source": str(path), "pair": _strip_labels(results[0] if results else {})}


def _load_component(path: Path) -> dict:
    return {"source": str(path), "component": json.loads(path.read_text())}


def _show(result: dict) -> None:
    print(f"model={result['model']} mode={result['mode']} cache={result['cache']}")
    for question_id, answer in result["answers"].items():
        extra = f" samples={answer.get('samples')}" if "samples" in answer else ""
        if answer["type"] == "choice":
            print(f"  {question_id}: {answer['choice']} conf={answer['confidence']} {answer['probabilities']}{extra}")
        elif answer["type"] == "score":
            print(f"  {question_id}: score={answer['score']} conf={answer['confidence']} levels={answer['levels']}{extra}")
        else:
            print(f"  {question_id}: P(true)={answer['probability']}{extra}")


def main() -> None:
    parser = argparse.ArgumentParser(description="JEV-style typed classifier over the local llama.cpp server")
    parser.add_argument("--pair", help="one pair_results/*.json")
    parser.add_argument("--component", help="one component_contexts/*.json")
    parser.add_argument("--all", action="store_true", help="every pair_results/pair_*.json")
    parser.add_argument("--demo", action="store_true", help="pair_results/pair_1.json")
    parser.add_argument("--mode", choices=["sample", "logprob"], default="sample")
    parser.add_argument("--samples", type=int, default=8, help="draws per question (sample mode)")
    parser.add_argument("--temperature", type=float, default=0.8, help="sampling temperature; 0 = one greedy draw")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--out", help="write all answers to a JSON file")
    args = parser.parse_args()

    targets: list[tuple[dict, dict]] = []
    if args.demo:
        targets.append((_load_pair(Path("pair_results/pair_1.json")), PAIR_QUESTIONS))
    if args.pair:
        targets.append((_load_pair(Path(args.pair)), PAIR_QUESTIONS))
    if args.component:
        targets.append((_load_component(Path(args.component)), COMPONENT_QUESTIONS))
    if args.all:
        for path in sorted(glob.glob("pair_results/pair_*.json"), key=lambda p: int(Path(p).stem.split("_")[-1])):
            targets.append((_load_pair(Path(path)), PAIR_QUESTIONS))

    if not targets:
        parser.print_help()
        return

    dump = []
    for state, questions in targets:
        print(f"=== {state['source']}")
        try:
            result = classify(
                state,
                questions,
                mode=args.mode,
                samples=args.samples,
                temperature=args.temperature,
                use_cache=not args.no_cache,
            )
            _show(result)
            dump.append({"source": state["source"], "answers": result["answers"]})
        except Exception as error:
            print(f"  error: {error}")

    if args.out:
        Path(args.out).write_text(json.dumps(dump, ensure_ascii=False, indent=2))
        print(f"wrote {args.out} ({len(dump)} items)")


if __name__ == "__main__":
    main()
