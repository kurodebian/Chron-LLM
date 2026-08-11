IMPORT ir::01-domain-model AS Schema
IMPORT runtime::r1::core AS Core

// ============================================================================
// Delta3 Kernel & Runtime Semantic Mapping Annotation
// File: docs/ir/07-chron-mapping.spec
// ============================================================================

// --- Core Entity & Type Mappings ---
@map Schema::Event               -> WAL_Entry
@map Schema::Candidate           -> proposalIR
@map Schema::ValidationReport    -> Δ0_Report
@map Schema::RuntimeRequest      -> Δ0_Request
@map Schema::KernelAction        -> KernelAction
@map Schema::RuntimeCommand      -> KernelCmd
@map Schema::Canonical           -> CanonicalState
@map Schema::Derived             -> Snapshot | Projection(CanonicalState)
@map Schema::Session             -> KernelState
@map Schema::Context             -> ReplayInput
@map Schema::FaultEvent          -> FaultEvent
@map Schema::External            -> ExtStore

// --- Runtime State Component Mappings ---
@map Core::KernelState.deferred  -> DeferredProposalQ[]
@map Core::KernelState.canonical -> Ref<CanonicalState>
@map Schema::Canonical.evidence  -> WAL[]
@map Schema::Canonical.mem-ref   -> RefStore
@map Schema::Canonical.config    -> RuntimeConfig

// --- Pipeline Operation Mappings ---
@map Core::validate              -> Δ0_Validator(proposalIR) -> Δ0_Report (det)
@map Core::policy-route          -> Δ0_Policy(Δ0_Report) -> Δ0_Request (det)
@map Core::kernel-transition     -> Runtime_Kernel(Δ0_Request) -> KernelCmd
@map Core::commit                -> op:mutate(CanonicalState)
@map Core::replay                -> replay(snapshot) -> ReplayInput (det)

// --- Architectural Invariant Annotations ---
INV: write(CanonicalState) == op:mutate(CanonicalState) // Commit is sole updater
INV: Replay(WAL[]) -> deterministic(ReplayInput)
INV: Projection(CanonicalState) ⊆ CanonicalState