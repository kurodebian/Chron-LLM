import pytest


class WAL:
    def __init__(self):
        self.store = []


class Graph:
    def __init__(self):
        self.store = []


class WorldHead:
    def __init__(self):
        self.heads = {}


def gen_event_id(parent_id, world_id, typ, payload_ref, schema_version):
    return f"H-{parent_id}-{world_id}-{typ}-{payload_ref}-{schema_version}"


def gen_causal_id(parent_causal_id, world_id, typ, payload_ref, schema_version):
    return f"C-{parent_causal_id}-{world_id}-{typ}-{payload_ref}-{schema_version}"


def commit(candidate, wal, graph, worldhead, memory):
    # PRE: payload exists
    if candidate["payload_ref"] not in memory:
        return {"status": "rejected", "reason": "missing-payload"}
    # PRE: parent exists or is ROOT
    if candidate["parent_id"] != "ROOT" and candidate["parent_id"] not in [
        e["event_id"] for e in graph.store
    ]:
        return {"status": "rejected", "reason": "invalid-parent"}
    eid = gen_event_id(
        candidate["parent_id"],
        candidate["world_id"],
        candidate["type"],
        candidate["payload_ref"],
        candidate["schema_version"],
    )
    cid = gen_causal_id(
        "parentC",
        candidate["world_id"],
        candidate["type"],
        candidate["payload_ref"],
        candidate["schema_version"],
    )
    ce = {
        "event_id": eid,
        "causal_id": cid,
        "parent_id": candidate["parent_id"],
        "world_id": candidate["world_id"],
        "type": candidate["type"],
        "payload_ref": candidate["payload_ref"],
        "schema_version": candidate["schema_version"],
    }
    wal.store.append(ce)
    graph.store.append(ce)
    worldhead.heads[candidate["world_id"]] = ce
    return {
        "status": "committed",
        "event_id": eid,
        "causal_id": cid,
        "world_id": candidate["world_id"],
    }


def test_valid_commit():
    wal = WAL()
    graph = Graph()
    worldhead = WorldHead()
    memory = {"p1": "payload"}
    candidate = {
        "parent_id": "ROOT",
        "world_id": "w1",
        "type": "T",
        "payload_ref": "p1",
        "schema_version": 1,
    }
    res = commit(candidate, wal, graph, worldhead, memory)
    assert res["status"] == "committed"
    assert len(graph.store) == 1
    assert graph.store[0]["event_id"] == res["event_id"]


def test_invalid_parent_rejected():
    wal = WAL()
    graph = Graph()
    worldhead = WorldHead()
    memory = {"p1": "payload"}
    candidate = {
        "parent_id": "nonexistent",
        "world_id": "w1",
        "type": "T",
        "payload_ref": "p1",
        "schema_version": 1,
    }
    res = commit(candidate, wal, graph, worldhead, memory)
    assert res["status"] == "rejected"


def test_idempotency_like_behavior():
    wal = WAL()
    graph = Graph()
    worldhead = WorldHead()
    memory = {"p1": "payload"}
    candidate = {
        "parent_id": "ROOT",
        "world_id": "w1",
        "type": "T",
        "payload_ref": "p1",
        "schema_version": 1,
    }
    r1 = commit(candidate, wal, graph, worldhead, memory)
    r2 = commit(candidate, wal, graph, worldhead, memory)
    assert r1["status"] == "committed"
    assert r2["status"] == "committed"
