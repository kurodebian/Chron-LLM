MOD chron-r2-0-a

TYPE payload-ref = { hash:String, type:Keyword, size:Int>=0, storage:Keyword }
INV(payload-ref): immutable_fields

TYPE store = Map{test=equal}
INV(store): explicit_reference; !global_singleton

TYPE causal-node | causal-edge | context-node : Abstract
TYPE causal-graph | causal-subgraph : Abstract
TYPE world | world-registry : Abstract

OP make-payload-ref(hash:String="", type:Keyword=:text, size:Int>=0=0, storage:Keyword=:memory) -> payload-ref

GET payload-ref.hash -> String
GET payload-ref.type -> Keyword
GET payload-ref.size -> Int
GET payload-ref.storage -> Keyword

OP make-memory-store() -> store

OP %content-string(c:Any) -> String
  POST: res = (IS_STRING(c) ? c : prin1-to-string(c))

OP utf8-octets(s:String) -> [UInt8]

OP sha256-string(s:String) -> String
  LOGIC:
    octets = utf8-octets(s)
    padded = SHA256_PAD(octets, 0x80, len_bits)
    digest = SHA256_BLOCKS(padded, +sha256-k+, %ror)
    RETURN "sha256:" + HEX(digest)

OP store-payload(store:store, content:Any, type:Keyword=:text, storage:Keyword=:memory) -> payload-ref
  LOGIC:
    s = %content-string(content)
    h = sha256-string(s)
    IF !EXISTS(store[h]) THEN store[h] = s ENDIF
    RETURN make-payload-ref(h, type, LEN(UTF8(s)), storage)

OP load-payload(store:store, ref:payload-ref|String) -> String|Nil
  LOGIC:
    h = (IS_TYPE(ref, payload-ref) ? ref.hash : ref)
    RETURN store[h]

OP payload-exists-p(store:store, ref:payload-ref|String) -> Bool
  LOGIC:
    h = (IS_TYPE(ref, payload-ref) ? ref.hash : ref)
    RETURN EXISTS(store[h])

OP add-node!(graph:causal-graph, node:causal-node) -> Void
OP add-edge!(graph:causal-graph, src:causal-node, dst:causal-node) -> Void
OP get-node(graph:causal-graph, id:Any) -> causal-node|Nil
OP associated-evaluations(node:causal-node) -> [Any]

OP fork-world(src:world) -> world
OP replace-world-metadata!(w:world, meta:Any) -> Void
OP kernel-commit-world!(w:world) -> Void
OP replay-world(w:world) -> Void
OP register-world(reg:world-registry, w:world) -> Void
OP find-world(reg:world-registry, id:Any) -> world|Nil
OP active-world() -> world
OP set-active-world(w:world) -> Void
OP list-worlds() -> [world]
OP archive-world(w:world) -> Void

OP prefill-state() -> Any
OP canonical-prompt() -> String