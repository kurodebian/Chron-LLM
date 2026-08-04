// ============================================================================
// Chron-LLM Phase C: Single Source of Truth (SSOT) Domain Schema (v1.0)
// File: docs/ir/01-domain-model.spec
// ============================================================================

ENUM Source={user,assistant,tool,system}
ENUM Intent={append,reflect,tool,memory-read,memory-write,recover,summarize}
ENUM ReqKind={commit-request,reject-request,defer-request,retry-request,retry-penalty-request,abort-request}
ENUM CmdKind={proceed,discard,sleep,regenerate,regenerate-with-penalty,terminate}

// --- Core Data Schema (Standardized Payload & Metadata) ---
TYPE Event={id,source:Source,payload,metadata:{ts,seq,causal-ref?}}
TYPE Candidate={id,origin,trigger,source:Source,intent:Intent,payload,constraints,metadata}
TYPE ValidationReport={facts,passed:Boolean}

// --- Pipeline Request & Command Contract ---
TYPE RuntimeRequest={kind:ReqKind,payload,metadata}
TYPE KernelAction={kind:ReqKind,payload,origin_req:RuntimeRequest}
TYPE RuntimeCommand={kind:CmdKind,payload,metadata}
TYPE FaultEvent={type,reason,metadata}

// --- Top-Level State Entities ---
TYPE Canonical={id,evidence:[Event],config,mem-ref}
TYPE Working={candidate:Candidate?,proc-state}
TYPE Derived={projection,analysis}
TYPE External={ext-ref}

TYPE Session={canonical_ref:Ref<Canonical>,working:Working,derived:Derived,external:External}
TYPE Context={canon-ref:Ref<Canonical>}

// --- Invariants ---
INV(Canonical):mutate_only_via(Commit)
INV(Derived):reproducible_from(Canonical),!authoritative
INV(Evidence):subset_of(Canonical.evidence),ordered_by(causal|seq)

// --- Producer / Consumer Map ---
PROD_CONS={
  Event:Commit->[Replay,History],
  Candidate:Backend->Validation,
  ValidationReport:Validation->PolicyRouter,
  RuntimeRequest:PolicyRouter->Kernel,
  RuntimeCommand:Kernel->Runtime,
  FaultEvent:Kernel->Observability,
  Derived:Replay->PromptBuilder,
  Canonical:Commit->[Replay,Validation]
}

// --- Ownership & Read Permission Map ---
OWNERSHIP={
  Candidate:Runtime(Read:[Validation,Kernel]),
  ValidationReport:Validation(Read:PolicyRouter),
  RuntimeRequest:PolicyRouter(Read:Kernel),
  RuntimeCommand:Kernel(Read:Runtime),
  FaultEvent:Kernel(Read:Observability),
  Canonical:Kernel(Read:[Replay,Validation]),
  Working:Runtime(Read:Runtime),
  Derived:Replay(Read:Runtime),
  External:Runtime(Read:Runtime)
}