"""Policies: what a memory system does on write, on consolidation and at action time.

Every baseline and the full defense are the same store with different flags, so
an ablation changes one mechanism at a time.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from .entry import MemoryEntry, Trust


@dataclass(frozen=True)
class Policy:
    name: str
    # Write path
    content_filter: bool = False          # in-band keyword filter (weak baseline)
    track_taint: bool = False             # runtime-computed provenance, propagated
    sign_entries: bool = False            # HMAC over content and provenance
    # Lifecycle
    untrusted_ttl: int | None = None   # sessions an untrusted entry may live
    ttl_survives_consolidation: bool = False
    partition_consolidation: bool = False  # never merge across trust levels
    # Action time
    trusted_wins_conflicts: bool = False
    deny_untrusted_initiated_actions: bool = False
    confirm_untrusted_args: bool = False


def presets(ttl: int = 20) -> dict[str, Policy]:
    return {
        "none": Policy("none"),
        "filter": Policy("filter", content_filter=True),
        "ttl": Policy("ttl", untrusted_ttl=ttl),
        "taint": Policy(
            "taint",
            track_taint=True,
            sign_entries=True,
            untrusted_ttl=ttl,
            ttl_survives_consolidation=True,
        ),
        "full": Policy(
            "full",
            track_taint=True,
            sign_entries=True,
            untrusted_ttl=ttl,
            ttl_survives_consolidation=True,
            partition_consolidation=True,
            trusted_wins_conflicts=True,
            deny_untrusted_initiated_actions=True,
            confirm_untrusted_args=True,
        ),
    }


class Decision(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"   # show provenance to the user and wait for a yes
    DENY = "deny"


def select_value(policy: Policy, entries: Sequence[MemoryEntry]) -> MemoryEntry | None:
    """Pick which remembered value an action will use.

    Without the conflict rule the most recent value wins, which is how
    recency-based memory updates behave and is the attacker-favourable case.
    With it, a value the user stated always outranks one that did not come
    from the user, however recent.
    """
    valued = [e for e in entries if e.value is not None]
    if not valued:
        return None
    if policy.trusted_wins_conflicts:
        trusted = [e for e in valued if e.trust is Trust.TRUSTED]
        if trusted:
            return trusted[-1]
    return valued[-1]


def resolve_value(
    policy: Policy, entries: Sequence[MemoryEntry], proposed: MemoryEntry | None
) -> MemoryEntry | None:
    """Decide which entry's value an action uses, given what the agent proposed.

    When the conflict rule is on and the user has stated a value, the runtime
    uses that value regardless of which memory the agent asked for. If the agent
    proposed nothing, it is asking the user, and that is respected.
    """
    if proposed is None:
        return None
    if policy.trusted_wins_conflicts:
        trusted = [e for e in entries if e.value is not None and e.trust is Trust.TRUSTED]
        if trusted:
            return trusted[-1]
    return proposed


def gate_argument(policy: Policy, entry: MemoryEntry, consequential: bool) -> Decision:
    """May a user-requested action use this entry's value as an argument?"""
    if policy.confirm_untrusted_args and consequential and entry.trust is Trust.UNTRUSTED:
        return Decision.CONFIRM
    return Decision.ALLOW


def gate_initiated_action(
    policy: Policy,
    entry: MemoryEntry | None,
    context: Sequence[MemoryEntry] = (),
) -> Decision:
    """May the agent start an action the user did not ask for in this session?

    ``entry`` is the memory the agent says prompted the action. If the agent
    gives none, the action is judged by everything it could see: one untrusted
    entry in ``context`` is enough to deny it.
    """
    if not policy.deny_untrusted_initiated_actions:
        return Decision.ALLOW
    if entry is not None:
        return Decision.DENY if entry.trust is Trust.UNTRUSTED else Decision.ALLOW
    if any(e.trust is Trust.UNTRUSTED for e in context):
        return Decision.DENY
    return Decision.ALLOW
