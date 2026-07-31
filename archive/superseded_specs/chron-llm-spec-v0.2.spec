TYPE Node = {id: ID, role: Role, ts: Time}
TYPE Role = reply | temporal | bridge
TYPE Edge = {from: ID, to: ID, rel: Role, str: Float[0,1], cnt: Int}
TYPE Graph = {nodes: Node[], edges: Edge[], clusters: Cluster[], meta: Map}
TYPE Cluster = {id: ID, type: Role, nodes: ID[], conns: Edge[], stab: Float}
TYPE ThreeClusterGraph = {A: Cluster, B: Cluster, C: Cluster}
TYPE Trajectory = {start: ID, steps: Int, path: ID[], term: ID, cycle: Cycle?, att: Attractor?}
TYPE EventSelection = {curr: ID, edge: Edge, str: Float, alts: Edge[]}
TYPE Cycle = {id: ID, nodes: ID[], len: Int, freq: Int, stab: Float, type: Role}
TYPE CycleResult = {cycles: Cycle[], periodic: Bool, period: Int}
TYPE SCC = {id: ID, nodes: ID[], reach: Bool, is_att: Bool, stable: Bool}
TYPE SCCResult = {comps: SCC[], conn_score: Float}
TYPE Attractor = {id: ID, type: cycle | fixed, nodes: ID[], stab: Float, rec: Int}
TYPE Basin = {att: Attractor, nodes: ID[], mass: Int, ratio: Float[0,1], cov: Area}
TYPE BasinResult = {basins: Basin[], total_att: Int, conv_rate: Float}

OP next_event(g: Graph, n: Node, e: Event) -> EventSelection
OP rollout*(g: Graph, n: Node, max_s: Int, thresh: Float) -> Trajectory
OP find_cycle(t: Trajectory) -> Cycle
OP find_recurrent_cycle(t: Trajectory) -> CycleResult
OP find_attractor(t: Trajectory) -> Attractor
OP analyze_scc(g: Graph) -> SCCResult
OP build_basin_map(g: Graph, atts: Attractor[]) -> Basin[]
OP build_basin_structure(bs: Basin[]) -> BasinResult

INV SCC.is_att == False
INV SCC -> Attractor IF SCC.stable > STAB_THRESH
INV Basin.mass == len(Basin.nodes)
INV Basin.ratio == Basin.mass / len(Graph.nodes)
INV Cluster.type == reply IF recurrence > HIGH
INV Cluster.type == temporal IF stability < LOW
INV Cluster.type == bridge IF conns > 1_cluster
INV Stability == cycle_reappearance / total_obs
PRE rollout* requires Graph.connectedness > 0
POST Trajectory.term IN Graph.nodes
POST Trajectory.path[0] == Trajectory.start
POST Trajectory.path[end] == Trajectory.term

MAP WorldState -> Node
MAP Event -> Edge
MAP Trace -> Trajectory