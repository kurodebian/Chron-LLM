PKG chronos-r0

OP start-chat : () -> Any

IMPL:
  start-chat() = chronos-r0.chat:start-chat()

STATE S = {}

CONTRACT(start-chat):
  PRE = True
  POST(r) = (r == chronos-r0.chat:start-chat())

INV:
  - impl(start-chat) -> delegate(chronos-r0.chat:start-chat)
  - args(start-chat) == []
  - return_val == passthrough(delegate_return)
  - delta(S) == {}
  - side_effects(Runtime|Session|History|Prompt|Kernel) == None
  - role(Facade) = True