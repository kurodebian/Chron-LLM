;; DEPRECATED: All logic has been consolidated into runtime/ir/chron-llm-r1-ir-observation-layer-spec-v1.0.spec
MODULE ir-divergence : ObservationAnalysisLayer | STATUS Deprecated
IMPORTS: [chron-observation-layer]

TYPE Profile = chron-observation-layer.DivRes
TYPE Prompt = STRING

OP extract-actions(stream: ir.IR_Buffer) -> Array[ir.IR] => chron-observation-layer.extract-actions(stream)
OP divergence-profile(prompt: Prompt, n-runs: INT, buf: ir.IR_Buffer) -> Array[Profile] => chron-observation-layer.divergence-profile(prompt, n-runs, 0)