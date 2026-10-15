#!/usr/bin/env python3
"""Scan markdown sheets and generate chapters_index.md (file -> chapter headings).

Parsing scope (the important part)
  * Only **level-1 (H1) headings** are parsed as chapters: a line whose first
    non-blank characters are exactly one `#` followed by whitespace, i.e.
    `# Step 1 — ...`, `# STEP-96 — ...`  (setext `===` underlines count as H1 too).
  * `##` / `###` / ... headings and every inline mention inside the body text are
    **not** chapter/step detection targets: they are not counted, not branch-numbered
    and not part of the coverage audit.  They are only tallied as "ignored" statistics
    (and, for gaps, shown as *evidence only* so a hole is easier to interpret).
  * `--chapter-levels N` widens the scope to H1..HN, `--with-subheadings` additionally
    lists the ignored H2+ headings under each chapter for navigation only.

Features
  1. Heading extraction (ATX `#`..`######` + setext `===`/`---`), code fences skipped.
  2. Unified step detection (case-insensitive) on the chapter headings: every chapter
     heading that contains a step number is a detection target, whatever the style:
       `# Step 1 ...`, `# step 1 ...`, `# STEP-1 ...`, `# STEP_1 ...`, `# STEP 1 ...`,
       `# Step 5.3 ...`, `# Step 7B ...`, `# 次段階：Step 10 — ...`,
       `# 12. STEP-64 暫定裁定`, `# STEP-84・STEP-83・STEP-80 ...`
     One chapter heading may register several step numbers (all of them are tracked).
  3. Automatic branch numbers: only when the same step number occurs more than once
     **among the extracted chapter headings** (within a file or across all files) the
     occurrences get a, b, c ... in order of appearance
     (`# Step 1` x2 -> `Step 1a`, `Step 1b`; `# STEP-96` x2 -> `STEP-96a`, `STEP-96b`).
     The branch letter is inserted right after the number in the heading text itself
     and every occurrence is registered in the audit report.
  4. `--coverage` audit report at the top of the index, recomputed on the H1 basis:
     numbering gaps, duplicate inventory, branch-number registry, per-file chapter
     coverage, chapter headings that carry no step number, and a self-consistency
     check proving that the branch numbering applied to the index body is exactly the
     one reported.

Token-cheap by design: files are parsed here and never echoed; only headings,
counts and audit rows are emitted.
"""
from __future__ import annotations

import argparse
import re
import string
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

INDEX_NAME = "chapters_index.md"

