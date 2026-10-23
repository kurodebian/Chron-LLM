#!/usr/bin/env python3
"""Sweep entrypoint for INV-H1 seed-independence runs.

Prints the canonical aggregate JSON of tier-1 + tier-2 sweeps. Run under
different PYTHONHASHSEED values; output must be byte-identical (INV-H1).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import test_l1_validation_harness as H  # noqa: E402

if __name__ == "__main__":
    cases = H.exhaustive_scenarios() + H.fuzz_corpus()
    print(H.L1.canonical_json(H.sweep(cases)))
