#!/usr/bin/env python3
"""Sweep entrypoint for INV-H1 seed-independence runs.

Prints the canonical aggregate JSON of tier-1 + tier-2 sweeps. Run under
different PYTHONHASHSEED values; output must be byte-identical (INV-H1).

Usage:
  run_sweep.py [--seed N] [--emit-results PATH]
    --seed N          corpus seed for the tier-2 fuzz sample (default 19205)
    --emit-results P  also write the full per-case results map to PATH
                      (governance evidence artifact, D13-4 E1)
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import test_l1_validation_harness as H  # noqa: E402


def _arg(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default


if __name__ == "__main__":
    seed = int(_arg("--seed", "19205"))
    emit = _arg("--emit-results")
    cases = H.exhaustive_scenarios() + H.fuzz_corpus(seed)
    aggregate = H.sweep(cases)
    print(H.L1.canonical_json(aggregate))
    if emit:
        with open(emit, "w", encoding="utf-8") as fh:
            fh.write(H.L1.canonical_json(aggregate) + "\n")
