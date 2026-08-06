STATE: STATUS=FROZEN, REV=1.0, DATE=2026-07-12, COMPAT=GUARANTEED, BREAKING=PROHIBITED
SCOPE: INC=[ObsRuntime, ObsObjABI, ObsSemantics], EXC=[BackendABI, Evaluator, Scheduler, MergeRuntime, R2.1+]
TYPES: world-observation, registry-observation, ancestry-observation, diff-observation, kernel-observation
OPS: build-world-observation->world-observation, build-registry-observation->registry-observation, build-ancestry-observation->ancestry-observation, build-diff-observation->diff-observation, build-kernel-observation->kernel-observation, describe-world->world-observation, describe-registry->registry-observation, describe-ancestry->ancestry-observation, describe-diff->diff-observation, describe-kernel->kernel-observation
INV: D1=!mutate(world), D2=!mutate(registry), D3=deterministic(obs), D4=accurate(ancestry), D5=deterministic(diff), D6=repr_independent(obs), ABI=additive_only(extensions), DESC=read_only(return)
VERIFY: ENV=SBCL_2.2.9, TESTS=PASS