# Chapters Index

- Source directory: `/home/junu/Chron-LLM/md_sheets`
- Generated: 2026-10-15 16:13:50
- Parse scope: **chapters = H1 only (`# ` at line start) headings**; chapters parsed: 127 | deeper headings ignored for detection: 4155 (H2..H3: H2: 1830 · H3: 2325)
- Files scanned: 3 | markdown headings seen: 4282 | H1: 127
- Step detection (case-insensitive `Step`/`STEP` + number inside a chapter heading, scope=contains): 127 chapter(s) carry a step number, 127 reference(s), 124 unique step number(s), 127 canonical (title-initial) reference(s); 0 chapter(s) carry no step number
- Branch numbering (chapters only): 3 duplicated step number(s), 3 extra occurrence(s), 6 branch letter(s) applied to 6 chapter heading(s) (mode=all, dup scope=global, gaps=1)

## Coverage audit report (H1 only (`# ` at line start) chapters · gaps · duplicates · branch numbers)

- Integer STEP range: **STEP-1 – STEP-124** (expected 124, found 123 unique chapter step number(s))
- Missing numbers: **1** → 5
- Step references detected in chapter headings: **127** (127 canonical / 0 inline reference style, 0 of them used as a range start such as `STEP-31–96`) in **127** chapter heading(s)
- Duplicated step numbers: **3** (6 occurrence(s), 3 extra occurrence(s), of which 0 are range-start references) → branch letters assigned
- Branch-numbered chapter headings: **6** in **6** chapter heading(s) (0 heading(s) carry more than one branch letter) (1×2, 2×2, 3×2)
- Multiplicity distribution: ×1: 121 number(s) · ×2: 3 number(s)

### Gaps (numbering holes)

| Missing STEP | Mentioned outside chapters? (evidence only, not counted) | First evidence | Evidence lines |
| --- | --- | --- | ---: |
| **STEP-5** | yes | `1-74.md` L287 | 3 |

### Duplicated step numbers and assigned branch numbers

| Step | Chapters | Files | Levels | Canonical | Range refs | Assigned labels (file · line) |
| --- | ---: | --- | --- | ---: | ---: | --- |
| **1** | 2 | `1-74.md`×2 | H1 | 2 | 0 | `STEP-1a` (`1-74.md` L34), `STEP-1b` (`1-74.md` L99) |
| **2** | 2 | `1-74.md`×2 | H1 | 2 | 0 | `STEP-2a` (`1-74.md` L121), `STEP-2b` (`1-74.md` L143) |
| **3** | 2 | `1-74.md`×2 | H1 | 2 | 0 | `STEP-3a` (`1-74.md` L162), `STEP-3b` (`1-74.md` L184) |

### Branch-number registry

| Branch | File | Line | Level | Style | Chapter heading (as indexed) |
| --- | --- | ---: | ---: | --- | --- |
| `STEP-1a` | `1-74.md` | 34 | H1 | canonical | Step 1a — 既存資産の所在と変更状態の確認 |
| `STEP-1b` | `1-74.md` | 99 | H1 | canonical | Step 1b — 現状確認結果 |
| `STEP-2a` | `1-74.md` | 121 | H1 | canonical | Step 2a — Contract の読み取り専用照合 |
| `STEP-2b` | `1-74.md` | 143 | H1 | canonical | Step 2b — Contract 照合の暫定裁定 |
| `STEP-3a` | `1-74.md` | 162 | H1 | canonical | Step 3a — Schema の読み取り専用照合 |
| `STEP-3b` | `1-74.md` | 184 | H1 | canonical | Step 3b — Contract / Schema 差分裁定 |

### Chapter headings without a step number (not counted as steps)

| File | Line | Level | Chapter heading |
| --- | ---: | ---: | --- |
| – | – | – | _every chapter heading carries a step number_ |

### Audit self-consistency (report ↔ index body)

| Check | Expected | Actual | Status |
| --- | ---: | ---: | --- |
| step detection used H1 only (`# ` at line start) headings only | 127 | 127 | ✅ ok |
| every duplicated number has one label per occurrence | 6 | 6 | ✅ ok |
| branch letters inserted into the index body | 6 | 6 | ✅ ok |
| chapter headings carrying branch letters in the index body | 6 | 6 | ✅ ok |
| branch labels are unique | 6 | 6 | ✅ ok |
| branch letters contiguous a, b, c … per duplicated number | 3 | 3 | ✅ ok |
| duplicated numbers listed in the audit table | 3 | 3 | ✅ ok |
| chapters listed in the index body | 127 | 127 | ✅ ok |

### Per-file chapter coverage

| File | H1 headings | Chapters parsed | Step chapters | Step refs | Duplicated refs | Branch letters | Ignored H2+ | Integer STEP numbers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `1-74.md` | 77 | 77 | 77 | 77 | 6 | 6 | 1480 | 1–4, 6–74 |
| `75-99.md` | 25 | 25 | 25 | 25 | 0 | 0 | 1360 | 75–99 |
| `100-124.md` | 25 | 25 | 25 | 25 | 0 | 0 | 1315 | 100–124 |

## Summary (file → chapter range)

