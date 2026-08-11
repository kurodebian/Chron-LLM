Type Meta : GovernanceLayer
Type Design : ConceptualLayer
Type Runtime : ExecutionLayer
Type Governance : LifecycleLayer
Type Foundation : PurposeLayer
Type Constitution : InvariantLayer
Type Repository : PhysicalLayer
Type Architecture : StructuralLayer
Type Process : WorkflowLayer
Type Responsibility : SemanticUnit
Type EvolutionRule : Constraint
Type Content : KnowledgeUnit
Type Implementation : BehavioralUnit
Type Authority : TruthSource
Type Representation : ViewUnit

Meta -> governs(KnowledgeStructure)
Design -> defines(ConceptualStructure, Responsibility[])
Runtime -> implements(Design)
Governance -> manages(ArtifactLifecycle)
Foundation -> defines(Purpose)
Constitution -> defines(Invariant[])
Architecture -> defines(KnowledgeStructure)
Process -> defines(Workflow)
Authority -> defines(TruthState)
Representation -> maps(Authority)

INV: Meta != Design
INV: Runtime != Design
INV: Runtime.evolution independent_of Design.evolution
INV: Governance != Design
INV: Foundation != Constitution
INV: Repository.Layout independent_of Architecture
INV: Architecture != Process
INV: Concept.definition depends_on(Responsibility)
INV: Concept.definition NOT depends_on(Implementation)
INV: NewConcept.introduction requires !Exists(r in Responsibility : r.canExpress(Meaning))
INV: Content.definition precedes Implementation.expansion
INV: Constitution != Implementation
INV: Implementation.evolution preserves(Constitution)
INV: Authority != Representation
INV: Representation.derived != Authority