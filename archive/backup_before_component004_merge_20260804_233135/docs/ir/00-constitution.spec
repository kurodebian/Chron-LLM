TYPE Canonical : Authoritative
TYPE Working : Ephemeral | NonAuthoritative
TYPE Derived : Deterministic | Reproducible | NonAuthoritative
TYPE External : NonAuthoritative
TYPE Event : id, payload, meta
TYPE Evidence = List[Event]
TYPE Candidate : Proposal | NonAuthoritative

OP Commit(Canonical, Evidence) -> Canonical'
OP Derive(Canonical) -> Derived

INV Canonical.authoritative == true
INV Working.authoritative == false
INV Derived.authoritative == false
INV External.authoritative == false
INV Candidate.authoritative == false
INV Evidence.causal_order == true
INV Mutate(Canonical) => Op == Commit
INV Derived != Canonical
INV Rejected(Candidate) -> Canonical_preserved
INV Deferred(Candidate) -> Canonical_preserved
PRE Derive : Pure | Deterministic