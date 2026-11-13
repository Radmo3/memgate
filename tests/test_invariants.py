"""Seeded fuzzing of the security invariants over random workloads and settings."""
import random

import pytest

from memgate import MemoryStore, Origin, Trust, presets
from memgate_eval import generate, run

CASES = 60


def random_setup(case: int):
    rng = random.Random(1000 + case)
    scenario = generate(
        case,
        n_sessions=rng.randint(12, 90),
        n_prefs=rng.randint(3, 25),
        n_facts=rng.randint(0, 20),
        n_attacks=rng.randint(1, 40),
        max_delay=rng.randint(1, 60),
    )
    policy = presets(ttl=rng.randint(1, 50))["full"]
    return scenario, policy, rng.randint(1, 9)


@pytest.mark.parametrize("case", range(CASES))
def test_full_policy_invariants(case):
    scenario, policy, every = random_setup(case)

    careful = run(scenario, policy, fatigue=0.0, seed=case, consolidate_every=every)
    assert careful["asr"] == 0.0                       # nothing gets through a careful user
    assert careful["wrong"] == 0.0                     # no attacker value is ever used
    assert careful["residual_after_retraction"] == 0.0  # repair leaves nothing behind
    assert careful["audit_ok"]

    careless = run(scenario, policy, fatigue=1.0, seed=case, consolidate_every=every)
    assert careless["asr_by_kind"].get("extra_action", 0.0) == 0.0  # never depends on the user
    assert careless["asr_by_kind"].get("override", 0.0) == 0.0
    assert careless["residual_after_retraction"] == 0.0


@pytest.mark.parametrize("case", range(CASES))
def test_taint_never_decreases_through_notes_and_merges(case):
    rng = random.Random(case)
    store = MemoryStore(presets(ttl=rng.randint(5, 30))["taint"])
    tainted_keys = set()
    for t in range(40):
        key = f"k{rng.randrange(6)}"
        untrusted_doc = rng.random() < 0.4
        context = [(f"doc{t}", not untrusted_doc)]
        origin = rng.choice([Origin.USER, Origin.AGENT, Origin.TOOL_UNTRUSTED])
        entry = store.write(
            key=key, value=f"v{t}", text=f"{key} is v{t}", origin=origin, now=t,
            source_id=f"doc{t}" if origin is Origin.TOOL_UNTRUSTED else None, context=context,
        ).entry
        if entry.trust is Trust.UNTRUSTED:
            tainted_keys.add(key)
        if rng.random() < 0.3:
            before = {e.key for e in store.live(t) if e.trust is Trust.UNTRUSTED}
            store.consolidate(t)
            after = {e.key for e in store.live(t) if e.trust is Trust.UNTRUSTED}
            assert before <= after   # a merge never launders an untrusted key clean
    for e in store.live(39):
        if e.trust is Trust.UNTRUSTED:
            assert e.sources and e.expires is not None
