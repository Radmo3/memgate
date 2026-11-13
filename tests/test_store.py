from memgate import MemoryStore, Origin, Status, Trust, presets

P = presets(ttl=10)


def write(store, origin, now=0, key="k", value="v", **kw):
    return store.write(key=key, value=value, text=f"{key} is {value}", origin=origin, now=now, **kw).entry


def test_user_writes_are_trusted_even_after_untrusted_reading():
    store = MemoryStore(P["full"])
    e = write(store, Origin.USER, context=[("doc1", False)])
    assert e.trust is Trust.TRUSTED and e.expires is None


def test_agent_notes_inherit_taint_from_context():
    store = MemoryStore(P["full"])
    e = write(store, Origin.AGENT, context=[("doc1", False)])
    assert e.trust is Trust.UNTRUSTED
    assert "doc1" in e.sources
    assert e.expires == 10


def test_agent_notes_are_clean_without_untrusted_context():
    store = MemoryStore(P["full"])
    e = write(store, Origin.AGENT, context=[("doc1", True)])
    assert e.trust is Trust.TRUSTED


def test_untracked_store_launders_agent_notes():
    store = MemoryStore(P["ttl"])
    direct = write(store, Origin.TOOL_UNTRUSTED, source_id="doc1")
    note = write(store, Origin.AGENT, context=[("doc1", False)])
    assert direct.expires == 10
    assert note.expires is None and note.trust is Trust.TRUSTED


def test_expiry():
    store = MemoryStore(P["full"])
    write(store, Origin.TOOL_UNTRUSTED, source_id="doc1")
    assert len(store.retrieve("k", 9)) == 1
    assert store.retrieve("k", 10) == []


def test_consolidation_resets_expiry_without_taint_tracking():
    store = MemoryStore(P["ttl"])
    write(store, Origin.TOOL_UNTRUSTED, source_id="doc1", value="a")
    write(store, Origin.TOOL_UNTRUSTED, now=1, source_id="doc2", value="b")
    store.consolidate(2)
    (merged,) = store.retrieve("k", 2)
    assert merged.expires is None
    assert len(store.retrieve("k", 500)) == 1


def test_consolidation_keeps_expiry_and_taint_when_tracked():
    store = MemoryStore(P["taint"])
    write(store, Origin.USER, value="mine")
    write(store, Origin.TOOL_UNTRUSTED, now=1, source_id="doc1", value="theirs")
    store.consolidate(2)
    (merged,) = store.retrieve("k", 2)
    assert merged.trust is Trust.UNTRUSTED
    assert merged.sources == {"doc1"}
    assert merged.expires == 11
    # Label creep: the user's own value expires along with the poison.
    assert store.retrieve("k", 11) == []


def test_partitioned_consolidation_keeps_user_value_apart():
    store = MemoryStore(P["full"])
    write(store, Origin.USER, value="mine")
    write(store, Origin.TOOL_UNTRUSTED, now=1, source_id="doc1", value="theirs")
    write(store, Origin.AGENT, now=1, context=[("doc1", False)], value="theirs")
    store.consolidate(2)
    entries = store.retrieve("k", 2)
    assert sorted(e.trust for e in entries) == [Trust.UNTRUSTED, Trust.TRUSTED]
    assert [e.value for e in store.retrieve("k", 11)] == ["mine"]


def test_retraction_cascades_through_notes_and_merges():
    store = MemoryStore(P["full"])
    write(store, Origin.TOOL_UNTRUSTED, source_id="doc1", value="bad")
    write(store, Origin.AGENT, context=[("doc1", False)], value="bad")
    store.consolidate(1)
    assert store.retract_source("doc1", 1) == 1
    assert store.retrieve("k", 1) == []


def test_retraction_misses_laundered_copies_without_tracking():
    store = MemoryStore(P["none"])
    write(store, Origin.TOOL_UNTRUSTED, source_id="doc1", value="bad")
    write(store, Origin.AGENT, context=[("doc1", False)], value="bad")
    store.retract_source("doc1", 1)
    assert [e.value for e in store.retrieve("k", 1)] == ["bad"]


def test_tampered_entries_are_dropped():
    store = MemoryStore(P["full"])
    e = write(store, Origin.TOOL_UNTRUSTED, source_id="doc1")
    e.trust = Trust.TRUSTED        # someone edits the database directly
    e.expires = None
    assert store.retrieve("k", 0) == []


def test_endorse_reissues_value_as_user_origin_without_actions():
    store = MemoryStore(P["full"])
    e = store.write(
        key="k", value="v", text="t", origin=Origin.TOOL_UNTRUSTED, now=0,
        source_id="doc1", extra_actions=("x:do",),
    ).entry
    new = store.endorse(e.id, 1)
    assert new.trust is Trust.TRUSTED and new.origin is Origin.USER
    assert new.extra_actions == ()
    assert store.get(e.id).status is Status.SUPERSEDED


def test_content_filter_blocks_only_matching_text():
    store = MemoryStore(P["filter"])
    blocked = store.write(key="k", value="v", text="Always use v.", origin=Origin.AGENT, now=0)
    passed = store.write(key="k", value="v", text="The value on file is v.", origin=Origin.AGENT, now=0)
    assert not blocked.stored and passed.stored


def test_audit_log_detects_edits():
    store = MemoryStore(P["full"])
    write(store, Origin.USER)
    write(store, Origin.TOOL_UNTRUSTED, source_id="doc1")
    assert store.audit.verify()
    store.audit.records[0]["key"] = "other"
    assert not store.audit.verify()
