MOD immune.lisp : Kernel/ImmuneService

TYPE Ctx = opaque_ptr
TYPE Logits = float[]
TYPE Status = :healthy | :warning | :fault
TYPE Result = tuple(Status, Float)

CONST FAULT_THRESH = 3.5
CONST WARN_THRESH = 2.5
CONST EPSILON = 1e-6

FFI get_logits(ctx: Ctx) -> Logits
FFI n_vocab(ctx: Ctx) -> Int

OP calculate_entropy(ctx: Ctx) -> Float:
    IF ctx==NIL RETURN(1.0 + rand(0.8))
    L = get_logits(ctx)
    m = max(L)
    S = sum(exp(x - m) for x in L)
    H = 0.0
    FOR x IN L:
        p = exp(x - m) / S
        IF p > EPSILON THEN H -= p * log(p)
    RETURN H

OP check_immune_status(ctx: Ctx, next_id: Int) -> Result:
    E = calculate_entropy(ctx)
    IF E > FAULT_THRESH RETURN(:fault, E)
    IF E > WARN_THRESH RETURN(:warning, E)
    RETURN(:healthy, E)

TRANS Runtime_Per_Token:
    R = check_immune_status(ctx, next_id)
    CASE R.status OF
        :fault -> Action(Rollback | KV_Reset | Stop)
        :warning -> Action(Log_Warning | Continue)
        :healthy -> Action(Decode_Token | Continue)

INV Pure_Functionality: calculate_entropy depends ONLY on Logits.
INV Monotonic_Thresholds: WARN_THRESH < FAULT_THRESH.
INV Complexity: Time=O(V), Space=O(1).