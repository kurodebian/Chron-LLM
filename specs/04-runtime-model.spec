MODULE RuntimeModel
EXTENDS ChronSemanticExtension
DEFINES SpecOS::RuntimeUniverse

-- ================================================================
-- 0. SCOPE OF RUNTIME
-- ================================================================

RuntimeModel defines the non-authoritative execution pipeline
that transforms external observations into CommitRequest.

Runtime SHALL:

- receive external observations
- validate proposals
- route proposals according to policy
- schedule execution tasks
- produce CommitRequest as the ONLY input to Kernel

Runtime SHALL NOT:

- define semantic meaning
- define Commit semantics
- execute Commit
- mutate CanonicalState
- generate Event
- define authority


-- ================================================================
-- 1. IDENTIFIERS
-- ================================================================

TYPE ObservationID =
  IDType(NamespacedID("observation"))

TYPE ValidatorID =
  IDType(NamespacedID("validator"))

TYPE RouterID =
  IDType(NamespacedID("router"))

TYPE SchedulerID =
  IDType(NamespacedID("scheduler"))

TYPE ExecutionTaskID =
  IDType(NamespacedID("execution-task"))

TYPE CommitRequestID =
  IDType(NamespacedID("commit-request"))


-- ================================================================
-- 2. OBSERVATION MODEL
-- ================================================================

ENTITY Observation {

  observation_id :
    ObservationID

  source :
    Expression

  timestamp :
    LogicalClock

  content :
    Expression
}

INVARIANT OBS_01:
Observation MUST be non-authoritative.

INVARIANT OBS_02:
Observation MUST NOT define Event or Commit.


-- ================================================================
-- 3. VALIDATOR MODEL
-- ================================================================

ENTITY Validator {

  validator_id :
    ValidatorID
}

OPERATION Validate {

  input :
    Proposal

  output :
    ValidationReport
}


ENTITY ValidationReport {

  proposal :
    Reference<Proposal>

  result :
    Expression

  diagnostics :
    Expression
}

INVARIANT VAL_01:
Validator MUST NOT execute Commit.

INVARIANT VAL_02:
Validator MUST NOT mutate CanonicalState.


-- ================================================================
-- 4. POLICY ROUTER MODEL
-- ================================================================

ENTITY PolicyRouter {

  router_id :
    RouterID
}

OPERATION RouteProposal {

  input :
    Proposal

  validation :
    ValidationReport

  output :
    RuntimeDecision
}


ENTITY RuntimeDecision {

  proposal :
    Reference<Proposal>

  routing_action :
    Expression
}

INVARIANT ROUTE_01:
RuntimeDecision MUST NOT define Commit authority.

INVARIANT ROUTE_02:
RuntimeDecision MUST NOT mutate CanonicalState.


-- ================================================================
-- 5. SCHEDULER MODEL
-- ================================================================

ENTITY Scheduler {

  scheduler_id :
    SchedulerID
}

OPERATION Schedule {

  input :
    RuntimeDecision

  output :
    ExecutionTask
}


ENTITY ExecutionTask {

  task_id :
    ExecutionTaskID

  decision :
    Reference<RuntimeDecision>

  schedule_hint :
    Expression
}

INVARIANT SCHED_01:
Scheduler MUST NOT execute Commit.

INVARIANT SCHED_02:
Scheduler MUST NOT mutate CanonicalState.


-- ================================================================
-- 6. EXECUTION MODEL
-- ================================================================

OPERATION ExecuteRuntimeTask {

  input :
    ExecutionTask

  output :
    CommitRequest
}


-- ================================================================
-- 7. COMMIT REQUEST MODEL
-- ================================================================

ENTITY CommitRequest {

  request_id :
    CommitRequestID

  proposal :
    Reference<Proposal>

  decision :
    Reference<RuntimeDecision>

  context :
    Expression
}

CONTRACT CommitRequestContract {

  CommitRequest MUST contain:
    - ProposalReference
    - RuntimeDecisionReference
    - ExecutionContext

  Kernel MUST treat CommitRequest
  as the ONLY input for Commit execution.
}

INVARIANT CR_01:
CommitRequest MUST NOT define Commit semantics.

INVARIANT CR_02:
CommitRequest MUST NOT mutate CanonicalState.

INVARIANT CR_03:
CommitRequest MUST NOT generate Event.


-- ================================================================
-- 8. PERSISTENCE INTERFACE (NON-AUTHORITATIVE)
-- ================================================================

ENTITY PersistenceInterface {

  backend :
    Expression
}

INVARIANT PERSIST_01:
Runtime persistence MUST NOT define authority.

INVARIANT PERSIST_02:
Runtime persistence MUST NOT mutate CanonicalState.


-- ================================================================
-- 9. RUNTIME BOUNDARY INVARIANTS
-- ================================================================

INVARIANT RUNTIME_BOUNDARY_01:
Runtime MUST NOT execute Commit.

INVARIANT RUNTIME_BOUNDARY_02:
Runtime MUST NOT mutate CanonicalState.

INVARIANT RUNTIME_BOUNDARY_03:
Runtime MUST NOT generate Event.

INVARIANT RUNTIME_BOUNDARY_04:
Runtime MUST NOT redefine Commit meaning.

INVARIANT RUNTIME_BOUNDARY_05:
Runtime MUST produce CommitRequest
as the sole interface to Kernel.

INVARIANT RUNTIME_BOUNDARY_06:
Runtime MUST NOT redefine semantic meaning.

INVARIANT RUNTIME_BOUNDARY_07:
Runtime MUST NOT redefine constitutional laws.
