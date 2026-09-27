#!/usr/bin/env python3
"""Phase 3 invariant-loss diagnosis (corrected, from scratch).

Uses ONLY the actual organizer parser (organizer.SpecParser) and the
current output/organization.json registry.

Sets:
  A          = authoritative invariant-bearing files (Gate patterns)
  B_PARSER   = corpus .spec files with parser entry.invariants nonempty
  B_REGISTRY = source filenames represented by org.json entity_registry.invariants

Records:
  For A - B_PARSER  : filename, authoritative matching lines, marker style,
                      entry.format_type, invariant_count, entry.invariants
  For B_PARSER - B_REGISTRY : filename, entry.format_type, invariant_count,
                      entry.invariants, registry keys for related filenames
"""
import os, re, json, sys, shutil
from pathlib import Path
from collections import OrderedDict

# --- paths (current repository state) ---
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
CORPUS = REPO.parent / "spec_sheet"
WORK = REPO / "work"
WORK.mkdir(parents=True, exist_ok=True)
FULL_RECORDS_FILE = WORK / "invariant_loss_diagnosis.json"
ORG_JSON = REPO / "output" / "organization.json"

import organizer

# --- authoritative gate detection (reproduced EXACTLY) ---
invariant_patterns = (
    r"^\s*INV(?:_DEF)?\b",
    r"^\s*INVARIANT\b",
)

# style discriminators (specific -> general)
style_re = OrderedDict([
    ("INV_DEF",   re.compile(r"^\s*INV_DEF\b",   re.IGNORECASE)),
    ("INVARIANT", re.compile(r"^\s*INVARIANT\b", re.IGNORECASE)),
    ("INV",       re.compile(r"^\s*INV\b",       re.IGNORECASE)),
])

def authoritative_matching_lines(content):
    matched = []
    for line in content.splitlines():
        for p in invariant_patterns:
            if re.match(p, line, re.IGNORECASE):
                matched.append(line)
                break
    return matched

def primary_style(matched_lines):
    for name, rx in style_re.items():
        if any(rx.match(l) for l in matched_lines):
            return name
    return "other"

# --- load registry (B_REGISTRY) from current organization.json ---
with open(ORG_JSON, "r", encoding="utf-8") as f:
    org = json.load(f)
reg_invariants = (org.get("entity_registry", {}) or {}).get("invariants") or {}
if isinstance(reg_invariants, dict):
    B_REGISTRY = {str(k).split(":", 1)[0] for k in reg_invariants.keys()
                  if str(k).strip() and ":" in str(k)}
    # also keep any bare filenames (defensive)
    for k in reg_invariants:
        if ":" not in str(k):
            B_REGISTRY.add(str(k))
else:
    B_REGISTRY = set()

# registry keys index for "related filenames" lookup
reg_keys_by_filename = OrderedDict()
if isinstance(reg_invariants, dict):
    for k in reg_invariants:
        fn = str(k)
        reg_keys_by_filename.setdefault(fn, []).append(str(k))
        if ":" in fn:
            base = fn.split(":", 1)[0]
            reg_keys_by_filename.setdefault(base, []).append(str(k))

# --- parse corpus: build A and B_PARSER ---
parser = organizer.SpecParser()
A = set()
B_PARSER = set()
parsed_entries = OrderedDict()   # filename -> entry
for filename in sorted(p.name for p in CORPUS.glob("*.spec")):
    entry = parser.parse_file(str(CORPUS / filename))
    parsed_entries[filename] = entry
    if authoritative_matching_lines(entry.content):
        A.add(filename)
    if len(entry.invariants) > 0:
        B_PARSER.add(filename)

A_MINUS_B_PARSER = sorted(A - B_PARSER)
A_MINUS_B_REGISTRY = sorted(A - B_REGISTRY)
B_PARSER_MINUS_B_REGISTRY = sorted(B_PARSER - B_REGISTRY)
B_PARSER_INTERSECT_A = sorted(B_PARSER & A)

# --- records ---
records = []
for fn in A_MINUS_B_PARSER:
    entry = parsed_entries[fn]
    matched = authoritative_matching_lines(entry.content)
    records.append(OrderedDict([
        ("filename", fn),
        ("authoritative_matching_lines", matched),
        ("marker_style", primary_style(matched)),
        ("entry.format_type", entry.format_type),
        ("invariant_count", len(entry.invariants)),
        ("entry.invariants", entry.invariants),
        ("set", "A_MINUS_B_PARSER"),
    ]))

for fn in B_PARSER_MINUS_B_REGISTRY:
    entry = parsed_entries[fn]
    related = reg_keys_by_filename.get(fn, [])
    records.append(OrderedDict([
        ("filename", fn),
        ("entry.format_type", entry.format_type),
        ("invariant_count", len(entry.invariants)),
        ("entry.invariants", entry.invariants),
        ("registry_keys_related", related),
        ("set", "B_PARSER_MINUS_B_REGISTRY"),
    ]))

records.sort(key=lambda r: (r.get("set", ""), r["filename"]))

# --- aggregates ---
format_counts_ab = OrderedDict()
format_counts_bparser = OrderedDict()
for fn in A_MINUS_B_PARSER:
    ft = parsed_entries[fn].format_type
    format_counts_ab[ft] = format_counts_ab.get(ft, 0) + 1
