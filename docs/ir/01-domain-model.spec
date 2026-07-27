ENUM Source={user,assistant,tool,system}
ENUM Intent={append,reflect,tool,memory-read,memory-write,recover,summarize}
ENUM ReqKind={commit-request,reject-request,defer-request,retry-request,retry-penalty-request,abort-request}
ENUM CmdKind={proceed,discard,sleep,regenerate,regenerate-with-penalty,terminate}

TYPE Event={id,source:Source,content,meta:{ts,seq,causal-ref?}}
TYPE Candidate={id,origin,intent:Intent,content,constraints,meta}
TYPE ValidationReport={facts}
TYPE RuntimeRequest={kind:ReqKind,payload}
TYPE RuntimeCommand={kind:CmdKind,payload}
TYPE FaultEvent={type,reason,meta}

TYPE Session={canonical:Canonical,working:Working,derived:Derived,external:External}
TYPE Canonical={evidence:[Event],config,mem-ref}
TYPE Working={candidate:Candidate?,proc-state}
TYPE Derived={projection,analysis}
TYPE External={ext-ref}
TYPE Context={canon-ref}

INV(Canonical):mutate_only_via(Commit)
INV(Derived):reproducible_from(Canonical),!authoritative
INV(Evidence):subset_of(Canonical.evidence),ordered_by(causal|seq)

PROD_CONS={Event:Commit->[Replay,History],Candidate:Backend->Validation,Report:Validation->PolicyRouter,Request:PolicyRouter->Kernel,Command:Kernel->Runtime,FaultEvent:Kernel->Observability,Derived:Replay->PromptBuilder,Canonical:Commit->[Replay,Validation]}
OWNERSHIP={Candidate:Runtime(Read:[Validation,Kernel]),Report:Validation(Read:PolicyRouter),Request:PolicyRouter(Read:Kernel),Command:Kernel(Read:Runtime),FaultEvent:Kernel(Read:Observability),Canonical:Kernel(Read:[Replay,Validation]),Working:Runtime(Read:Runtime),Derived:Replay(Read:Runtime),External:Runtime(Read:Runtime)}