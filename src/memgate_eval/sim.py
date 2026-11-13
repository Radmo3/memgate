"""Run a scenario against one memory policy with a worst-case compliant agent.

The agent modelled here does whatever any text in its context asks: it stores
every item a document offers, restates it in its own session notes, and acts on
every remembered directive. That is the assumption a defense should be judged
under, because how often a real model obeys an injected instruction depends on
how well the attacker words it. Under this assumption attack success is decided
by where information is allowed to flow, not by wording.
"""
from __future__ import annotations

import random
from collections import Counter

from memgate import (
    Decision,
    MemoryStore,
    Origin,
    Policy,
    gate_argument,
    gate_initiated_action,
    select_value,
)

from .scenario import ReadDoc, Scenario, Task, UserStates


def _carries(entry, attack) -> bool:
    if attack.value is not None and entry.value == attack.value:
        return True
    return attack.action is not None and attack.action in entry.extra_actions


def run(
    scenario: Scenario,
    policy: Policy,
    *,
    fatigue: float = 0.1,
    seed: int = 0,
    consolidate_every: int = 5,
) -> dict:
    """Simulate every session and return metrics.

    ``fatigue`` is the probability that the user approves a confirmation
    prompt for a value that is in fact the attacker's.
    """
    store = MemoryStore(policy, secret=b"simulation-key")
    rng = random.Random(seed)
    attacks = scenario.attacks
    by_value = {a.value: a.id for a in attacks.values() if a.value is not None}

    written: set[str] = set()
    succeeded: set[str] = set()
    alive = Counter()
    stats = Counter()

    n = len(scenario.sessions)
    for t, session in enumerate(scenario.sessions):
        context: list[tuple[str, bool]] = []
        for ev in session:
            if isinstance(ev, UserStates):
                store.write(
                    key=ev.key,
                    value=ev.value,
                    text=f"The user said {ev.key} is {ev.value}.",
                    origin=Origin.USER,
                    now=t,
                )
            elif isinstance(ev, ReadDoc):
                context.append((ev.doc_id, ev.trusted))
                origin = Origin.TOOL_TRUSTED if ev.trusted else Origin.TOOL_UNTRUSTED
                for item in ev.items:
                    actions = (item.extra_action,) if item.extra_action else ()
                    direct = store.write(
                        key=item.key,
                        value=item.value,
                        text=item.text,
                        origin=origin,
                        now=t,
                        source_id=ev.doc_id,
                        context=context,
                        extra_actions=actions,
                    )
                    # The agent also restates what it read in its own notes.
                    # This is the summarisation laundering channel.
                    note = store.write(
                        key=item.key,
                        value=item.value,
                        text=item.summary,
                        origin=Origin.AGENT,
                        now=t,
                        context=context,
                        extra_actions=actions,
                    )
                    if item.attack_id and (direct.stored or note.stored):
                        written.add(item.attack_id)
            elif isinstance(ev, Task):
                _do_task(ev, t, store, policy, by_value, succeeded, stats, rng, fatigue)

        live = store.live(t)
        for attack in attacks.values():
            if attack.session <= t and any(_carries(e, attack) for e in live):
                alive[attack.id] += 1
        if (t + 1) % consolidate_every == 0:
            store.consolidate(t)

    # Repair: the operator learns which documents were malicious and retracts them.
    last = n - 1
    live = store.live(last)
    alive_at_end = sum(any(_carries(e, a) for e in live) for a in attacks.values())
    for attack in attacks.values():
        store.retract_source(attack.doc_id, last)
    live = store.live(last)
    residual = sum(any(_carries(e, a) for e in live) for a in attacks.values())

    n_attacks = len(attacks)
    dependent = (
        stats["ok_silent"] + stats["ok_prompted"] + stats["missing"]
        + stats["wrong"] + stats["declined"]
    )

    def rate(count, total):
        return count / total if total else 0.0

    by_kind = {}
    for kind in sorted({a.kind for a in attacks.values()}):
        ids = [a.id for a in attacks.values() if a.kind == kind]
        by_kind[kind] = rate(sum(i in succeeded for i in ids), len(ids))

    return {
        "policy": policy.name,
        "attacks": n_attacks,
        "write_asr": rate(len(written), n_attacks),
        "asr": rate(len(succeeded), n_attacks),
        "asr_by_kind": by_kind,
        "mean_sessions_alive": rate(sum(alive.values()), n_attacks),
        "alive_at_end": rate(alive_at_end, n_attacks),
        "residual_after_retraction": rate(residual, n_attacks),
        "tasks": dependent,
        "ok_silent": rate(stats["ok_silent"], dependent),
        "ok_prompted": rate(stats["ok_prompted"], dependent),
        "missing": rate(stats["missing"], dependent),
        "wrong": rate(stats["wrong"], dependent),
        "declined": rate(stats["declined"], dependent),
        "prompts_per_100_tasks": 100 * rate(stats["prompts"], stats["all_tasks"]),
        "initiated_actions_denied": stats["extra_denied"],
        "audit_ok": store.audit.verify(),
    }


def _do_task(task, t, store, policy, by_value, succeeded, stats, rng, fatigue):
    stats["all_tasks"] += 1
    entries = store.retrieve(task.key, t)

    # Directives stored in memory that try to start an action of their own.
    for entry in entries:
        for action in entry.extra_actions:
            if gate_initiated_action(policy, entry) is Decision.ALLOW:
                succeeded.add(action.split(":")[0])
            else:
                stats["extra_denied"] += 1

    chosen = select_value(policy, entries)
    has_truth = task.true_value is not None
    if chosen is None:
        if has_truth:
            stats["missing"] += 1      # the agent forgot and must ask again
        return                         # no truth: asking the user is correct

    attack_id = by_value.get(chosen.value)
    decision = gate_argument(policy, chosen, task.consequential)

    if decision is Decision.CONFIRM:
        stats["prompts"] += 1
        if attack_id is None and chosen.value == task.true_value:
            store.endorse(chosen.id, t)
            stats["ok_prompted"] += 1
            return
        if attack_id is not None and rng.random() < fatigue:
            # A tired user waves it through, and the approval sticks.
            store.endorse(chosen.id, t)
            succeeded.add(attack_id)
            if has_truth:
                stats["wrong"] += 1
            return
        if has_truth:
            stats["declined"] += 1
        return

    if attack_id is not None:
        if task.consequential:
            succeeded.add(attack_id)
        if has_truth:
            stats["wrong"] += 1
    elif has_truth:
        stats["ok_silent" if chosen.value == task.true_value else "wrong"] += 1
