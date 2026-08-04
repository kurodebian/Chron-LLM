TYPES
Event = FeedbackIntent | CorrectionIntent | CorrectionCandidate | VALIDATED_CORRECTION_FACT | COMMIT_CORRECTION | ReindexEvent | BulkReindexEvent | DISCARD_STALE_CONTEXT
Op = :REWRITE | :INSERT-AFTER | :DEPRECATE | :ATTACH-GUARD
State = IDLE | PREPARING_CORRECTION | APPLYING_CORRECTION | ABORTING_CORRECTION
CorrectionNode = { :id: UUID, :target: Ref, :op: Op, :ast-delta: { :before-hash: SHA256, :after-ast: SExpr }, :bindings: [(Sym, Type)], :epoch_number: Int }
SExpr = Symbol | Ref | Node | List
ValidationReport = { :INV_CAUSAL_CYCLE: Bool, :INV_REGRESSION_FAILURE: { :break_count: Int, :severity: Float }, :INV_AST_TOO_DEEP: { :max_depth: Int, :unbound_symbols: [Sym] }, :INV_CONTINUITY_BROKEN: Bool, :INV_INSUFFICIENT_AUTHORITY: Bool }

CONFIG
TX_TIMEOUT = 3000ms (Configurable)
MAX_DEPTH = 6

INVARIANTS
INV_LOCK_ATOMIC = Lock(Targets) -> All | None. Fail -> INV_NODE_LOCKED
INV_CLOCK_ISOLATION = Clock_tentative visible only in PREPARING. No holes in Clock_kernel
INV_CANONICAL_MUTATION = Canonical update ONLY via COMMIT_CORRECTION
INV_DERIVED_CONSISTENCY = Derived = f(Canonical)
INV_RADIUS = Correction Scope = {Target} U Children(Target)
INV_EPOCH_MONOTONIC = Node.epoch_number increments on COMMIT_CORRECTION

OPERATIONS
Normalize(SExpr) -> SExpr: If Depth(S) > MAX_DEPTH -> Extract Subtree -> (node :id <Ref> :body Subtree), Replace with (ref <Ref>)
Validate(Candidate) -> ValidationReport: Check Invariants. No side effects.
PolicyRouter(Report, Config) -> Decision: COMMIT_CORRECTION | Reject
EpochCheck(Candidate, Node) -> Bool: If Candidate.base_epoch < Node.current_epoch -> DISCARD_STALE_CONTEXT

STATE_MACHINE
IDLE --(VALIDATED_CORRECTION_FACT)--> PREPARING_CORRECTION
PREPARING_CORRECTION:
  Pre: Lock(Targets). Fail -> INV_NODE_LOCKED
  Action: Clock_tentative = Clock_kernel + 1. WAL.Write(PREPARE_CORRECTION). Fsync
  Post: APPLYING_CORRECTION
APPLYING_CORRECTION:
  Action: Update AST/DAG. WAL.Write(COMMIT_CORRECTION). Fsync
  Post: Clock_kernel = Clock_tentative. Update WorldHead. Unlock. Emit ReindexEvent. -> IDLE
Timeout(State) where State in [PREPARING_CORRECTION, APPLYING_CORRECTION] -> ABORTING_CORRECTION
ABORTING_CORRECTION:
  Action: Discard Memory. WAL.Write(ABORT). Fsync
  Post: -> IDLE

RECOVERY
OnRestart: Scan WAL
Case PREPARE only: Write ABORT. Discard
Case PREPARE + ABORT: Write COMPLETE. Discard
Case PREPARE + COMMIT: Reapply. Advance WorldHead
Post-Recovery: Emit BulkReindexEvent

DEPENDENCIES
L5_Recovery -> L4_Kernel -> L3_Validation -> L2_Normalization -> L1_Constitution