| File | Chapters | Step chapters | First chapter | Last chapter |
| --- | ---: | ---: | --- | --- |
| `1-74.md` | 77 | 77 | L34: Step 1a — 既存資産の所在と変更状態の確認 | L32194: STEP-74 — Distributed Ordering / Causal Consistency / Partition Recovery and Reconciliati… |
| `75-99.md` | 25 | 25 | L1: STEP-75 — Distributed Membership / Failure Detection / Quorum / Fencing and Split-Brain P… | L26623: STEP-99 — Normative Compliance Assurance / Cross-Contract Conformance Audit / Adoption Re… |
| `100-124.md` | 25 | 25 | L1: STEP-100 — Normative Adoption Execution / Canonical Baseline Establishment / Post-Adoptio… | L20854: STEP-124 — Recovery Evidence Trust / External Execution Attestation / Reconciliation Auth… |

## Master chapter map (H1 only (`# ` at line start))

| # | STEP | Chapter | File | Line |
| ---: | --- | --- | --- | ---: |
| 1 | `STEP-1a` | Step 1a — 既存資産の所在と変更状態の確認 | `1-74.md` | 34 |
| 2 | `STEP-1b` | Step 1b — 現状確認結果 | `1-74.md` | 99 |
| 3 | `STEP-2a` | Step 2a — Contract の読み取り専用照合 | `1-74.md` | 121 |
| 4 | `STEP-2b` | Step 2b — Contract 照合の暫定裁定 | `1-74.md` | 143 |
| 5 | `STEP-3a` | Step 3a — Schema の読み取り専用照合 | `1-74.md` | 162 |
| 6 | `STEP-3b` | Step 3b — Contract / Schema 差分裁定 | `1-74.md` | 184 |
| 7 | `STEP-4` | Step 4 — テスト保証範囲の裁定 | `1-74.md` | 236 |
| 8 | `STEP-5.8` | Step 5.8 — Schema 許容値ギャップ一覧 | `1-74.md` | 863 |
| 9 | `STEP-6` | Step 6 — Design Note v0.2 構造化ドラフト案 | `1-74.md` | 999 |
| 10 | `STEP-7` | Step 7 — 変更候補の優先順位表（Design-Only） | `1-74.md` | 1318 |
| 11 | `STEP-8` | Step 8 — Local LLM Review Loop Specification | `1-74.md` | 1391 |
| 12 | `STEP-9` | Step 9 — Local LLM Review Loop の失敗モード分析（Design-Only） | `1-74.md` | 1532 |
| 13 | `STEP-10` | Step 10 — 決定的検証契約の設計（Design-Only） | `1-74.md` | 1648 |
| 14 | `STEP-11` | Step 11 — ループの受入基準と設計完了条件（Design-Only） | `1-74.md` | 1809 |
| 15 | `STEP-12` | Step 12 — 統合設計レビュー（Design-Only） | `1-74.md` | 1914 |
| 16 | `STEP-13` | Step 13 — 統合補正の規範化（Design-Only） | `1-74.md` | 2021 |
| 17 | `STEP-14` | Step 14 — 規範候補の競合・閉包検査（Design-Only） | `1-74.md` | 2125 |
| 18 | `STEP-15` | Step 15 — 補正候補の依存順序と裁定契約 | `1-74.md` | 2283 |
| 19 | `STEP-16` | Step 16 — 状態遷移表と失敗分類の形式化 | `1-74.md` | 2431 |
| 20 | `STEP-17` | Step 17 — 状態遷移の網羅性・到達可能性検査 | `1-74.md` | 2554 |
| 21 | `STEP-18` | Step 18 — 状態機械の正規モデルと機械検証契約 | `1-74.md` | 2702 |
| 22 | `STEP-19` | Step 19 — 正規モデルのシリアライズ契約とエラー体系 | `1-74.md` | 2873 |
| 23 | `STEP-20` | Step 20 — 正規モデルの意味論と競合解決規則 | `1-74.md` | 3053 |
| 24 | `STEP-21` | Step 21 — 不変条件の形式化と検証可能性 | `1-74.md` | 3259 |
| 25 | `STEP-22` | Step 22 — 時間的性質・履歴整合性・試行間不変条件 | `1-74.md` | 3480 |
| 26 | `STEP-23` | Step 23 — Commit・履歴追記の原子性と障害回復契約 | `1-74.md` | 3681 |
| 27 | `STEP-24` | Step 24 — WAL レコード形式・回復アルゴリズム・整合性証明 | `1-74.md` | 3873 |
| 28 | `STEP-25` | Step 25 — Canonical History のイベント契約と履歴再生意味論 | `1-74.md` | 4106 |
| 29 | `STEP-26` | Step 26 — Event Type Registry / State Transition Matrix / Normative Compatibility | `1-74.md` | 4315 |
| 30 | `STEP-27` | Step 27 — Canonical Serialization / Digest / Identity Contract | `1-74.md` | 4553 |
| 31 | `STEP-28` | Step 28 — Commit Authority / Authorization Policy Formalization | `1-74.md` | 4775 |
| 32 | `STEP-29` | Step 29 — Policy Versioning / Revocation / TOCTOU Contract | `1-74.md` | 5065 |
| 33 | `STEP-30` | Step 30 — Kernel Commit Linearization / Concurrency Control | `1-74.md` | 5314 |
| 34 | `STEP-31` | Step 31 — Failure Atomicity / Crash Consistency / Recovery Matrix | `1-74.md` | 5543 |
| 35 | `STEP-32` | Step 32 — Checkpoint / Snapshot / WAL Compaction Contract | `1-74.md` | 5772 |
| 36 | `STEP-33` | Step 33 — Retention / Auditability / Evidence Preservation Contract | `1-74.md` | 6032 |
| 37 | `STEP-34` | Step 34 — Backup / Restore / Disaster Recovery Contract | `1-74.md` | 6341 |
| 38 | `STEP-35` | Step 35 — Observability / Audit Logging / Operational Telemetry Contract | `1-74.md` | 6674 |
| 39 | `STEP-36` | Step 36 — Health / Liveness / Readiness / Safe Degradation Contract | `1-74.md` | 6993 |
| 40 | `STEP-37` | Step 37 — Configuration / Environment / Startup Validation Contract | `1-74.md` | 7264 |
| 41 | `STEP-38` | Step 38 — Shutdown / Restart / Graceful Termination Contract | `1-74.md` | 7748 |
| 42 | `STEP-39` | Step 39 — Concurrency / Serialization / Transaction Isolation Contract | `1-74.md` | 8339 |
| 43 | `STEP-40` | Step 40 — Event Ordering / Causality / Deterministic Replay Contract | `1-74.md` | 8894 |
| 44 | `STEP-41` | Step 41 — Schema Evolution / Version Compatibility / Migration Contract | `1-74.md` | 9459 |
| 45 | `STEP-42` | Step 42 — Security Boundary / Trust Model / Capability Authorization Contract | `1-74.md` | 9985 |
| 46 | `STEP-43` | Step 43 — Threat Modeling / Attack Surface / Security Invariant Verification Contract | `1-74.md` | 10671 |
| 47 | `STEP-44` | Step 44 — Security Incident / Detection / Containment / Evidence Preservation / Recovery… | `1-74.md` | 11199 |
| 48 | `STEP-45` | Step 45 — Security Governance / Risk Acceptance / Change Approval / Compliance Evidence C… | `1-74.md` | 11855 |
| 49 | `STEP-46` | Step 46 — Formal Contract Registry / Invariant Traceability / Cross-Contract Consistency… | `1-74.md` | 12450 |
| 50 | `STEP-47` | Step 47 — Normative Source of Truth / Contract Precedence / Conflict Adjudication Contract | `1-74.md` | 13080 |
| 51 | `STEP-48` | Step 48 — Normative Amendment / Deprecation / Supersession / Effective-Version Lifecycle… | `1-74.md` | 13619 |
| 52 | `STEP-49` | Step 49 — Normative Change Impact Analysis / Dependency Revalidation / Regression Evidenc… | `1-74.md` | 14214 |
| 53 | `STEP-50` | Step 50 — Contract Corpus Inventory / Baseline Manifest / Evidence-Bound Coverage Audit C… | `1-74.md` | 14831 |
| 54 | `STEP-51` | Step 51 — Semantic Corpus Classification / Normative Role Assignment / Evidence-Bound Cla… | `1-74.md` | 15499 |
| 55 | `STEP-52` | Step 52 — Semantic Claim Extraction / Claim-Evidence Separation / Unknown-Preserving Extr… | `1-74.md` | 16230 |
| 56 | `STEP-53` | Step 53 — Claim Relationship / Dependency / Causal Edge Proposal Contract | `1-74.md` | 17198 |
| 57 | `STEP-54` | Step 54 — Semantic Graph Validation / Invariant Checking / Contradiction and Closure Audi… | `1-74.md` | 17963 |
| 58 | `STEP-55` | Step 55 — Audit Finding Lifecycle / Remediation Proposal / Revalidation and Closure Contr… | `1-74.md` | 18940 |
| 59 | `STEP-56` | Step 56 — Audit Evidence Provenance / Reproducibility / Independent Verification Contract | `1-74.md` | 19815 |
| 60 | `STEP-57` | Step 57 — Evidence Trust / Authority Validation / Source Authenticity and Acceptance Cont… | `1-74.md` | 20410 |
| 61 | `STEP-58` | Step 58 — Evidence Registry / Trust Policy Versioning / Acceptance Decision Ledger Contra… | `1-74.md` | 21075 |
| 62 | `STEP-59` | Step 59 — Registry Integrity / Append-Only Guarantees / Tamper Evidence / Recovery Verifi… | `1-74.md` | 21816 |
| 63 | `STEP-60` | STEP-60 — Registry Recovery Acceptance / Operational Readiness / Service Resume Authoriza… | `1-74.md` | 22615 |
| 64 | `STEP-61` | STEP-61 — Operational Capability Matrix / Degraded Mode / Capability-Specific Authorizati… | `1-74.md` | 23316 |
| 65 | `STEP-62` | STEP-62 — Capability Registry / Operation Catalog / Policy Binding and Version Lifecycle… | `1-74.md` | 24006 |
| 66 | `STEP-63` | STEP-63 — Policy Conflict Resolution / Rule Precedence / Authorization Decision Determini… | `1-74.md` | 24775 |
| 67 | `STEP-64` | STEP-64 — Policy Evaluation Engine / Deterministic Decision Trace / Decision Replay Contr… | `1-74.md` | 25506 |
| 68 | `STEP-65` | STEP-65 — Authorization Decision Lifecycle / Revocation / Revalidation / In-Flight Operat… | `1-74.md` | 26127 |
| 69 | `STEP-66` | STEP-66 — Authorization Enforcement / Policy Decision Point / Policy Enforcement Point /… | `1-74.md` | 26718 |
| 70 | `STEP-67` | STEP-67 — Enforcement Failure Recovery / Partial Execution / Side-Effect Reconciliation C… | `1-74.md` | 27321 |
| 71 | `STEP-68` | STEP-68 — Recovery Evidence Closure / Residual Risk Acceptance / Operational Resume Gate… | `1-74.md` | 27974 |
| 72 | `STEP-69` | STEP-69 — Post-Recovery Monitoring / Stability Window / Automatic Degradation and Re-Entr… | `1-74.md` | 28661 |
| 73 | `STEP-70` | STEP-70 — Operational Stability Certification / Post-Recovery Audit Closure / Lifecycle T… | `1-74.md` | 29423 |
| 74 | `STEP-71` | STEP-71 — Lifecycle State Registry / Transition Graph Integrity / Reachability and Dead-E… | `1-74.md` | 29972 |
| 75 | `STEP-72` | STEP-72 — Lifecycle Transition Concurrency / Competing Requests / Stale-State and Atomic… | `1-74.md` | 30746 |
| 76 | `STEP-73` | STEP-73 — Distributed Commit Protocol / Transaction Boundary / Outbox-Inbox and Reconcili… | `1-74.md` | 31525 |
| 77 | `STEP-74` | STEP-74 — Distributed Ordering / Causal Consistency / Partition Recovery and Reconciliati… | `1-74.md` | 32194 |
| 78 | `STEP-75` | STEP-75 — Distributed Membership / Failure Detection / Quorum / Fencing and Split-Brain P… | `75-99.md` | 1 |
| 79 | `STEP-76` | STEP-76 — Distributed Durability / Replication / Commit Acknowledgment and Recovery Consi… | `75-99.md` | 1004 |
| 80 | `STEP-77` | STEP-77 — Distributed Read Consistency / Snapshot Isolation / Stale Read Detection and Re… | `75-99.md` | 1970 |
| 81 | `STEP-78` | STEP-78 — Distributed Query / Multi-Source Read Composition / Cross-Source Consistency an… | `75-99.md` | 2753 |
| 82 | `STEP-79` | STEP-79 — Distributed Result Validation / Semantic Integrity / Contradiction Detection an… | `75-99.md` | 3762 |
| 83 | `STEP-80` | STEP-80 — Validation Decision Ledger / Acceptance Evidence / Decision Replay and Auditabi… | `75-99.md` | 4933 |
| 84 | `STEP-81` | STEP-81 — Decision Lifecycle Governance / Revocation Propagation / Downstream Invalidatio… | `75-99.md` | 6042 |
| 85 | `STEP-82` | STEP-82 — Decision Dependency Registry / Versioned Dependency Evidence / Completeness Cer… | `75-99.md` | 7291 |
| 86 | `STEP-83` | STEP-83 — Dependency Change Impact Analysis / Transitive Revalidation / Certification Rev… | `75-99.md` | 8231 |
| 87 | `STEP-84` | STEP-84 — Dependency Impact Policy Registry / Risk-Based Revalidation Priority / Mandator… | `75-99.md` | 9369 |
| 88 | `STEP-85` | STEP-85 — Policy Decision Enforcement / Mandatory Action Completion / Enforcement Evidenc… | `75-99.md` | 10401 |
| 89 | `STEP-86` | STEP-86 — Enforcement Completion Ledger / Cross-Target Consistency / Residual Action Clos… | `75-99.md` | 11248 |
| 90 | `STEP-87` | STEP-87 — Completion Certification Validity / Post-Completion Change Detection / Automati… | `75-99.md` | 12189 |
| 91 | `STEP-88` | STEP-88 — Certificate Revocation Propagation / Dependent Authorization Revalidation / Ope… | `75-99.md` | 12551 |
| 92 | `STEP-89` | STEP-89 — Distributed Revocation Convergence / Stale Authority Detection / Global Consist… | `75-99.md` | 13596 |
| 93 | `STEP-90` | STEP-90 — Operational Resume Authorization / Convergence Evidence Validation / Safe Re-En… | `75-99.md` | 14547 |
| 94 | `STEP-91` | STEP-91 — Post-Resume Stability Certification / Runtime Drift Detection / Automatic Safe-… | `75-99.md` | 15574 |
| 95 | `STEP-92` | STEP-92 — Safe-State Reversion Completion Ledger / Residual Risk Reconciliation / Post-Re… | `75-99.md` | 16972 |
| 96 | `STEP-93` | STEP-93 — Recovery Readiness Certification / Resume Authorization Revalidation / Controll… | `75-99.md` | 18402 |
| 97 | `STEP-94` | STEP-94 — Controlled Re-Entry Execution Ledger / Stage Transition Verification / Post-Res… | `75-99.md` | 19685 |
| 98 | `STEP-95` | STEP-95 — Re-Entry Completion Certification / Stability Evidence Closure / Operational Li… | `75-99.md` | 21223 |
| 99 | `STEP-96` | STEP-96 — Operational Lifecycle State Certification / Post-Handoff Invalidation Propagati… | `75-99.md` | 22539 |
| 100 | `STEP-97` | STEP-97 — Continuous Compliance Evaluation / Policy Drift Revalidation / Operational Conf… | `75-99.md` | 23529 |
| 101 | `STEP-98` | STEP-98 — Compliance Decision Governance / Nonconformance Risk Acceptance / Corrective Ac… | `75-99.md` | 24855 |
| 102 | `STEP-99` | STEP-99 — Normative Compliance Assurance / Cross-Contract Conformance Audit / Adoption Re… | `75-99.md` | 26623 |
| 103 | `STEP-100` | STEP-100 — Normative Adoption Execution / Canonical Baseline Establishment / Post-Adoptio… | `100-124.md` | 1 |
| 104 | `STEP-101` | STEP-101 — Canonical Baseline Governance / Normative Change Control / Version Transition… | `100-124.md` | 1100 |
| 105 | `STEP-102` | STEP-102 — Normative Change Deployment / Migration Execution / Cross-Version Runtime Conf… | `100-124.md` | 2372 |
| 106 | `STEP-103` | STEP-103 — Migration Outcome Reconciliation / Canonical State Recovery / Post-Migration I… | `100-124.md` | 3298 |
| 107 | `STEP-104` | STEP-104 — Operational Re-Entry Execution / Runtime Capability Revalidation / Stability M… | `100-124.md` | 4319 |
| 108 | `STEP-105` | STEP-105 — Operational Stability Certification / Lifecycle Closure / Cross-Contract Final… | `100-124.md` | 5080 |
| 109 | `STEP-106` | STEP-106 — Normative Corpus Inventory Execution / Contract Identity Resolution / Cross-Co… | `100-124.md` | 5776 |
| 110 | `STEP-107` | STEP-107 — Cross-Contract Finding Adjudication / Remediation Prioritization / Audit Closu… | `100-124.md` | 6525 |
| 111 | `STEP-108` | STEP-108 — Audit Contract Consolidation / Normative Gap Review / Execution Readiness Gate | `100-124.md` | 7156 |
| 112 | `STEP-109` | STEP-109 — Read-Only Corpus Audit Runbook / Deterministic Inventory Execution / Audit Evi… | `100-124.md` | 7659 |
| 113 | `STEP-110` | STEP-110 — Audit Output Schema / Manifest Validation / Cross-Artifact Integrity Contract | `100-124.md` | 8437 |
| 114 | `STEP-111` | STEP-111 — Validator Conformance / Negative-Test Coverage / Deterministic Failure Classif… | `100-124.md` | 9280 |
| 115 | `STEP-112` | STEP-112 — Audit Test Fixture Registry / Golden Oracle Governance / Regression Evidence C… | `100-124.md` | 9936 |
| 116 | `STEP-113` | STEP-113 — Test Coverage Traceability / Requirement-to-Test Closure / Coverage Claim Cert… | `100-124.md` | 10704 |
| 117 | `STEP-114` | STEP-114 — Coverage Policy Registry / Threshold Governance / Exception Authorization Cont… | `100-124.md` | 11500 |
| 118 | `STEP-115` | STEP-115 — Coverage Certification Lifecycle / Certificate Revocation / Downstream Accepta… | `100-124.md` | 12260 |
| 119 | `STEP-116` | STEP-116 — Certificate Registry Integrity / Revocation Ledger / Consumer Acknowledgment R… | `100-124.md` | 13182 |
| 120 | `STEP-117` | STEP-117 — Revocation Propagation Certification / Consumer Convergence / Residual Inconsi… | `100-124.md` | 13932 |
| 121 | `STEP-118` | STEP-118 — Convergence Certificate Registry / Consumer Acceptance Ledger / Post-Certifica… | `100-124.md` | 14952 |
| 122 | `STEP-119` | STEP-119 — Certificate Trust Continuity / Consumer Authorization Revalidation / Post-Revo… | `100-124.md` | 15845 |
| 123 | `STEP-120` | STEP-120 — Authorization Enforcement Coverage / Revocation-to-Operation Traceability / Pr… | `100-124.md` | 16710 |
| 124 | `STEP-121` | STEP-121 — Prevention Assurance Consumption / Downstream Authorization Binding / Certific… | `100-124.md` | 18291 |
| 125 | `STEP-122` | STEP-122 — Authorization Decision Lifecycle / Permit Lease / Execution-Boundary Revalidat… | `100-124.md` | 19267 |
| 126 | `STEP-123` | STEP-123 — Authorization Lifecycle Recovery / Lease Consumption Reconciliation / Duplicat… | `100-124.md` | 20165 |
| 127 | `STEP-124` | STEP-124 — Recovery Evidence Trust / External Execution Attestation / Reconciliation Auth… | `100-124.md` | 20854 |

