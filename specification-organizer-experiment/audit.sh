#!/bin/bash
cd ~/Chron-LLM/specification-organizer-experiment || exit 1

echo "===== L1. RAW OBSERVATION: BOUNDARY AROUND GAPS ====="
python - <<'PY'
import json
from pathlib import Path

p = Path("diagnostics/a1_segment/e6de5b826380706705559d494f0fffd317553efc788b36d3ee4ca500b3379a8e.json")
d = json.loads(p.read_text(encoding="utf-8"))
raw = d.get("raw_output", "")
print("diagnostic:", p)
print("extraction_status:", d.get("extraction_status"))
print("validation_status:", d.get("validation_status"))
print("error:", d.get("error"))

try:
    obj = json.loads(raw)
    boundaries = obj.get("boundaries", [])
    print("raw_boundary_count:", len(boundaries))
    for i, b in enumerate(boundaries):
        if (
            b.get("line_start", 0) <= 710 <= b.get("line_end", 0)
            or b.get("line_start", 0) <= 756 <= b.get("line_end", 0)
            or b.get("line_end", 0) in (708, 709, 710, 755, 756, 757)
            or b.get("line_start", 0) in (708, 709, 710, 755, 756, 757)
        ):
            print(f"boundary[{i}]:", b)
except Exception as e:
    print("RAW_JSON_PARSE_ERROR:", repr(e))
    print("raw_output_repr:", repr(raw[:3000]))
PY

echo
echo "===== L2. NORMALIZATION IMPLEMENTATION ====="
grep -nE 'def normalize|def .*boundary|line_start|line_end|source_text|unit_id' \
  tools/normalize_boundaries.py tools/a1_segment.py 2>/dev/null

echo
echo "===== L3. NORMALIZATION SOURCE ====="
sed -n '1,260p' tools/normalize_boundaries.py

echo
echo "===== L4. COVERAGE VALIDATION CONTRACT ====="
grep -nE 'def validate_units_json|previous_end|line_start|line_end|coverage|gap|all.lines|source_lines' \
  tools/validate_a1_artifact.py

echo
echo "===== L5. NORMALIZATION TEST CONTRACT ====="
grep -nE 'gap|coverage|missing|line_start|line_end|normalize|whitespace|unsorted' \
  tests/test_normalize_boundaries.py

echo
echo "===== L6. PRIOR DIAGNOSTIC SNAPSHOT ====="
OLD="diagnostics/a1_segment/e6de5b826380706705559d494f0fffd317553efc788b36d3ee4ca500b3379a8e.json.before_machine_output_20261009_234202"
if test -f "$OLD"; then
  python - <<'PY'
import json
from pathlib import Path

p = Path("diagnostics/a1_segment/e6de5b826380706705559d494f0fffd317553efc788b36d3ee4ca500b3379a8e.json.before_machine_output_20261009_234202")
d = json.loads(p.read_text(encoding="utf-8"))
print("snapshot:", p)
for k in ("timestamp_utc", "document_path", "extraction_status",
          "validation_status", "error", "raw_output"):
    v = d.get(k)
    if k == "raw_output" and isinstance(v, str):
        print(k + ":", repr(v[:4000]))
    else:
        print(k + ":", v)
print("metadata:", json.dumps(d.get("metadata"), ensure_ascii=False, indent=2))
PY
else
  echo "PRIOR_DIAGNOSTIC_SNAPSHOT_NOT_FOUND"
fi

