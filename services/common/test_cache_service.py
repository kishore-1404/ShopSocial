import logging

from common.cache_service import CacheClient


def test_delete_prefix_removes_all_matching_memory_entries():
    client = CacheClient(redis_url=None)

    client.set_json("chat:history:1:50", [{"a": 1}], ttl_seconds=30)
    client.set_json("chat:history:1:100", [{"a": 2}], ttl_seconds=30)
    client.set_json("chat:history:2:50", [{"a": 3}], ttl_seconds=30)

    client.delete_prefix("chat:history:1:")

    assert client.get_json("chat:history:1:50") is None
    assert client.get_json("chat:history:1:100") is None
    assert client.get_json("chat:history:2:50") == [{"a": 3}]


def test_delete_prefix_emits_debug_metrics(caplog):
    client = CacheClient(redis_url=None)
    client.set_json("chat:history:1:50", [{"a": 1}], ttl_seconds=30)

    with caplog.at_level(logging.DEBUG):
        client.delete_prefix("chat:history:1:")

    records = [r for r in caplog.records if r.message == "cache_prefix_invalidation"]
    assert records
    record = records[-1]
    assert getattr(record, "event", None) == "cache_prefix_invalidation"
    assert getattr(record, "cache_prefix", None) == "chat:history:1:"
    assert getattr(record, "memory_deleted", None) == 1
    assert getattr(record, "duration_ms", None) >= 0


def test_delete_prefix_does_not_emit_debug_metrics_when_disabled(caplog):
    client = CacheClient(redis_url=None, prefix_invalidation_debug_enabled=False)
    client.set_json("chat:history:1:50", [{"a": 1}], ttl_seconds=30)

    with caplog.at_level(logging.DEBUG):
        client.delete_prefix("chat:history:1:")

    records = [r for r in caplog.records if r.message == "cache_prefix_invalidation"]
    assert not records


def test_delete_prefix_sampling_skips_debug_event(caplog, monkeypatch):
    client = CacheClient(redis_url=None, prefix_invalidation_debug_sample_rate=0.1)
    client.set_json("chat:history:1:50", [{"a": 1}], ttl_seconds=30)
    monkeypatch.setattr("common.cache_service.random.random", lambda: 0.9)

    with caplog.at_level(logging.DEBUG):
        client.delete_prefix("chat:history:1:")

    records = [r for r in caplog.records if r.message == "cache_prefix_invalidation"]
    assert not records


def test_delete_prefix_sampling_emits_debug_event(caplog, monkeypatch):
    client = CacheClient(redis_url=None, prefix_invalidation_debug_sample_rate=0.1)
    client.set_json("chat:history:1:50", [{"a": 1}], ttl_seconds=30)
    monkeypatch.setattr("common.cache_service.random.random", lambda: 0.01)

    with caplog.at_level(logging.DEBUG):
        client.delete_prefix("chat:history:1:")

    records = [r for r in caplog.records if r.message == "cache_prefix_invalidation"]
    assert records