## Full index (file → chapters)

### 1-74.md

- L34 · H1 · Step 1a — 既存資産の所在と変更状態の確認 · `STEP-1a`
- L99 · H1 · Step 1b — 現状確認結果 · `STEP-1b`
- L121 · H1 · Step 2a — Contract の読み取り専用照合 · `STEP-2a`
- L143 · H1 · Step 2b — Contract 照合の暫定裁定 · `STEP-2b`
- L162 · H1 · Step 3a — Schema の読み取り専用照合 · `STEP-3a`
- L184 · H1 · Step 3b — Contract / Schema 差分裁定 · `STEP-3b`
- L236 · H1 · Step 4 — テスト保証範囲の裁定 · `STEP-4`
- L863 · H1 · Step 5.8 — Schema 許容値ギャップ一覧 · `STEP-5.8`
- L999 · H1 · Step 6 — Design Note v0.2 構造化ドラフト案 · `STEP-6`
- L1318 · H1 · Step 7 — 変更候補の優先順位表（Design-Only） · `STEP-7`
- L1391 · H1 · Step 8 — Local LLM Review Loop Specification · `STEP-8`
- L1532 · H1 · Step 9 — Local LLM Review Loop の失敗モード分析（Design-Only） · `STEP-9`
- L1648 · H1 · Step 10 — 決定的検証契約の設計（Design-Only） · `STEP-10`
- L1809 · H1 · Step 11 — ループの受入基準と設計完了条件（Design-Only） · `STEP-11`
- L1914 · H1 · Step 12 — 統合設計レビュー（Design-Only） · `STEP-12`
- L2021 · H1 · Step 13 — 統合補正の規範化（Design-Only） · `STEP-13`
- L2125 · H1 · Step 14 — 規範候補の競合・閉包検査（Design-Only） · `STEP-14`
- L2283 · H1 · Step 15 — 補正候補の依存順序と裁定契約 · `STEP-15`
- L2431 · H1 · Step 16 — 状態遷移表と失敗分類の形式化 · `STEP-16`
- L2554 · H1 · Step 17 — 状態遷移の網羅性・到達可能性検査 · `STEP-17`
- L2702 · H1 · Step 18 — 状態機械の正規モデルと機械検証契約 · `STEP-18`
- L2873 · H1 · Step 19 — 正規モデルのシリアライズ契約とエラー体系 · `STEP-19`
- L3053 · H1 · Step 20 — 正規モデルの意味論と競合解決規則 · `STEP-20`
- L3259 · H1 · Step 21 — 不変条件の形式化と検証可能性 · `STEP-21`
- L3480 · H1 · Step 22 — 時間的性質・履歴整合性・試行間不変条件 · `STEP-22`
- L3681 · H1 · Step 23 — Commit・履歴追記の原子性と障害回復契約 · `STEP-23`
- L3873 · H1 · Step 24 — WAL レコード形式・回復アルゴリズム・整合性証明 · `STEP-24`
- L4106 · H1 · Step 25 — Canonical History のイベント契約と履歴再生意味論 · `STEP-25`
- L4315 · H1 · Step 26 — Event Type Registry / State Transition Matrix / Normative Compatibility · `STEP-26`
- L4553 · H1 · Step 27 — Canonical Serialization / Digest / Identity Contract · `STEP-27`
- L4775 · H1 · Step 28 — Commit Authority / Authorization Policy Formalization · `STEP-28`
- L5065 · H1 · Step 29 — Policy Versioning / Revocation / TOCTOU Contract · `STEP-29`
- L5314 · H1 · Step 30 — Kernel Commit Linearization / Concurrency Control · `STEP-30`
- L5543 · H1 · Step 31 — Failure Atomicity / Crash Consistency / Recovery Matrix · `STEP-31`
- L5772 · H1 · Step 32 — Checkpoint / Snapshot / WAL Compaction Contract · `STEP-32`
- L6032 · H1 · Step 33 — Retention / Auditability / Evidence Preservation Contract · `STEP-33`
- L6341 · H1 · Step 34 — Backup / Restore / Disaster Recovery Contract · `STEP-34`
- L6674 · H1 · Step 35 — Observability / Audit Logging / Operational Telemetry Contract · `STEP-35`
- L6993 · H1 · Step 36 — Health / Liveness / Readiness / Safe Degradation Contract · `STEP-36`
- L7264 · H1 · Step 37 — Configuration / Environment / Startup Validation Contract · `STEP-37`
- L7748 · H1 · Step 38 — Shutdown / Restart / Graceful Termination Contract · `STEP-38`
- L8339 · H1 · Step 39 — Concurrency / Serialization / Transaction Isolation Contract · `STEP-39`
- L8894 · H1 · Step 40 — Event Ordering / Causality / Deterministic Replay Contract · `STEP-40`
- L9459 · H1 · Step 41 — Schema Evolution / Version Compatibility / Migration Contract · `STEP-41`
- L9985 · H1 · Step 42 — Security Boundary / Trust Model / Capability Authorization Contract · `STEP-42`
- L10671 · H1 · Step 43 — Threat Modeling / Attack Surface / Security Invariant Verification Contract · `STEP-43`
- L11199 · H1 · Step 44 — Security Incident / Detection / Containment / Evidence Preservation / Recovery Contract · `STEP-44`
- L11855 · H1 · Step 45 — Security Governance / Risk Acceptance / Change Approval / Compliance Evidence Contract · `STEP-45`
- L12450 · H1 · Step 46 — Formal Contract Registry / Invariant Traceability / Cross-Contract Consistency Audit · `STEP-46`
- L13080 · H1 · Step 47 — Normative Source of Truth / Contract Precedence / Conflict Adjudication Contract · `STEP-47`
- L13619 · H1 · Step 48 — Normative Amendment / Deprecation / Supersession / Effective-Version Lifecycle Contract · `STEP-48`
- L14214 · H1 · Step 49 — Normative Change Impact Analysis / Dependency Revalidation / Regression Evidence Contract · `STEP-49`
- L14831 · H1 · Step 50 — Contract Corpus Inventory / Baseline Manifest / Evidence-Bound Coverage Audit Contract · `STEP-50`
- L15499 · H1 · Step 51 — Semantic Corpus Classification / Normative Role Assignment / Evidence-Bound Classification Contract · `STEP-51`
- L16230 · H1 · Step 52 — Semantic Claim Extraction / Claim-Evidence Separation / Unknown-Preserving Extraction Contract · `STEP-52`
- L17198 · H1 · Step 53 — Claim Relationship / Dependency / Causal Edge Proposal Contract · `STEP-53`
- L17963 · H1 · Step 54 — Semantic Graph Validation / Invariant Checking / Contradiction and Closure Audit Contract · `STEP-54`
- L18940 · H1 · Step 55 — Audit Finding Lifecycle / Remediation Proposal / Revalidation and Closure Contract · `STEP-55`
- L19815 · H1 · Step 56 — Audit Evidence Provenance / Reproducibility / Independent Verification Contract · `STEP-56`
- L20410 · H1 · Step 57 — Evidence Trust / Authority Validation / Source Authenticity and Acceptance Contract · `STEP-57`
- L21075 · H1 · Step 58 — Evidence Registry / Trust Policy Versioning / Acceptance Decision Ledger Contract · `STEP-58`
- L21816 · H1 · Step 59 — Registry Integrity / Append-Only Guarantees / Tamper Evidence / Recovery Verification Contract · `STEP-59`
- L22615 · H1 · STEP-60 — Registry Recovery Acceptance / Operational Readiness / Service Resume Authorization Contract · `STEP-60`
- L23316 · H1 · STEP-61 — Operational Capability Matrix / Degraded Mode / Capability-Specific Authorization Contract · `STEP-61`
- L24006 · H1 · STEP-62 — Capability Registry / Operation Catalog / Policy Binding and Version Lifecycle Contract · `STEP-62`
- L24775 · H1 · STEP-63 — Policy Conflict Resolution / Rule Precedence / Authorization Decision Determinism Contract · `STEP-63`
- L25506 · H1 · STEP-64 — Policy Evaluation Engine / Deterministic Decision Trace / Decision Replay Contract · `STEP-64`
- L26127 · H1 · STEP-65 — Authorization Decision Lifecycle / Revocation / Revalidation / In-Flight Operation Control Contract · `STEP-65`
- L26718 · H1 · STEP-66 — Authorization Enforcement / Policy Decision Point / Policy Enforcement Point / Fail-Safe Integration Contract · `STEP-66`
- L27321 · H1 · STEP-67 — Enforcement Failure Recovery / Partial Execution / Side-Effect Reconciliation Contract · `STEP-67`
- L27974 · H1 · STEP-68 — Recovery Evidence Closure / Residual Risk Acceptance / Operational Resume Gate Contract · `STEP-68`
- L28661 · H1 · STEP-69 — Post-Recovery Monitoring / Stability Window / Automatic Degradation and Re-Entry Gate Contract · `STEP-69`
- L29423 · H1 · STEP-70 — Operational Stability Certification / Post-Recovery Audit Closure / Lifecycle Transition Authorization Contract · `STEP-70`
- L29972 · H1 · STEP-71 — Lifecycle State Registry / Transition Graph Integrity / Reachability and Dead-End Audit Contract · `STEP-71`
- L30746 · H1 · STEP-72 — Lifecycle Transition Concurrency / Competing Requests / Stale-State and Atomic Commit Contract · `STEP-72`
- L31525 · H1 · STEP-73 — Distributed Commit Protocol / Transaction Boundary / Outbox-Inbox and Reconciliation Contract · `STEP-73`
- L32194 · H1 · STEP-74 — Distributed Ordering / Causal Consistency / Partition Recovery and Reconciliation Contract · `STEP-74`