for fn in sorted(B_PARSER):
    ft = parsed_entries[fn].format_type
    format_counts_bparser[ft] = format_counts_bparser.get(ft, 0) + 1

# loss stages: marker_to_parser = A-B_PARSER ; parser_to_registry = B_PARSER-B_REGISTRY
marker_to_parser = len(A_MINUS_B_PARSER)
parser_to_registry = len(B_PARSER_MINUS_B_REGISTRY)
other = 0
# cross-check: is B_PARSER_MINUS_B_REGISTRY subset of A_MINUS_B_REGISTRY? (diagnostic)
# B_PARSER - B_REGISTRY could contain files not in A (parser found invariants for files
# that the Gate does not even flag). Report those as 'other' if they are not in A-B_PARSER.
# But by construction B_PARSER-MINUS-B_REGISTRY is the parser->registry loss set.

marker_styles = OrderedDict([("INV", 0), ("INV_DEF", 0), ("INVARIANT", 0), ("other", 0)])
for fn in A_MINUS_B_PARSER:
    ms = primary_style(authoritative_matching_lines(parsed_entries[fn].content))
    marker_styles[ms] = marker_styles.get(ms, 0) + 1

samples_by_format = OrderedDict()
for fn in A_MINUS_B_PARSER:
    ft = parsed_entries[fn].format_type
    samples_by_format.setdefault(ft, [])
    if len(samples_by_format[ft]) < 3:
        samples_by_format[ft].append(fn)
for fn in B_PARSER_MINUS_B_REGISTRY:
    ft = parsed_entries[fn].format_type
    samples_by_format.setdefault(ft, [])
    if len(samples_by_format[ft]) < 3 and fn not in samples_by_format[ft]:
        samples_by_format[ft].append(fn)

# --- persist full records ---
diag = OrderedDict([
    ("meta", OrderedDict([
        ("full_records_file", str(FULL_RECORDS_FILE)),
        ("a_count", len(A)),
        ("b_parser_count", len(B_PARSER)),
        ("b_registry_count", len(B_REGISTRY)),
        ("a_minus_b_parser_count", len(A_MINUS_B_PARSER)),
        ("a_minus_b_registry_count", len(A_MINUS_B_REGISTRY)),
        ("b_parser_minus_b_registry_count", len(B_PARSER_MINUS_B_REGISTRY)),
        ("b_parser_intersect_a_count", len(B_PARSER_INTERSECT_A)),
        ("authoritative_patterns", list(invariant_patterns)),
    ])),
    ("sets", OrderedDict([
        ("A", sorted(A)),
        ("B_PARSER", sorted(B_PARSER)),
        ("B_REGISTRY", sorted(B_REGISTRY)),
        ("A_MINUS_B_PARSER", A_MINUS_B_PARSER),
        ("A_MINUS_B_REGISTRY", A_MINUS_B_REGISTRY),
        ("B_PARSER_MINUS_B_REGISTRY", B_PARSER_MINUS_B_REGISTRY),
        ("B_PARSER_INTERSECT_A", B_PARSER_INTERSECT_A),
    ])),
    ("records", records),
])
with open(FULL_RECORDS_FILE, "w", encoding="utf-8") as f:
    json.dump(diag, f, indent=2, ensure_ascii=False)
shutil.copy2(FULL_RECORDS_FILE, "/tmp/invariant_loss_diagnosis.json")

# --- print ONLY aggregate summary ---
print("INVARIANT_LOSS_DIAGNOSIS_BEGIN")
print(f"A_COUNT={len(A)}")
print(f"B_PARSER_COUNT={len(B_PARSER)}")
print(f"B_REGISTRY_COUNT={len(B_REGISTRY)}")
print(f"A_MINUS_B_PARSER_COUNT={len(A_MINUS_B_PARSER)}")
print(f"A_MINUS_B_REGISTRY_COUNT={len(A_MINUS_B_REGISTRY)}")
print(f"B_PARSER_MINUS_B_REGISTRY_COUNT={len(B_PARSER_MINUS_B_REGISTRY)}")
print(f"B_PARSER_INTERSECT_A_COUNT={len(B_PARSER_INTERSECT_A)}")
print("")
print("FORMAT_COUNTS_A_MINUS_B_PARSER:")
for ft, n in format_counts_ab.items():
    print(f"  {ft}={n}")
print("")
print("FORMAT_COUNTS_B_PARSER:")
for ft, n in format_counts_bparser.items():
    print(f"  {ft}={n}")
print("")
print("LOSS_STAGE_COUNTS:")
print(f"  marker_to_parser={marker_to_parser}")
print(f"  parser_to_registry={parser_to_registry}")
print(f"  other={other}")
print("")
print("MARKER_STYLES_A_MINUS_B_PARSER:")
for k in ["INV", "INV_DEF", "INVARIANT"]:
    print(f"  {k}={marker_styles.get(k, 0)}")
print("")
print("SAMPLES:")
for ft, names in samples_by_format.items():
    for nm in names:
        print(f"  {ft}: {nm}")
print("")
print(f"FULL_RECORDS_FILE={FULL_RECORDS_FILE}")
print("INVARIANT_LOSS_DIAGNOSIS_END")
