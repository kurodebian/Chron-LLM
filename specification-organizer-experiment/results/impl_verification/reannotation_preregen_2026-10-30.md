# Re-annotation of pre-regen records (adjudicated 2026-10-30)

Adjudication (user, 2026-10-30): chapter identity going forward follows the LEDGER PIN range.
The 31 records below predate the regen. They are NOT rewritten; they are re-annotated as covering
pre-regen segments. Records from STEP-29 onward use ledger pin ranges.

Facts verified this turn:
- 3 different record shapes (key-sets) among the 31 records.
- 31/31 carry no recorded/live digest field: protocol step 5 provenance is unverifiable from the log itself.
- 20/31 logged ranges equal the ledger pin (and those digests reproduce from live bytes).
- 9 logged ranges are pre-regen groupings that do not match a pin; 1 is malformed (STEP-28 '5462-5064+').
- Pins are H1-aligned; the pre-regen index grouped multiple H1 chapters in the STEP-19..STEP-28 region.

| chapter | logged range | pin unit | pin range | range vs pin | digest from logged range |
| --- | --- | --- | --- | --- | --- |
| STEP-1a | 34-120 | mdsu0001 | 34-98 | not-pin | n/a (malformed) |
| STEP-1b | 99-120 | mdsu0002 | 99-120 | exact-pin | reproduces |
| STEP-2a | 121-142 | mdsu0003 | 121-142 | exact-pin | reproduces |
| STEP-2b | 143-161 | mdsu0004 | 143-161 | exact-pin | reproduces |
| STEP-3a | 162-183 | mdsu0005 | 162-183 | exact-pin | reproduces |
| STEP-3b | 184-235 | mdsu0006 | 184-235 | exact-pin | reproduces |
| STEP-4 | 236-862 | mdsu0007 | 236-862 | exact-pin | reproduces |
| STEP-5.8 | 863-998 | mdsu0008 | 863-998 | exact-pin | reproduces |
| STEP-6 | 999-1317 | mdsu0009 | 999-1317 | exact-pin | reproduces |
| STEP-7 | 1318-1390 | mdsu0010 | 1318-1390 | exact-pin | reproduces |
| STEP-8 | 1391-1531 | mdsu0011 | 1391-1531 | exact-pin | reproduces |
| STEP-9 | 1532-1647 | mdsu0012 | 1532-1647 | exact-pin | reproduces |
| STEP-10 | 1648-1808 | mdsu0013 | 1648-1808 | exact-pin | reproduces |
| STEP-11 | 1809-1913 | mdsu0014 | 1809-1913 | exact-pin | reproduces |
| STEP-12 | 1914-2020 | mdsu0015 | 1914-2020 | exact-pin | reproduces |
| STEP-13 | 2021-2124 | mdsu0016 | 2021-2124 | exact-pin | reproduces |
| STEP-14 | 2125-2282 | mdsu0017 | 2125-2282 | exact-pin | reproduces |
| STEP-15 | 2283-2430 | mdsu0018 | 2283-2430 | exact-pin | reproduces |
| STEP-16 | 2431-2553 | mdsu0019 | 2431-2553 | exact-pin | reproduces |
| STEP-17 | 2554-2701 | mdsu0020 | 2554-2701 | exact-pin | reproduces |
| STEP-18 | 2702-2872 | mdsu0021 | 2702-2872 | exact-pin | reproduces |
| STEP-19 | 2873-3404 | mdsu0022 | 2873-3052 | not-pin | n/a (malformed) |
| STEP-20 | 3405-3720 | mdsu0023 | 3053-3258 | not-pin | n/a (malformed) |
| STEP-21 | 3721-4054 | mdsu0024 | 3259-3479 | not-pin | n/a (malformed) |
| STEP-22 | 4055-4390 | mdsu0025 | 3480-3680 | not-pin | n/a (malformed) |
| STEP-23 | 4391-4641 | mdsu0026 | 3681-3872 | not-pin | n/a (malformed) |
| STEP-24 | 4642-4900 | mdsu0027 | 3873-4105 | not-pin | n/a (malformed) |
| STEP-25 | 4901-5064 | mdsu0028 | 4106-4314 | not-pin | n/a (malformed) |
| STEP-26 | 5065-5241 | mdsu0029 | 4315-4552 | not-pin | n/a (malformed) |
| STEP-27 | 5242-5461 | mdsu0030 | 4553-4774 | not-pin | n/a (malformed) |
| STEP-28 | 5462-5064+ | mdsu0031 | 4775-5064 | malformed | n/a |