_H2..H3 headings in this file (1480) are intentionally not listed._

### 75-99.md

- L1 · H1 · STEP-75 — Distributed Membership / Failure Detection / Quorum / Fencing and Split-Brain Prevention Contract · `STEP-75`
- L1004 · H1 · STEP-76 — Distributed Durability / Replication / Commit Acknowledgment and Recovery Consistency Contract · `STEP-76`
- L1970 · H1 · STEP-77 — Distributed Read Consistency / Snapshot Isolation / Stale Read Detection and Read Authority Contract · `STEP-77`
- L2753 · H1 · STEP-78 — Distributed Query / Multi-Source Read Composition / Cross-Source Consistency and Result Provenance Contract · `STEP-78`
- L3762 · H1 · STEP-79 — Distributed Result Validation / Semantic Integrity / Contradiction Detection and Acceptance Gate Contract · `STEP-79`
- L4933 · H1 · STEP-80 — Validation Decision Ledger / Acceptance Evidence / Decision Replay and Auditability Contract · `STEP-80`
- L6042 · H1 · STEP-81 — Decision Lifecycle Governance / Revocation Propagation / Downstream Invalidation and Reauthorization Contract · `STEP-81`
- L7291 · H1 · STEP-82 — Decision Dependency Registry / Versioned Dependency Evidence / Completeness Certification Contract · `STEP-82`
- L8231 · H1 · STEP-83 — Dependency Change Impact Analysis / Transitive Revalidation / Certification Revocation Contract · `STEP-83`
- L9369 · H1 · STEP-84 — Dependency Impact Policy Registry / Risk-Based Revalidation Priority / Mandatory Invalidation Rules Contract · `STEP-84`
- L10401 · H1 · STEP-85 — Policy Decision Enforcement / Mandatory Action Completion / Enforcement Evidence Reconciliation Contract · `STEP-85`
- L11248 · H1 · STEP-86 — Enforcement Completion Ledger / Cross-Target Consistency / Residual Action Closure Contract · `STEP-86`
- L12189 · H1 · STEP-87 — Completion Certification Validity / Post-Completion Change Detection / Automatic Reopening Contract · `STEP-87`
- L12551 · H1 · STEP-88 — Certificate Revocation Propagation / Dependent Authorization Revalidation / Operational Gate Consistency Contract · `STEP-88`
- L13596 · H1 · STEP-89 — Distributed Revocation Convergence / Stale Authority Detection / Global Consistency Certification Contract · `STEP-89`
- L14547 · H1 · STEP-90 — Operational Resume Authorization / Convergence Evidence Validation / Safe Re-Entry Gate Contract · `STEP-90`
- L15574 · H1 · STEP-91 — Post-Resume Stability Certification / Runtime Drift Detection / Automatic Safe-State Reversion Contract · `STEP-91`
- L16972 · H1 · STEP-92 — Safe-State Reversion Completion Ledger / Residual Risk Reconciliation / Post-Reversion Recovery Authorization Contract · `STEP-92`
- L18402 · H1 · STEP-93 — Recovery Readiness Certification / Resume Authorization Revalidation / Controlled Re-Entry Evidence Contract · `STEP-93`
- L19685 · H1 · STEP-94 — Controlled Re-Entry Execution Ledger / Stage Transition Verification / Post-Resume Stability Gate Contract · `STEP-94`
- L21223 · H1 · STEP-95 — Re-Entry Completion Certification / Stability Evidence Closure / Operational Lifecycle Handoff Contract · `STEP-95`
- L22539 · H1 · STEP-96 — Operational Lifecycle State Certification / Post-Handoff Invalidation Propagation / Steady-State Governance Contract · `STEP-96`
- L23529 · H1 · STEP-97 — Continuous Compliance Evaluation / Policy Drift Revalidation / Operational Conformance Evidence Contract · `STEP-97`
- L24855 · H1 · STEP-98 — Compliance Decision Governance / Nonconformance Risk Acceptance / Corrective Action Closure Certification Contract · `STEP-98`
- L26623 · H1 · STEP-99 — Normative Compliance Assurance / Cross-Contract Conformance Audit / Adoption Readiness Certification Contract · `STEP-99`