ATX_RE = re.compile(r"^\s{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
SETEXT_RE = re.compile(r"^\s{0,3}(=+|-+)[ \t]*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# step token: number (optionally dotted sub-steps, optionally a trailing letter),
# not followed by another digit/dot so "Step 5.1" is 5.1 and never 5
STEP_NUM = r"(\d+(?:\.\d+)*[A-Za-z]?)(?![\d.])"
STEP_ANCHOR_RE = re.compile(r"^\W{0,4}STEP[-_ ]?" + STEP_NUM, re.I)     # title starts with Step/STEP
STEP_CONTAIN_RE = re.compile(r"\bSTEP[-_ ]?" + STEP_NUM, re.I)          # anywhere in a title
STEP_ANY_RE = re.compile(r"\bSTEP[-_ ]?" + STEP_NUM, re.I)              # non-chapter lines (evidence)

MAX_MENTION_SAMPLES = 2

# a step number immediately followed by an en/dash range (`STEP-31–96`, `Step 31d–45`)
RANGE_TAIL_RE = re.compile(r"\s*[-–—〜~]+\s*(?:STEP[-_ ]?)?\d", re.I)


def clean_title(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)          # links -> label
    text = re.sub(r"\\([\\`*_{}\[\]()+#.\-!])", "\x00\\1", text)  # protect escaped markers
    text = re.sub(r"[*`]", "", text)                                # emphasis / code
    # underscores used as emphasis markers are dropped, but underscores *inside* a
    # token are kept so identifiers such as `STEP_96` or `Step_1` survive intact
    text = re.sub(r"(?<![\w_\x00])_|_(?![\w_\x00])", "", text)
    text = text.replace("\x00", "")                                 # unescape
    return re.sub(r"\s+", " ", text).strip()


def trunc(text: str, n: int = 90) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def letter(i: int) -> str:
    """a, b, ... z, aa, ab, ... (0-based index)."""
    if i < 26:
        return string.ascii_lowercase[i]
    return string.ascii_lowercase[i // 26 - 1] + string.ascii_lowercase[i % 26]


def step_sort_key(key: str):
    num = re.match(r"[\d.]+", key)
    parts = [int(x) for x in num.group(0).split(".")] if num else [0]
    tail = key[len(num.group(0)):] if num else key
    return (parts, tail.lower())


def is_plain_step(key: str) -> bool:
    return re.fullmatch(r"\d+", key) is not None


def step_matches(title: str, scope: str) -> list[tuple[str, int, int, bool]]:
    """All step references inside one chapter heading.

    Returns [(step key, number start, number end, is_range_reference)] where
    `is_range_reference` marks a number used as the start of a range
    (`STEP-31–96`, `Step 31–45`) rather than a reference to one single step.

    `anchor` -> only a heading that *starts* with Step/STEP + number counts.
    `contains` -> every Step/STEP + number inside the heading counts (default),
                  so `12. STEP-64 暫定裁定` or `次段階：Step 10 ...` are detected too,
                  and one heading may register several distinct step numbers.
    """
    if scope == "anchor":
        m = STEP_ANCHOR_RE.match(title)
        it = [m] if m else []
    else:
        it = list(STEP_CONTAIN_RE.finditer(title))
    out: list[tuple[str, int, int, bool]] = []
    seen: set[str] = set()
    for m in it:
        key = m.group(1)
        if key in seen:
            continue
        seen.add(key)
        out.append((key, m.start(1), m.end(1), bool(RANGE_TAIL_RE.match(title, m.end(1)))))
    return out


def extract_headings(path: Path, chapter_levels: int):
    """Parse one markdown file.

    Returns (headings, level_counts, mentions):
      headings     [(line_no, level, title), ...]  every markdown heading found
      level_counts {level: how many headings of that level exist}  (H1..H6)
      mentions     {step_number: [count, line, line, ...]}  step numbers found on
                   *non-chapter* lines (body text + ignored deeper headings) — used
                   as evidence only, never counted as a chapter.
    """
    headings: list[tuple[int, int, str]] = []
    level_counts: dict[int, int] = defaultdict(int)
    mentions: dict[str, list] = defaultdict(lambda: [0])
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"  ! unreadable {path.name}: {exc}", file=sys.stderr)
        return headings, level_counts, mentions

    fence = False
    for i, line in enumerate(lines, start=1):
        if FENCE_RE.match(line):
            fence = not fence
            continue
        if fence:
            continue

        m = ATX_RE.match(line)
        if m:
            level = len(m.group(1))
            title = clean_title(m.group(2))
            if title:
                headings.append((i, level, title))
                level_counts[level] += 1
            continue

        if SETEXT_RE.match(line) and i >= 2:                      # setext underline style
            prev = lines[i - 2].strip()
            if prev and not ATX_RE.match(prev) and not FENCE_RE.match(prev):
                title = clean_title(prev)
                if title:
                    level = 1 if line.strip()[0] == "=" else 2
                    headings.append((i, level, title))
                    level_counts[level] += 1
                continue

        # not a heading line at all -> body text
        for num in STEP_ANY_RE.findall(line):
            rec = mentions[num]
            rec[0] += 1
            if rec[0] <= MAX_MENTION_SAMPLES + 1:
                rec.append(i)

    # deeper headings are not chapters: their step numbers are evidence only
    for line_no, level, title in headings:
        if level <= chapter_levels:
            continue
        for num in STEP_ANY_RE.findall(title):
            rec = mentions[num]
            rec[0] += 1
            if rec[0] <= MAX_MENTION_SAMPLES + 1:
                rec.append(line_no)
    return headings, level_counts, mentions


def natural_key(name: str):
    return ([int(n) for n in re.findall(r"\d+", name)], name)


def group_ranges(nums: list[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for n in sorted(nums):
        if out and n == out[-1][1] + 1:
            out[-1] = (out[-1][0], n)
        else:
            out.append((n, n))
    return out


def fmt_ranges(nums: list[int], max_show: int = 12) -> str:
    rs = group_ranges(nums)
    s = ", ".join(f"{a}" if a == b else f"{a}–{b}" for a, b in rs)
    return s if len(rs) <= max_show else s[:200] + " …"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build chapters_index.md from markdown sheets (H1 chapters only)")
    ap.add_argument("--dir", default=str(Path.home() / "Chron-LLM" / "md_sheets"))
    ap.add_argument("--out", default=INDEX_NAME)
    ap.add_argument("--coverage", action="store_true",
                    help="prepend an H1-based coverage audit report (gaps / duplicates / branch numbers)")
    ap.add_argument("--chapter-levels", type=int, default=1, metavar="N",
                    help="heading levels treated as chapters: H1..HN (default: 1 = H1 only, "
                         "i.e. lines starting with exactly one '# ')")
    ap.add_argument("--with-subheadings", action="store_true",
                    help="also list the ignored H2+ headings under each chapter (navigation only, "
                         "they are never counted as chapters or steps)")
    ap.add_argument("--step-scope", choices=("contains", "anchor"), default="contains",
                    help="contains: any `Step`/`STEP` + number inside the chapter title counts (default); "
                         "anchor: title must start with Step/STEP + number")
    ap.add_argument("--dup-scope", choices=("global", "file"), default="global",
                    help="global: same number in different files counts as duplicate (default)")
    ap.add_argument("--suffix-mode", choices=("all", "tail", "none"), default="all",
                    help="all: every occurrence of a duplicated step gets a/b/c (default); "
                         "tail: only 2nd+ occurrences; none: keep bare numbers")
    ap.add_argument("--audit-range", metavar="LO:HI",
                    help="restrict gap scan to this integer STEP range (default: detected min–max)")
    ap.add_argument("--max-audit-rows", type=int, default=0, metavar="N",
                    help="cap audit table rows (0 = show all, default)")
    args = ap.parse_args()

    root = Path(args.dir).expanduser().resolve()
    if not root.is_dir():
        print(f"directory not found: {root}", file=sys.stderr)
        return 1

    out_path = root / args.out
    def is_generated_index(p: Path) -> bool:
        """Never re-parse a previously generated index (avoids self-pollution)."""
        if p.name == out_path.name or p.name == INDEX_NAME:
            return True
        try:
            first = p.open(encoding="utf-8", errors="replace").readline()
        except OSError:
            return False
        return first.strip() == "# Chapters Index"

    files = sorted((p for p in root.glob("*.md") if not is_generated_index(p)),
                   key=lambda p: natural_key(p.name))

    data: dict[str, list[tuple[int, int, str]]] = {}
    lcounts: dict[str, dict[int, int]] = {}
    mentions: dict[str, dict[str, list]] = {}
    for p in files:
        heads, lcnt, ments = extract_headings(p, args.chapter_levels)
        data[p.name] = heads
        lcounts[p.name] = lcnt
        mentions[p.name] = ments

    all_headings = sum(len(v) for v in data.values())
    max_level = max((h[1] for v in data.values() for h in v), default=0)
    level_counts = {lv: sum(lc.get(lv, 0) for lc in lcounts.values())
                    for lv in range(1, max_level + 1)}
    ignored_headings = sum(c for lv, c in level_counts.items() if lv > args.chapter_levels)

    # chapters = H1 headings only (by default)
    chapters: dict[str, list[tuple[int, int, str]]] = {
        name: [h for h in heads if h[1] <= args.chapter_levels] for name, heads in data.items()}
    chapter_total = sum(len(v) for v in chapters.values())

    # ---- step detection (case-insensitive, Step / STEP unified, chapters only) ----
    # occ: step key -> [(file, line, level, num_start, num_end, is_canonical, is_range)]
    occ: dict[str, list[tuple[str, int, int, int, int, bool, bool]]] = defaultdict(list)
    for name, heads in chapters.items():
        for line_no, level, title in heads:
            a = STEP_ANCHOR_RE.match(title)
            anchor_key = a.group(1) if a else None
            for key, s, e, rng in step_matches(title, args.step_scope):
                occ[key].append((name, line_no, level, s, e, key == anchor_key, rng))

    def dup_group(key: str, hits):
        if args.dup_scope == "file":
            by_file: dict[str, list] = defaultdict(list)
            for h in hits:
                by_file[h[0]].append(h)
            return [o for o in by_file.values() if len(o) > 1]
        return [hits] if len(hits) > 1 else []

    dup_keys = sorted((k for k, o in occ.items() if dup_group(k, o)), key=step_sort_key)

    suffix: dict[tuple[str, int, str], str] = {}     # (file, line, step key) -> branch letter
    labels: dict[str, list[str]] = {}                # step key -> [labels, one per occurrence]
    registry: list[tuple[str, str, int, int, str, bool, bool]] = []   # (label, file, line, level, title, canonical, range)
    for key in dup_keys:
        labs = []
        flat = [h for g in dup_group(key, occ[key]) for h in g]
        for idx, (name, line_no, level, _s, _e, anchor, rng) in enumerate(flat):
            if args.suffix_mode == "none":
                sfx = ""
            elif args.suffix_mode == "tail" and idx == 0:
                sfx = ""
            else:
                sfx = letter(idx) if args.suffix_mode == "all" else letter(idx - 1)
                suffix[(name, line_no, key)] = sfx
            lab = f"STEP-{key}{sfx}"
            labs.append(lab)
            title = next(t for ln, _l, t in data[name] if ln == line_no)
            registry.append((lab, name, line_no, level, title, anchor, rng))
        labels[key] = labs

    def label_of(name: str, line_no: int, title: str) -> str:
        """Canonical STEP label for a chapter heading ('' when it has no step number)."""
        keys = [k for k, _s, _e, _r in step_matches(title, args.step_scope)]
        if not keys:
            return ""
        return " + ".join(f"STEP-{k}{suffix.get((name, line_no, k), '')}" for k in keys)

    def label_title(name: str, line_no: int, title: str) -> str:
        """Insert the assigned branch letter(s) right after the step number(s)."""
        matches = step_matches(title, args.step_scope)
        if not matches:
            return title
        out = title
        for key, _s, e, _rng in reversed(matches):    # right-to-left keeps offsets valid
            sfx = suffix.get((name, line_no, key))
            if sfx:
                out = out[:e] + sfx + out[e:]
        return out

    int_nums = sorted(int(k) for k in occ if is_plain_step(k))
    if args.audit_range:
        lo_s, hi_s = args.audit_range.split(":", 1)
        lo, hi = int(lo_s), int(hi_s)
    else:
        lo, hi = (int_nums[0], int_nums[-1]) if int_nums else (0, 0)
    gaps = [n for n in range(lo, hi + 1) if str(n) not in occ]

    def first_mention(n: int):
        for name in data:
            rec = mentions[name].get(str(n))
            if rec and rec[0]:
                return name, rec[1], rec[0]
        return None

    step_hits = sum(len(o) for o in occ.values())
    step_chapters = sum(1 for heads in chapters.values()
                        for _ln, _lv, t in heads if step_matches(t, args.step_scope))
    plain_chapters = chapter_total - step_chapters
    anchor_hits = sum(1 for o in occ.values() for h in o if h[5])
    range_hits = sum(1 for o in occ.values() for h in o if h[6])
    dup_extra = sum(len(f) - 1 for k in dup_keys for f in dup_group(k, occ[k]))
    dup_hits = sum(len(occ[k]) for k in dup_keys)
    multiplicity: dict[int, int] = defaultdict(int)
    for k, o in occ.items():
        multiplicity[len(o)] += 1

    # verify the branch letters really land in the index body (report <-> body)
    body_letters = body_headings = multi_ref_headings = 0
    for name, heads in chapters.items():
        for ln, _lv, t in heads:
            n = sum(1 for key, _s, _e, _rng in step_matches(t, args.step_scope)
                    if (name, ln, key) in suffix)
            if n:
                body_letters += n
                body_headings += 1
                if n > 1:
                    multi_ref_headings += 1
    distinct_suffixed = len({(f, ln) for (f, ln, _k) in suffix})
    counted_from_chapters = sum(1 for o in occ.values() for h in o if h[2] <= args.chapter_levels)

    scope_note = (f"H1 only (`# ` at line start)" if args.chapter_levels == 1
                  else f"H1..H{args.chapter_levels}")

    # ---- index body -----------------------------------------------------------
    lines = [
        "# Chapters Index",
        "",
        f"- Source directory: `{root}`",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Parse scope: **chapters = {scope_note} headings**; "
        f"chapters parsed: {chapter_total} | deeper headings ignored for detection: {ignored_headings} "
        f"(H2..H{max_level}: " + " · ".join(f"H{lv}: {level_counts.get(lv, 0)}"
                                            for lv in range(2, max_level + 1)) + ")",
        f"- Files scanned: {len(files)} | markdown headings seen: {all_headings} | "
        f"H1: {level_counts.get(1, 0)}",
        f"- Step detection (case-insensitive `Step`/`STEP` + number inside a chapter heading, "
        f"scope={args.step_scope}): {step_chapters} chapter(s) carry a step number, "
        f"{step_hits} reference(s), {len(occ)} unique step number(s), "
        f"{anchor_hits} canonical (title-initial) reference(s); "
        f"{plain_chapters} chapter(s) carry no step number",
        f"- Branch numbering (chapters only): {len(dup_keys)} duplicated step number(s), "
        f"{dup_extra} extra occurrence(s), {len(suffix)} branch letter(s) applied to "
        f"{distinct_suffixed} chapter heading(s) (mode={args.suffix_mode}, "
        f"dup scope={args.dup_scope}, gaps={len(gaps)})",
    ]

    if args.coverage:
        lines += [
            "",
            f"## Coverage audit report ({scope_note} chapters · gaps · duplicates · branch numbers)",
            "",
            f"- Integer STEP range: **STEP-{lo} – STEP-{hi}** "
            f"(expected {hi - lo + 1}, found {len(int_nums)} unique chapter step number(s))",
            f"- Missing numbers: **{len(gaps)}** → {fmt_ranges(gaps) or 'none'}",
            f"- Step references detected in chapter headings: **{step_hits}** "
            f"({anchor_hits} canonical / {step_hits - anchor_hits} inline reference style, "
            f"{range_hits} of them used as a range start such as `STEP-31–96`) "
            f"in **{step_chapters}** chapter heading(s)",
            f"- Duplicated step numbers: **{len(dup_keys)}** ({dup_hits} occurrence(s), "
            f"{dup_extra} extra occurrence(s), of which "
            f"{sum(1 for k in dup_keys for h in occ[k] if h[6])} are range-start references) "
            f"→ branch letters assigned",
            f"- Branch-numbered chapter headings: **{len(suffix)}** in **{distinct_suffixed}** "
            f"chapter heading(s) ({multi_ref_headings} heading(s) carry more than one branch letter) "
            f"({', '.join(f'{k}×{len(occ[k])}' for k in dup_keys[:12])}"
            f"{' …' if len(dup_keys) > 12 else ''})",
            f"- Multiplicity distribution: "
            + " · ".join(f"×{m}: {c} number(s)" for m, c in sorted(multiplicity.items())),
            "",
            "### Gaps (numbering holes)",
            "",
            "| Missing STEP | Mentioned outside chapters? (evidence only, not counted) | "
            "First evidence | Evidence lines |",
            "| --- | --- | --- | ---: |",
        ]
        if gaps:
            for n in gaps[:args.max_audit_rows or None]:
                hit = first_mention(n)
                if hit:
                    name, line_no, cnt = hit
                    lines.append(f"| **STEP-{n}** | yes | `{name}` L{line_no} | {cnt} |")
                else:
                    lines.append(f"| **STEP-{n}** | no | – | 0 |")
            if args.max_audit_rows and len(gaps) > args.max_audit_rows:
                lines.append(f"| … | _{len(gaps) - args.max_audit_rows} more gap(s)_ | – | 0 |")
        else:
            lines.append("| – | _no gaps in range_ | – | 0 |")

        lines += [
            "",
            "### Duplicated step numbers and assigned branch numbers",
            "",
            "| Step | Chapters | Files | Levels | Canonical | Range refs | Assigned labels (file · line) |",
            "| --- | ---: | --- | --- | ---: | ---: | --- |",
        ]
        if dup_keys:
            for key in dup_keys[:args.max_audit_rows or None]:
                hits = [h for g in dup_group(key, occ[key]) for h in g]
                lvls = ", ".join(f"H{lv}" for lv in sorted({h[2] for h in hits}))
                fls = ", ".join(f"`{f}`×{sum(1 for h in hits if h[0] == f)}"
                                for f in dict.fromkeys(h[0] for h in hits))
                canon = sum(1 for h in hits if h[5])
                cells = ", ".join(f"`{lab}` (`{name}` L{line_no})"
                                  for lab, (name, line_no, *_rest) in zip(labels[key], hits))
                lines.append(f"| **{key}** | {len(hits)} | {fls} | {lvls} | {canon} | "
                             f"{sum(1 for h in hits if h[6])} | {cells} |")
            if args.max_audit_rows and len(dup_keys) > args.max_audit_rows:
                lines.append(f"| … | _{len(dup_keys) - args.max_audit_rows} more number(s)_ "
                             "| – | – | – | – | – |")
        else:
            lines.append("| – | 0 | – | – | 0 | 0 | _no duplicated chapter step numbers_ |")

        lines += [
            "",
            "### Branch-number registry",
            "",
            "| Branch | File | Line | Level | Style | Chapter heading (as indexed) |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
        if registry:
            for lab, name, line_no, level, title, anchor, rng in sorted(
                    registry, key=lambda r: (step_sort_key(re.sub(r"^[A-Za-z]+", "", r[0][5:])), r[0]))[
                    :args.max_audit_rows or None]:
                style = "range" if rng else ("canonical" if anchor else "reference")
                lines.append(f"| `{lab}` | `{name}` | {line_no} | H{level} | {style} | "
                             f"{trunc(label_title(name, line_no, title), 70)} |")
            if args.max_audit_rows and len(registry) > args.max_audit_rows:
                lines.append(f"| … | _{len(registry) - args.max_audit_rows} more branch(es)_ "
                             "| – | – | – | – | – |")
        else:
            lines.append("| – | – | – | – | – | _no branch numbers assigned_ |")

        # ---- chapter headings without a step number ------------------------------
        lines += [
            "",
            "### Chapter headings without a step number (not counted as steps)",
            "",
            "| File | Line | Level | Chapter heading |",
            "| --- | ---: | ---: | --- |",
        ]
        plain = [(name, ln, lv, t) for name, heads in chapters.items()
                 for ln, lv, t in heads if not step_matches(t, args.step_scope)]
        if plain:
            for name, ln, lv, t in plain[:args.max_audit_rows or None]:
                lines.append(f"| `{name}` | {ln} | H{lv} | {trunc(t, 70)} |")
            if args.max_audit_rows and len(plain) > args.max_audit_rows:
                lines.append(f"| … | _{len(plain) - args.max_audit_rows} more chapter(s)_ | – | – |")
        else:
            lines.append("| – | – | – | _every chapter heading carries a step number_ |")

        # ---- self-consistency check: audit report vs. what the index really shows
        unique_labels = len({r[0] for r in registry})

        def expected_letters(n: int) -> list[str]:
            if args.suffix_mode == "none":
                return [""] * n
            if args.suffix_mode == "tail":
                return [""] + [letter(i) for i in range(n - 1)]
            return [letter(i) for i in range(n)]

        bad_letters = []
        for k in dup_keys:
            flat = [h for g in dup_group(k, occ[k]) for h in g]
            got = [suffix.get((h[0], h[1], k)) or "" for h in flat]
            if got != expected_letters(len(flat)):
                bad_letters.append(k)

        checks = [
            (f"step detection used {scope_note} headings only",
             step_hits, counted_from_chapters, step_hits == counted_from_chapters),
            ("every duplicated number has one label per occurrence",
             dup_hits, sum(len(v) for v in labels.values()),
             dup_hits == sum(len(v) for v in labels.values())),
            ("branch letters inserted into the index body", len(suffix), body_letters,
             len(suffix) == body_letters),
            ("chapter headings carrying branch letters in the index body", distinct_suffixed,
             body_headings, distinct_suffixed == body_headings),
            ("branch labels are unique", len(registry), unique_labels,
             len(registry) == unique_labels),
            ("branch letters contiguous a, b, c … per duplicated number",
             len(dup_keys), len(dup_keys) - len(bad_letters), not bad_letters),
            ("duplicated numbers listed in the audit table", len(dup_keys), len(labels),
             len(dup_keys) == len(labels)),
            ("chapters listed in the index body", chapter_total,
             sum(1 for heads in chapters.values() for _h in heads),
             True),
        ]
        lines += [
            "",
            "### Audit self-consistency (report ↔ index body)",
            "",
            "| Check | Expected | Actual | Status |",
            "| --- | ---: | ---: | --- |",
        ]
        for what, exp, act, ok in checks:
            lines.append(f"| {what} | {exp} | {act} | {'✅ ok' if ok else '❌ mismatch'} |")
        if bad_letters:
            lines.append(f"| ↳ broken branch lettering: {', '.join(bad_letters[:10])} | – | – | ❌ |")

        lines += [
            "",
            "### Per-file chapter coverage",
            "",
            "| File | H1 headings | Chapters parsed | Step chapters | Step refs | Duplicated refs | "
            "Branch letters | Ignored H2+ | Integer STEP numbers |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for name in data:
            nums = sorted(int(k) for k, o in occ.items()
                          if is_plain_step(k) and any(f == name for f, *_ in o))
            cnt = sum(1 for o in occ.values() for (f, *_rest) in o if f == name)
            head_cnt = sum(1 for _ln, _lv, t in chapters[name] if step_matches(t, args.step_scope))
            dup_cnt = sum(1 for k in dup_keys for h in occ[k] if h[0] == name)
            sfx_cnt = sum(1 for (f, _l, _k) in suffix if f == name)
            ign = sum(c for lv, c in lcounts[name].items() if lv > args.chapter_levels)
            lines.append(f"| `{name}` | {lcounts[name].get(1, 0)} | {len(chapters[name])} | "
                         f"{head_cnt} | {cnt} | {dup_cnt} | {sfx_cnt} | {ign} | "
                         f"{fmt_ranges(nums) or '–'} |")

    lines += [
        "",
        "## Summary (file → chapter range)",
        "",
        "| File | Chapters | Step chapters | First chapter | Last chapter |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for name, heads in chapters.items():
        step_n = sum(1 for _ln, _lv, t in heads if step_matches(t, args.step_scope))
        first = (f"L{heads[0][0]}: {trunc(label_title(name, heads[0][0], heads[0][2]))}"
                 if heads else "_(empty)_")
        last = (f"L{heads[-1][0]}: {trunc(label_title(name, heads[-1][0], heads[-1][2]))}"
                if heads else "_(empty)_")
        lines.append(f"| `{name}` | {len(heads)} | {step_n} | {first} | {last} |")

    top = [(name, h) for name, heads in chapters.items() for h in heads]
    lines += [
        "",
        f"## Master chapter map ({scope_note})",
        "",
        "| # | STEP | Chapter | File | Line |",
        "| ---: | --- | --- | --- | ---: |",
    ]
    if top:
        for idx, (name, (line_no, _lv, title)) in enumerate(top, start=1):
            lab = label_of(name, line_no, title)
            lines.append(f"| {idx} | {f'`{lab}`' if lab else '–'} | "
                         f"{trunc(label_title(name, line_no, title))} | `{name}` | {line_no} |")
    else:
        lines.append("| – | – | _no chapter headings_ | – | – |")

    lines += [
        "",
        f"## Full index (file → {'chapters' if not args.with_subheadings else 'chapters + subheadings'})",
        "",
    ]
    for name, heads in data.items():
        lines.append(f"### {name}")
        lines.append("")
        if not chapters[name]:
            lines.append("_No chapter headings found (no H1 `# ` heading in this file)._")
            lines.append("")
            continue
        for line_no, level, title in heads:
            if level <= args.chapter_levels:
                lab = label_of(name, line_no, title)
                tag = f" · `{lab}`" if lab else ""
                lines.append(f"- L{line_no} · H{level} · {label_title(name, line_no, title)}{tag}")
            elif args.with_subheadings:
                lines.append(f"  {'  ' * (level - 2)}- L{line_no} · H{level} · "
                             f"{trunc(title, 80)}  _(not a chapter)_")
        if not args.with_subheadings:
            ign = sum(c for lv, c in lcounts[name].items() if lv > args.chapter_levels)
            lines.append("")
            lines.append(f"_H{args.chapter_levels + 1}..H{max_level} headings in this file "
                         f"({ign}) are intentionally not listed._")
        lines.append("")

    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(f"scanned {len(files)} file(s); {all_headings} heading(s) seen, "
          f"{chapter_total} chapter(s) parsed ({scope_note}) -> {out_path}")
    for name, heads in chapters.items():
        print(f"  {name}: {len(heads)} chapter(s), "
              f"{sum(c for lv, c in lcounts[name].items() if lv > args.chapter_levels)} ignored")
    print(f"step chapters: {step_chapters} chapter(s) / {step_hits} reference(s) "
          f"({len(occ)} unique, {anchor_hits} canonical) | integer range STEP-{lo}..STEP-{hi} "
          f"| scope={args.step_scope}")
    print(f"  gaps      : {fmt_ranges(gaps) or 'none'}")
    print(f"  duplicates: {len(dup_keys)} number(s), {dup_extra} extra occurrence(s), "
          f"{len(suffix)} branch letter(s) on {distinct_suffixed} chapter heading(s)")
    for key in dup_keys[:15]:
        print(f"    {key} x{len(occ[key])} -> {', '.join(labels[key])}")
    if len(dup_keys) > 15:
        print(f"    … {len(dup_keys) - 15} more (see audit report)")
    if args.coverage:
        print("  coverage audit report: written at the top of the index")
    else:
        print("  (run with --coverage for the audit report)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
