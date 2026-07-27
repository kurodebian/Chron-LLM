MODULE ir-divergence : ObservationAnalysisLayer | STATUS StableBaseline
TYPE IR = { phase: Int, pos: Int, token: String }
TYPE Profile = { step: Int, all-same: Bool, p-same: Float }
TYPE Prompt = String
STATE *model*, *ctx* : ExternalContext
OP extract-actions(stream: Vector<IR>) -> List<IR>
  PRE stream != NULL
  ALGO sorted=sort(copy(stream),key=pos); return filter(sorted,x.phase==1)
  COST O(N log N)
OP run-ir-trial(prompt: Prompt) -> Vector<IR>
  PRE *model* valid AND *ctx* valid
  ALGO clear(ir-stream); llama-run(*model*,*ctx*,prompt); return coerce(extract-actions(ir-stream),Vector)
OP divergence-profile(prompt: Prompt, n-runs: Int) -> List<Profile>
  PRE n-runs > 0
  ALGO runs=[run-ir-trial(prompt) for _ in range(n-runs)]; L=min(len(r) for r in runs); profiles=[]; FOR s IN 0..L: tokens=[r[s].token for r in runs]; cnt=max(count(t) for t in unique(tokens)); p=cnt/n-runs; profiles.append({step:s,all-same:(p==1.0),p-same:p}); RETURN profiles
INV INV_OBS_ONLY : !write(Runtime|Kernel|Candidate|Canonical|Prompt)
INV INV_DET : Same inputs -> Same outputs; No RNG in analysis
INV INV_LOSSLESS : IR immutable during processing
INV INV_ISOLATION : Results not fed back to Runtime control