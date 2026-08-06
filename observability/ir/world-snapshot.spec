;; =============================================================================
;; RELEASE & ABI GOVERNANCE
;; =============================================================================
;; STATUS          : FROZEN
;; REV             : 1.0
;; GOVERNANCE_REF  : docs/ir/r2-0-c-freeze-report.spec
;; CONSTITUTION_REF: docs/ir/Chron-LLM_R2.0-C_Observability_Runtime_Constitution_Spec.spec
;; ABI_POLICY      : additive_only
;; BREAKING_CHANGE : PROHIBITED
;; ENV_TARGET      : SBCL_2.2.9
;; =============================================================================
;; TYPE MAPPING TABLE (Constitution Abstract Types -> Concrete IR Indices)
;; =============================================================================
;; Constitution Type   | Concrete IR Type      | Field / Index Mapping
;; --------------------+-----------------------+-------------------------------------------------------------
;; WorldObs            | world-observation     | [0]=schema, [1]=id, [2]=root, [3]=head, [4]=policy, [5]=meta...
;; RegistryObs         | registry-observation  | [0]=schema, [1]=ids, [2]=active, [3]=archived
;; KernelObs           | kernel-observation    | [0]=schema, [1]=kernel-id, [2]=cycle, [3]=flags, [4]=hash, [5]=context
;; =============================================================================

PKG chron-r2-0-c; DEP chron-r2-0-a
CONST +observation-schema-version+ = 1
TYPE PrimitiveLeaf = null | t | string | number | char | keyword
TYPE PrimitiveTree = PrimitiveLeaf | (cons PrimitiveTree PrimitiveTree)
INV: Obs fields subset PrimitiveTree. Accessors -> deep-copy(%copy-primitive-tree). Builders -> validate %require-primitive-tree.

TYPE world-observation = [schema-version:int, world-id:PrimitiveTree, root-node-id:PrimitiveTree, head-node-id:PrimitiveTree, projection-policy:PrimitiveTree, metadata:PrimitiveTree, lifecycle:value, parent-world-id:PrimitiveTree]
PRED world-observation-p(o) = vectorp(o) & len(o)=8 & o[0]==+observation-schema-version+
OP world-observation-equal(a,b) = vector-equal(a,b)

TYPE registry-observation = [schema-version:int, world-ids:PrimitiveTree, active-world-id:PrimitiveTree, archived-world-ids:PrimitiveTree]
PRED registry-observation-p(o) = vectorp(o) & len(o)=4 & o[0]==+observation-schema-version+
OP registry-observation-equal(a,b) = vector-equal(a,b)

TYPE ancestry-observation = [schema-version:int, world-id:PrimitiveTree, parent-world-id:PrimitiveTree, ancestry-path:PrimitiveTree]
PRED ancestry-observation-p(o) = vectorp(o) & len(o)=4 & o[0]==+observation-schema-version+
OP ancestry-observation-equal(a,b) = vector-equal(a,b)

TYPE diff-observation = [schema-version:int, changed-p:boolean, changed-fields:PrimitiveTree]
PRED diff-observation-p(o) = vectorp(o) & len(o)=3 & o[0]==+observation-schema-version+
OP diff-observation-equal(a,b) = vector-equal(a,b)


TYPE kernel-observation = [schema-version:int, kernel-id:PrimitiveTree, cycle-count:uint64, status-flags:uint32, memory-hash:PrimitiveTree, context-state:PrimitiveTree]
PRED kernel-observation-p(o) = vectorp(o) & len(o)=6 & o[0]==+observation-schema-version+
OP kernel-observation-equal(a,b) = vector-equal(a,b)

FUNC build-world-observation(world, parent-world-id?) -> world-observation
  PRE: world-p(world)
  POST: result.world-id=world-id(world), result.root-node-id=root-node-id(world), result.head-node-id=head-node-id(world), result.projection-policy=projection-policy(world), result.metadata=metadata(world), result.lifecycle=lifecycle(world), result.parent-world-id=parent-world-id

FUNC build-registry-observation(registry) -> registry-observation
  PRE: world-registry-p(registry)
  POST: result.world-ids=list-worlds(registry), result.active-world-id=active-world(registry), result.archived-world-ids=[w | w in list-worlds(registry) if lifecycle(w)==:archived]

FUNC build-ancestry-observation(registry, world-id) -> ancestry-observation
  PRE: world-registry-p(registry), exists-parent(registry, world-id)
  POST: result.world-id=world-id, result.parent-world-id=get-parent(registry, world-id), result.ancestry-path=(cons world-id parent-world-id)

FUNC build-diff-observation(left, right) -> diff-observation
  LOGIC: type(left)!=type(right) -> changed-fields=(:type); else if known-obs-type(type(left)) -> compare fields; else changed-fields=[]


FUNC build-kernel-observation(kernel) -> kernel-observation
  PRE: kernel-p(kernel)
  POST: result.kernel-id=kernel-id(kernel), result.cycle-count=kernel-cycle-count(kernel), result.status-flags=kernel-status-flags(kernel), result.memory-hash=kernel-memory-hash(kernel), result.context-state=kernel-context-state(kernel)

ALIAS describe-world = build-world-observation
ALIAS describe-registry = build-registry-observation
ALIAS describe-ancestry = build-ancestry-observation
ALIAS describe-diff = build-diff-observation
ALIAS describe-kernel = build-kernel-observation
