TYPE ID = Symbol | String
TYPE Keyword = Symbol
TYPE Ref = Any
TYPE Metadata = Map<String, Any>

CausalNode = { id: ID [RO], type: Keyword [RO], payload-ref: Ref [RO], metadata: Metadata [RO] }
CausalEdge = { from: ID [RO], to: ID [RO], type: Keyword [RO] }
CausalGraph = { nodes: [CausalNode], edges: [CausalEdge] }

make-causal-node(id, type, payload-ref, metadata?) -> CausalNode
make-causal-edge(from, to, type) -> CausalEdge
make-causal-graph(nodes?, edges?) -> CausalGraph

get-node(g: CausalGraph, id: ID) -> CausalNode | nil
  PRE: true
  POST: result = find(n in g.nodes where n.id == id) || nil

add-node!(g: CausalGraph, node: CausalNode) -> CausalGraph
  PRE: is-causal-node(node) AND NOT exists(n in g.nodes where n.id == node.id)
  POST: result.nodes = append(g.nodes, [node]) AND result.edges == g.edges

add-edge!(g: CausalGraph, edge: CausalEdge) -> CausalGraph
  PRE: is-causal-edge(edge) AND exists(n in g.nodes where n.id == edge.from) AND exists(m in g.nodes where m.id == edge.to)
  POST: result.edges = append(g.edges, [edge]) AND result.nodes == g.nodes

INV NODE-UNIQUE: forall x,y in CausalGraph.nodes, x != y -> x.id != y.id
INV EDGE-CLOSURE: forall e in CausalGraph.edges, exists n1,n2 in CausalGraph.nodes where (n1.id == e.from AND n2.id == e.to)
INV FIELD-IMMUTABLE: all fields of CausalNode/CausalEdge are read-only post-construction