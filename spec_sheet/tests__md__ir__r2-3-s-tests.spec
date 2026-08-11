PKG chron-llm/r2-3-s-tests :cl
IMPORTS chron-llm/r2-3-s {make-world-state, copy-world-state, scheduler-step, make-physical-action}
EXPORTS run-r2-3-s-verification

TYPE world-state = {causal-id: string|nil, parent-id: string|nil, status: symbol, retry-count: int, history: list[], context: list[symbol]}
TYPE physical-action = {type: symbol, payload: any}

DEF %make-genesis-world() -> world-state:
  make-world-state(causal-id="genesis", parent-id=nil, status=:running, retry-count=0, history=nil, context='(:phase :r2-3-s :origin :genesis))

DEF run-r2-3-s-verification() -> T:
  S1(); S2(); S3(); S4()
  PRINT "S-Tier verification passed."
  RETURN T

DEF S1():
  world = %make-genesis-world()
  before = copy-world-state(world)
  scheduler-step(world, '(:op :retry), "child") -> _
  INV equalp(world, before) == T

DEF S2():
  world = %make-genesis-world()
  old-history = world.history
  ops = '(:op :retry ...)
  new-world, _ = scheduler-step(world, ops, "child")
  INV equal(ops, first(new-world.history)) == T
  INV eq(old-history, cdr(new-world.history)) == T

DEF S3():
  world = %make-genesis-world()
  new-world, _ = scheduler-step(world, '(:op :retry), "child-id")
  INV string=("child-id", new-world.causal-id) == T
  INV string=("genesis", new-world.parent-id) == T

DEF S4():
  world = %make-genesis-world()
  w-retry, a-retry = scheduler-step(world, '(:op :retry), "c1")
  INV w-retry.retry-count == 1
  INV a-retry.type == :invoke-api
  w-abort, a-abort = scheduler-step(world, '(:op :abort), "c2")
  INV w-abort.status == :halted
  INV a-abort.type == :halt