TYPE KnowledgeSystem = { meta: Meta, design: Design, executable: Executable }
TYPE Meta = { foundation: Foundation, governance: Governance }
TYPE Foundation = { purpose: Concept, philosophy: Concept, direction: Concept }
TYPE Governance = { policies: [Lifecycle | Versioning | Freeze | Amendment | Compatibility | Review | ReferenceRules | Traceability] }
TYPE Design = { constitution: Constitution, domainModel: DomainModel, charter: Charter, specification: Specification }
TYPE Constitution = { principles: [Concept], invariants: [Rule] }
TYPE DomainModel = { concepts: [Concept], entities: [Entity] }
TYPE Charter = { responsibilities: [Responsibility], boundaries: [Boundary] }
TYPE Specification = { interfaces: [Interface], contracts: [Contract], rules: [Rule] }
TYPE Executable = { runtime: Runtime }
TYPE Runtime = { implementations: [Implementation] }

INV Independence: Architecture !-> RepoLayout | DirStructure | DocNames | Lang | Impl
INV GovernanceScope: Governance -> Artifact && Governance !-> RuntimeBehavior
INV RuntimeSatisfaction: Runtime -> Specification
INV RuntimeVolatility: Runtime.evolution > Design.evolution
INV Minimalism: Concepts = Min(Necessary)
INV Neutrality: KnowledgeSystem !-> Product | Repo | Impl
INV EvolutionRule: Introduce(NewCategory) -> !Exists(ExistingCategory -> Responsibility)
INV ExtensionPriority: Extend(Existing) > Introduce(New)

PROCESS KnowledgeLifecycle: Understand -> Analyze -> Design -> Implement -> Verify -> Record

STATE Baseline: status = StableFoundation; scope = MinimumRequired