# 13-worldline-branching.spec (Worldline Branching Contract)

MODULE WorldlineBranching
  REQUIRES: [ architecture-v1.1, constitution ]

## 1. TYPES

Type DiscontinuityType = :discontinuity | :abort | :drift | :stagnation

Type BranchTrigger = {
    event_type: DiscontinuityType,
    count: U32
}

Type BranchCandidate = {
    parent_event: CandidateEvent,
    target_world_id: WorldID,
    derivation_hash: HashString
}


## 2. PREDICTING BRANCH CONDITIONS

Pred NeedBranch(trigger: BranchTrigger) = 
    (trigger.event_type in {:discontinuity, :abort}) | 
    (trigger.event_type == :drift & trigger.count >= 3) | 
    (trigger.event_type == :stagnation & trigger.count >= 5)


## 3. OPERATIONS

Op ExecuteBranch(
    state: SystemState, 
    parent_event: CandidateEvent, 
    trigger: BranchTrigger,
    new_world_id: WorldID
) -> Result<SystemState, BranchError>

  PRE: 
    NeedBranch(trigger) AND
    ExistsInWAL(state.wal, parent_event.parent_id) AND
    NOT ExistsWorld(state.world_heads, new_world_id)

  STEPS:
    // 1. 因果ハッシュの決定論的計算（内部クロック/可変ID/gen_id()は使用しない）
    derivation_hash = Hash(parent_event.parent_id || new_world_id || parent_event.kind)
    
    candidate = BranchCandidate {
        parent_event: parent_event,
        target_world_id: new_world_id,
        derivation_hash: derivation_hash
    }

    // 2. Constitution (B) の Commit を呼び出し、不変条件検証とWAL追記をアトミック委任
    commit_result = Constitution.Commit(state, candidate)

    IF commit_result.is_success THEN
        state.active_causal_id = derivation_hash
        state.kv_cache = NULL  // 分岐に伴うキャッシュクリア
        state.world_heads[new_world_id] = derivation_hash
        RETURN Ok(state)
    ELSE
        RETURN Err(BranchError.ValidationFailed(commit_result.reason))


## 4. INVARIANTS

INV: Branch deterministic (derivation_hash depends only on parent_id, world_id, kind)
INV: history replayable from WAL
INV: forall w in state.world_heads: w.key != state.active_stream_id => w.value is immutable
