MODULE MetaModel DEFINES SpecOS::LanguageAST

-- ===================================================================
-- 1. PRIMITIVES
-- ===================================================================
TYPE Identifier   = StringConstraint(Pattern: "^[a-z][a-z0-9\-_]*$")
TYPE ModulePath   = List<Identifier>   -- 階層的モジュールID
TYPE TypeSymbol   = StringConstraint(Pattern: "^[A-Z][a-zA-Z0-9]*$")
TYPE VersionExpr  = StringConstraint(Pattern: "^v[0-9]+\.[0-9]+\.[0-9]+$")

-- ===================================================================
-- 2. SPECIFICATION FILE
-- ===================================================================
RECORD SpecificationFile {
  module_name : ModulePath,
  version     : VersionExpr,
  imports     : List<ImportStatement>,
  exports     : List<ExportStatement>,
  body        : List<SpecNode>
}

RECORD ImportStatement {
  source_path : ModulePath,
  symbols     : List<Identifier>
}

RECORD ExportStatement {
  symbols     : List<Identifier>
}

-- ===================================================================
-- 3. TOP-LEVEL SPEC NODES
-- ===================================================================
VARIANT SpecNode {
  | TypeDefinitionNode(TypeDef)
  | OperationDefinitionNode(OperationDef)
  | ContractDefinitionNode(ContractDef)
  | InvariantDefinitionNode(InvariantDef)
  | ReferenceDefinitionNode(ReferenceDef)
  | ConstantDefinitionNode(ConstDef)
  | AnnotationNode(Annotation)
}

-- ===================================================================
-- 4. TYPE SYSTEM
-- ===================================================================
VARIANT TypeExpr {
  | PrimitiveType(TypeSymbol)
  | SymbolType(TypeSymbol)
  | ListType(TypeExpr)
  | OptionalType(TypeExpr)
  | MapType(key: TypeExpr, value: TypeExpr)
  | VariantType(variants: Map<Identifier, TypeExpr>)
  | RecordType(fields: Map<Identifier, TypeExpr>)
  | AliasType(target: TypeExpr)
}

RECORD TypeDef {
  name       : TypeSymbol,
  body       : TypeExpr,
  attributes : List<Attribute>
}

-- ===================================================================
-- 5. CONSTANTS / SYMBOL DECLARATIONS
-- ===================================================================
RECORD ConstDef {
  name       : Identifier,
  type       : TypeExpr,
  value      : Expression,
  annotations: List<Annotation>
}

-- ===================================================================
-- 6. OPERATIONS
-- ===================================================================
RECORD OperationDef {
  name        : Identifier,
  inputs      : Map<Identifier, TypeExpr>,
  outputs     : Map<Identifier, TypeExpr>,
  pre_cond    : List<Expression>,
  post_cond   : List<Expression>,
  annotations : List<Annotation>
}

-- ===================================================================
-- 7. CONTRACTS (ASSUMPTIONS / GUARANTEES / INVARIANTS)
-- ===================================================================
RECORD ContractDef {
  id          : Identifier,
  target      : Reference,           -- Operation / Type / Module
  assumptions : List<Expression>,
  guarantees  : List<Expression>,
  invariants  : List<Expression>,
  annotations : List<Annotation>
}

-- ===================================================================
-- 8. INVARIANTS
-- ===================================================================
RECORD InvariantDef {
  id         : Identifier,
  target     : Reference,            -- Type / Module / Contract
  condition  : Expression,
  fallback   : Optional<Identifier>, -- Recovery / Fault handler
  annotations: List<Annotation>
}

-- ===================================================================
-- 9. REFERENCES & RELATIONS
-- ===================================================================
RECORD Reference {
  module : ModulePath,
  symbol : Identifier
}

ENUM RelationKind {
  DependsOn,
  Refines,
  Implements,
  Generates,
  Verifies,
  MapsTo
}

RECORD ReferenceDef {
  id        : Identifier,
  kind      : RelationKind,
  source    : Reference,
  target    : Reference,
  metadata  : Map<Identifier, Expression>,
  annotations: List<Annotation>
}

-- ===================================================================
-- 10. EXPRESSIONS (AST FOR PRE/POST/INV/CONTRACT)
-- ===================================================================
ENUM Operator {
  -- Arithmetic
  Add, Sub, Mul, Div,
  -- Logic
  And, Or, Not,
  -- Compare
  Eq, Neq, Lt, Gt, Le, Ge,
  -- Collection
  Contains, MemberOf
}

VARIANT Expression {
  | BoolLiteral(Boolean)
  | IntLiteral(Integer)
  | StringLiteral(String)
  | IdentifierRef(Identifier)
  | BinaryExpr(lhs: Expression, op: Operator, rhs: Expression)
  | UnaryExpr(op: Operator, expr: Expression)
  | FunctionCall(name: Identifier, args: List<Expression>)
  | Quantifier(kind: ENUM { ForAll, Exists },
               var: Identifier,
               domain: Expression,
               body: Expression)
}

-- ===================================================================
-- 11. ANNOTATIONS / ATTRIBUTES
-- ===================================================================
RECORD Annotation {
  name      : Identifier,
  arguments : Map<Identifier, Expression>
}

RECORD Attribute {
  key   : Identifier,
  value : String
}

-- ===================================================================
-- 12. META INVARIANTS (LANGUAGE-LEVEL CONSTRAINTS)
-- ===================================================================
INVARIANT META_01: UniqueSymbolsPerFile {
  FORALL f IN SpecificationFile =>
    IsUnique(AllSymbols(f.body))
}

INVARIANT META_02: ImportGraphIsAcyclic {
  FORALL m IN AllModules =>
    IsAcyclic(DependencyGraph(m))
}

INVARIANT META_03: NoUndefinedReference {
  FORALL r IN ReferenceDef =>
    ExistsModule(r.source.module)
    AND ExistsSymbol(r.source)
    AND ExistsModule(r.target.module)
    AND ExistsSymbol(r.target)
}

INVARIANT META_04: MetaDoesNotDependOnSemantic {
  FORALL f IN SpecificationFile =>
    NOT ImportsSemanticLayer(f.module_name)
}

INVARIANT META_05: GenerationBoundaryIsolation {
  FORALL change IN ChangeLog =>
    NOT (change.origin == PhysicalImplementation
         AND change.target == MetaModel)
}