_H2..H3 headings in this file (1360) are intentionally not listed._

### 100-124.md

- L1 · H1 · STEP-100 — Normative Adoption Execution / Canonical Baseline Establishment / Post-Adoption Integrity Verification Contract · `STEP-100`
- L1100 · H1 · STEP-101 — Canonical Baseline Governance / Normative Change Control / Version Transition and Compatibility Verification Contract · `STEP-101`
- L2372 · H1 · STEP-102 — Normative Change Deployment / Migration Execution / Cross-Version Runtime Conformance and Rollback Safety Contract · `STEP-102`
- L3298 · H1 · STEP-103 — Migration Outcome Reconciliation / Canonical State Recovery / Post-Migration Integrity and Operational Re-Entry Authorization Contract · `STEP-103`
- L4319 · H1 · STEP-104 — Operational Re-Entry Execution / Runtime Capability Revalidation / Stability Monitoring and Automatic Safe-State Transition Contract · `STEP-104`
- L5080 · H1 · STEP-105 — Operational Stability Certification / Lifecycle Closure / Cross-Contract Finalization and Freeze Readiness Audit Contract · `STEP-105`
- L5776 · H1 · STEP-106 — Normative Corpus Inventory Execution / Contract Identity Resolution / Cross-Contract Audit Orchestration Contract · `STEP-106`
- L6525 · H1 · STEP-107 — Cross-Contract Finding Adjudication / Remediation Prioritization / Audit Closure Decision Contract · `STEP-107`
- L7156 · H1 · STEP-108 — Audit Contract Consolidation / Normative Gap Review / Execution Readiness Gate · `STEP-108`
- L7659 · H1 · STEP-109 — Read-Only Corpus Audit Runbook / Deterministic Inventory Execution / Audit Evidence Capture Contract · `STEP-109`
- L8437 · H1 · STEP-110 — Audit Output Schema / Manifest Validation / Cross-Artifact Integrity Contract · `STEP-110`
- L9280 · H1 · STEP-111 — Validator Conformance / Negative-Test Coverage / Deterministic Failure Classification Contract · `STEP-111`
- L9936 · H1 · STEP-112 — Audit Test Fixture Registry / Golden Oracle Governance / Regression Evidence Contract · `STEP-112`
- L10704 · H1 · STEP-113 — Test Coverage Traceability / Requirement-to-Test Closure / Coverage Claim Certification Contract · `STEP-113`
- L11500 · H1 · STEP-114 — Coverage Policy Registry / Threshold Governance / Exception Authorization Contract · `STEP-114`
- L12260 · H1 · STEP-115 — Coverage Certification Lifecycle / Certificate Revocation / Downstream Acceptance Invalidation Contract · `STEP-115`
- L13182 · H1 · STEP-116 — Certificate Registry Integrity / Revocation Ledger / Consumer Acknowledgment Reconciliation Contract · `STEP-116`
- L13932 · H1 · STEP-117 — Revocation Propagation Certification / Consumer Convergence / Residual Inconsistency Closure Contract · `STEP-117`
- L14952 · H1 · STEP-118 — Convergence Certificate Registry / Consumer Acceptance Ledger / Post-Certification Drift Reconciliation Contract · `STEP-118`
- L15845 · H1 · STEP-119 — Certificate Trust Continuity / Consumer Authorization Revalidation / Post-Revocation Use Prevention Contract · `STEP-119`
- L16710 · H1 · STEP-120 — Authorization Enforcement Coverage / Revocation-to-Operation Traceability / Prevention Assurance Certification Contract · `STEP-120`
- L18291 · H1 · STEP-121 — Prevention Assurance Consumption / Downstream Authorization Binding / Certification-Scope Enforcement Contract · `STEP-121`
- L19267 · H1 · STEP-122 — Authorization Decision Lifecycle / Permit Lease / Execution-Boundary Revalidation and Revocation Race Control Contract · `STEP-122`
- L20165 · H1 · STEP-123 — Authorization Lifecycle Recovery / Lease Consumption Reconciliation / Duplicate Execution Prevention Contract · `STEP-123`
- L20854 · H1 · STEP-124 — Recovery Evidence Trust / External Execution Attestation / Reconciliation Authority Contract · `STEP-124`

_H2..H3 headings in this file (1315) are intentionally not listed._
