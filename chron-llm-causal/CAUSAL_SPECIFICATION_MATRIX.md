# Chron-LLM Causal Specification Matrix

- **Total Specifications**: 102
- **Total Domains**: 13 domains
- **Graph Integrity**: DAG Valid (0 Cycles)

## High Impact Core Specifications (Upstream Dependents)

| Evidence ID | Source Path | Impacted Count | Downstream Dependent IDs |
|---|---|---|---|
| `EVID-076` | `source/runtime/ir/ir.spec` | 3 | EVID-017, EVID-021, EVID-087 |
| `EVID-056` | `source/graph-runtime/ir/graph.spec` | 2 | EVID-049, EVID-050 |
| `EVID-050` | `source/experiments/ir/chron-llm-spec-v0.2.spec` | 1 | EVID-049 |
| `EVID-061` | `source/llama-agent/ir/chron-llm-runtime.spec` | 1 | EVID-021 |
| `EVID-063` | `source/llama-agent/ir/chron-llm.spec` | 1 | EVID-007 |

## Topological Execution Sequence

| Order | Evidence ID | Domain | Title | Version | Hard Deps |
|---|---|---|---|---|---|
| 1 | `EVID-001` | `bindings` | SECTION 1: CFFI TYPE MAPPING & OPAQUE HANDLES | v1.0.0 | - |
| 2 | `EVID-002` | `config` | SECTION 1: GLOBAL COMPILER OPTIMIZATION POLICIES | v1.0.0 | - |
| 3 | `EVID-003` | `contracts` | abi-registry.spec | v1.0.0 | - |
| 4 | `EVID-004` | `contracts` | base-excludes.spec | v1.0.0 | - |
| 5 | `EVID-005` | `contracts` | base-history.spec | v1.0.0 | - |
| 6 | `EVID-006` | `contracts` | base-invariants.spec | v1.0.0 | - |
| 7 | `EVID-007` | `contracts` | base-types.spec | v1.0.0 | EVID-063 |
| 8 | `EVID-008` | `contracts` | integration-verification.spec | v1.0.0 | - |
| 9 | `EVID-009` | `contracts` | kernel-world.spec | v1.0.0 | - |
| 10 | `EVID-010` | `contracts` | pipeline-orchestration.spec | v1.0.0 | - |
| 11 | `EVID-011` | `contracts` | v2.8.0-C-persistence.spec | v2.8.0 | - |
| 12 | `EVID-012` | `contracts` | v2.8.0-D-replay.spec | v2.8.0 | - |
| 13 | `EVID-013` | `contracts` | spec-metamodel.spec | v1.0.0 | - |
| 14 | `EVID-014` | `core` | SECTION 1: SYSTEM INVARIANTS & BASE TYPES | v1.0.0 | - |
| 15 | `EVID-015` | `docs` | 00-constitution.spec | v1.0.0 | - |
| 16 | `EVID-016` | `docs` | 01-domain-model.spec | v1.0.0 | - |
| 17 | `EVID-017` | `docs` | 02-operational-semantics.spec | v1.0.0 | EVID-076 |
| 18 | `EVID-018` | `docs` | SPEC RuntimeR1: REFERENCE_IMPL | v1.0.0 | - |
| 19 | `EVID-019` | `docs` | 05-validation-pipeline.spec | v1.0.0 | - |
| 20 | `EVID-020` | `docs` | 06-kernel-state-machine.spec | v1.0.0 | - |
| 21 | `EVID-021` | `docs` | 07-chron-mapping.spec | v1.0.0 | EVID-061, EVID-076 |
| 22 | `EVID-022` | `docs` | 08-memory-model.spec | v1.0.0 | - |
| 23 | `EVID-023` | `docs` | 09-runtime-scheduling.spec | v1.0.0 | - |
| 24 | `EVID-024` | `docs` | 10-tool-execution.spec | v1.0.0 | - |
| 25 | `EVID-025` | `docs` | 11-prompt-builder.spec | v1.0.0 | - |
| 26 | `EVID-026` | `docs` | SPEC: Chron-LLM-Recovery-R1 | v1.0.0 | - |
| 27 | `EVID-027` | `docs` | 13-worldline-branching.spec (Worldline Branching Contract) | v1.0.0 | - |
| 28 | `EVID-028` | `docs` | 99-open-questions.spec | v1.0.0 | - |
| 29 | `EVID-029` | `docs` | Chron-LLM_R2.0-A_Graph_Runtime_Core_Constitution_Spec.spec | v1.0.0 | - |
| 30 | `EVID-030` | `docs` | DOC_ID: CHRON-R2.0-B-WORLD-CONSTITUTION | v1.0.0 | - |
| 31 | `EVID-031` | `docs` | SPEC_ID=CHRON-R2.0-C-OBSERVABILITY-CONSTITUTION | v1.0.0 | - |
| 32 | `EVID-032` | `docs` | DOC: CHRON-R2.0-D-COMMIT-KERNEL-CONSTITUTION | v1.0.0 | - |
| 33 | `EVID-033` | `docs` | Architecture Specification v2.0 (Unified Core SOT) | v1.1. | - |
| 34 | `EVID-034` | `docs` | chron-llm-r1-interface-spec-v1.2.spec | v1.2. | - |
| 35 | `EVID-035` | `docs` | knowledge-system.spec | v1.0.0 | - |
| 36 | `EVID-036` | `docs` | phase-a-charter.spec | v1.0.0 | - |
| 37 | `EVID-037` | `docs` | phase-b-charter.spec | v1.0.0 | - |
| 38 | `EVID-038` | `docs` | phase-c-charter.spec | v1.0.0 | - |
| 39 | `EVID-039` | `docs` | phase-d-charter.spec | v1.0.0 | - |
| 40 | `EVID-040` | `docs` | phase-e-charter.spec | v1.0.0 | - |
| 41 | `EVID-041` | `docs` | phase-f-charter.spec | v1.0.0 | - |
| 42 | `EVID-042` | `docs` | pull_request_template.spec | v1.0.0 | - |
| 43 | `EVID-043` | `docs` | r2-0-c-freeze-report.spec | v1.0.0 | - |
| 44 | `EVID-044` | `docs` | knowledge-rationale.spec | v1.0.0 | - |
| 45 | `EVID-045` | `docs` | Chron-LLM_R2.1-D_Commit_Kernel_Freeze_Spec.spec | v1.0.0 | - |
| 46 | `EVID-046` | `docs` | Chron-LLM_R2.1-Kernel_Freeze_Spec.spec | v1.0.0 | - |
| 47 | `EVID-047` | `docs` | Chron-R2.0-World-Graph-Runtime-Specification-v1.0.spec | v1.0. | - |
| 48 | `EVID-048` | `docs` | R2.0-B_C_World_Runtime_Observation_Contract_v1.0.spec | v1.0. | - |
| 49 | `EVID-049` | `experiments` | 3cluster.spec | v1.0.0 | EVID-050 |
| 50 | `EVID-051` | `experiments` | cycle.spec | v1.0.0 | - |
| 51 | `EVID-052` | `experiments` | dynamics.spec | v1.0.0 | - |
| 52 | `EVID-053` | `experiments` | scc.spec | v1.0.0 | - |
| 53 | `EVID-054` | `graph-runtime` | SPEC causal-subgraph v1.0 | v1.0.0 | - |
| 54 | `EVID-055` | `graph-runtime` | chron-llm-r2-graph-runtime-causal-context-spec-v1.0.spec | v1.0.0 | - |
| 55 | `EVID-057` | `llama-agent` | causal-kernel.spec | v1.0.0 | - |
| 56 | `EVID-058` | `llama-agent` | chron-llm-graph.spec | v1.0.0 | - |
| 57 | `EVID-059` | `llama-agent` | chron-llm-immune.spec | v1.0.0 | - |
| 58 | `EVID-060` | `llama-agent` | chron-llm-kernel.spec | v1.0.0 | - |
| 59 | `EVID-062` | `llama-agent` | SPEC WorldService | v1.0.0 | - |
| 60 | `EVID-064` | `llama-agent` | delta3-agent.spec | v1.0.0 | - |
| 61 | `EVID-065` | `llama-agent` | MODULE ffi-bindings-mock.lisp : PhysicalLayerMock | v1.0.0 | - |
| 62 | `EVID-066` | `llama-agent` | ffi-bindings.spec | v1.0.0 | - |
| 63 | `EVID-067` | `llama-agent` | generate.spec | v1.0.0 | - |
| 64 | `EVID-068` | `llama-agent` | immune-system.spec | v1.0.0 | - |
| 65 | `EVID-069` | `llama-agent` | MODULE: llama-agent.lisp | v1.0.0 | - |
| 66 | `EVID-070` | `memory` | store.spec | v1.0.0 | - |
| 67 | `EVID-071` | `observability` | world-snapshot.spec | v1.0.0 | - |
| 68 | `EVID-072` | `runtime` | callback.spec | v1.0.0 | - |
| 69 | `EVID-073` | `runtime` | chron-llm-r1-ir-observation-layer-spec-v1.0.spec | v1.0.0 | - |
| 70 | `EVID-074` | `runtime` | MODULE ir-divergence : ObservationAnalysisLayer | STATUS Deprecated | v1.0.0 | - |
| 71 | `EVID-075` | `runtime` | ffi.spec | v1.0.0 | - |
| 72 | `EVID-077` | `runtime` | stream.spec | v1.0.0 | - |
| 73 | `EVID-078` | `runtime` | llama-engine.spec | v1.0.0 | - |
| 74 | `EVID-079` | `runtime` | CONTRACT(start-chat): | v1.0.0 | - |
| 75 | `EVID-080` | `runtime` | MODULE chronos-r0.chat | v1.0.0 | - |
| 76 | `EVID-081` | `runtime` | chron-llm-r0-session-execution-layer-spec-v1.0.spec | v1.0.0 | - |
| 77 | `EVID-082` | `runtime` | MODULE chronos-r0.history | v1.0.0 | - |
| 78 | `EVID-083` | `runtime` | llama-run.spec | v1.0.0 | - |
| 79 | `EVID-084` | `runtime` | prompt.spec | v1.0.0 | - |
| 80 | `EVID-085` | `runtime` | trace.spec | v1.0.0 | - |
| 81 | `EVID-086` | `runtime` | chron-llm-phase-e-ir-to-causal-dsl-transformation-contract-v1.0.spec | v1.0.0 | - |
| 82 | `EVID-087` | `runtime` | MODULE chronos-r1 | v1.0.0 | EVID-076 |
| 83 | `EVID-088` | `specs` | SPEC: 00-expression-grammar.spec | v1.0.0 | - |
| 84 | `EVID-089` | `specs` | MODULE MetaModel | v1.0.0 | - |
| 85 | `EVID-090` | `specs` | SPEC: 00-type-system.spec | v1.0.0 | - |
| 86 | `EVID-091` | `specs` | MODULE SemanticModel | v1.0.0 | - |
| 87 | `EVID-092` | `specs` | MODULE Constitution | v1.0.0 | - |
| 88 | `EVID-093` | `specs` | MODULE ChronSemanticExtension | v1.0.0 | - |
| 89 | `EVID-094` | `specs` | MODULE RuntimeModel | v1.0.0 | - |
| 90 | `EVID-095` | `tests` | phase0-big-bang-test.spec | v1.0.0 | - |
| 91 | `EVID-096` | `tests` | r2-0-a-tests.spec | v1.0.0 | - |
| 92 | `EVID-097` | `tests` | r2-0-b-tests.spec | v1.0.0 | - |
| 93 | `EVID-098` | `tests` | r2-0-c-tests.spec | v1.0.0 | - |
| 94 | `EVID-099` | `tests` | r2-1-b-tests.spec | v1.0.0 | - |
| 95 | `EVID-100` | `tests` | r2-2-e-tests.spec | v1.0.0 | - |
| 96 | `EVID-101` | `tests` | r2-3-s-tests.spec | v1.0.0 | - |
| 97 | `EVID-102` | `tests` | SECTION 1: MOCK CFFI INTERFACE & TEST SETUP | v1.0.0 | - |
| 98 | `EVID-063` | `llama-agent` | chron-llm.spec | v1.0.0 | - |
| 99 | `EVID-061` | `llama-agent` | MODULE: Chron-LLM/Runtime | v1.0.0 | - |
| 100 | `EVID-050` | `experiments` | chron-llm-spec-v0.2.spec | v0.2. | EVID-056 |
| 101 | `EVID-076` | `runtime` | ir.spec | v1.0.0 | - |
| 102 | `EVID-056` | `graph-runtime` | graph.spec | v1.0.0 | - |