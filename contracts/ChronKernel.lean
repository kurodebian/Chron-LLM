-- ChronKernel.lean (v2.7.1 Final Frozen Public Interface)
import ChronLLM.Internal

namespace ChronLLM

def TokenState        := ChronLLM.Internal.TokenState
def KernelContext     := ChronLLM.Internal.KernelContext
def KernelAction      := ChronLLM.Internal.KernelAction
def Runtime           := ChronLLM.Internal.Runtime
def History           := ChronLLM.Internal.History
def Projection        := ChronLLM.Internal.Projection
def Event             := ChronLLM.Internal.Event
def EventFact         := ChronLLM.Internal.EventFact
def project           := @ChronLLM.Internal.project
def stepRuntime       := ChronLLM.Internal.stepRuntime

-- Theorem 1: History Index Consistency Theorem
theorem history_index_homomorphism
    {ctx : KernelContext}
    {p : Projection}
    (h : History ctx p) :
    project h = p :=
  rfl

-- Theorem 2: Transition Index Determinism Theorem
theorem step_runtime_index_correctness
    (ctx : KernelContext)
    (rt : Runtime ctx TokenState.available)
    (act : KernelAction ctx)
    (h_allowed : match rt with | ChronLLM.Internal.Runtime.available _ _ cap => cap.allowedAction act) :
    let res := stepRuntime ctx rt act h_allowed
    match rt with
    | ChronLLM.Internal.Runtime.available p _ _ =>
      res.2.1 = { stateMap := ChronLLM.Internal.applyIntentToMap act.intent p.stateMap } :=
  by
    cases rt
    rfl

end ChronLLM