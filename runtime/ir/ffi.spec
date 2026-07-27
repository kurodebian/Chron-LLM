MOD ir-ffi
USE [CL, CFFI, IR-CALLBACK]
EXPORT [init-ir-bridge]

EXT register_ir_callback(cb: Ptr) -> Void

STATE *ir-callback-pointer*: Ptr = NIL

OP init-ir-bridge():
  ptr := cffi:callback(ir-callback)
  *ir-callback-pointer* := ptr
  register_ir_callback(ptr)

INV:
  - (*ir-callback-pointer* != NIL) -> (gc_rooted(*ir-callback-pointer*))
  - !contains(ir-ffi, [IR_GEN, IR_PARSE, COMMIT])

PRE init-ir-bridge: symbol_exists(register_ir_callback)
POST init-ir-bridge: registered_in_c_runtime(*ir-callback-pointer*)