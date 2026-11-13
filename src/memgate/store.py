"""The memory store: write, retrieve, consolidate, expire, retract, endorse.

The store is part of the trusted runtime. The model never chooses an entry's
origin, trust level or source list; the runtime computes them from the channel
the content arrived on and from everything that was in context at write time.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from .entry import MemoryEntry, Origin, Status, Trust
from .policy import Policy

# The in-band baseline: block text that "looks like" an instruction.
FILTER_RE = re.compile(
    r"\b(remember|always|never|ignore|from now on|must|do not tell)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class WriteResult:
    entry: Optional[MemoryEntry]
    reason: str = "stored"

    @property
    def stored(self) -> bool:
        return self.entry is not None


class AuditLog:
    """Append-only, hash-chained record of every change to the store."""

    def __init__(self) -> None:
        self.records: list[dict] = []
        self._head = "0" * 64

    def append(self, event: str, **fields) -> None:
        body = {"event": event, **fields, "prev": self._head}
        digest = hashlib.sha256(
            json.dumps(body, sort_keys=True, default=str).encode()
        ).hexdigest()
        self.records.append({**body, "hash": digest})
        self._head = digest

    def verify(self) -> bool:
        prev = "0" * 64
        for rec in self.records:
            body = {k: v for k, v in rec.items() if k != "hash"}
            if body["prev"] != prev:
                return False
            digest = hashlib.sha256(
                json.dumps(body, sort_keys=True, default=str).encode()
            ).hexdigest()
            if digest != rec["hash"]:
                return False
            prev = digest
        return True


class MemoryStore:
    def __init__(self, policy: Policy, secret: Optional[bytes] = None) -> None:
        self.policy = policy
        self._secret = secret if secret is not None else os.urandom(32)
        self._entries: dict[str, MemoryEntry] = {}
        self._counter = 0
        self.audit = AuditLog()

    # ------------------------------------------------------------------ helpers
    def _new_id(self) -> str:
        self._counter += 1
        return f"m{self._counter:06d}"

    def _sign(self, entry: MemoryEntry) -> str:
        return hmac.new(self._secret, entry.canonical(), hashlib.sha256).hexdigest()

    def _valid(self, entry: MemoryEntry) -> bool:
        if not self.policy.sign_entries:
            return True
        return hmac.compare_digest(entry.sig, self._sign(entry))

    def _add(self, entry: MemoryEntry, event: str) -> MemoryEntry:
        if self.policy.sign_entries:
            entry.sig = self._sign(entry)
        self._entries[entry.id] = entry
        self.audit.append(
            event,
            id=entry.id,
            key=entry.key,
            origin=entry.origin.value,
            trust=int(entry.trust),
            sources=sorted(entry.sources),
            at=entry.created,
        )
        return entry

    # -------------------------------------------------------------------- write
    def write(
        self,
        *,
        key: str,
        value: Optional[str],
        text: str,
        origin: Origin,
        now: int,
        source_id: Optional[str] = None,
        context: Iterable[tuple[str, bool]] = (),
        parents: Sequence[str] = (),
        extra_actions: Sequence[str] = (),
    ) -> WriteResult:
        """Store a memory.

        ``context`` lists every external source read so far in the session as
        ``(source_id, trusted)`` pairs. It is supplied by the runtime.
        """
        if self.policy.content_filter and FILTER_RE.search(text):
            self.audit.append("write_filtered", key=key, at=now)
            return WriteResult(None, "filtered")

        parent_entries = [self._entries[p] for p in parents]
        trust, sources = self._label(origin, source_id, context, parent_entries)
        entry = MemoryEntry(
            id=self._new_id(),
            key=key,
            value=value,
            text=text,
            origin=origin,
            trust=trust,
            sources=sources,
            parents=tuple(parents) if self.policy.track_taint else (),
            created=now,
            expires=self._expiry(origin, trust, now),
            extra_actions=tuple(extra_actions),
        )
        return WriteResult(self._add(entry, "write"))

    def _label(self, origin, source_id, context, parent_entries):
        if not self.policy.track_taint:
            # A system without provenance tracking treats every entry alike. It
            # still knows which document a direct tool write came from.
            direct = origin in (Origin.TOOL_UNTRUSTED, Origin.TOOL_TRUSTED)
            return Trust.TRUSTED, frozenset([source_id] if direct and source_id else [])

        sources: set[str] = set()
        untrusted = origin is Origin.TOOL_UNTRUSTED
        if source_id:
            sources.add(source_id)
        for parent in parent_entries:
            sources |= parent.sources
            untrusted = untrusted or parent.trust is Trust.UNTRUSTED
        if origin is not Origin.USER:
            # Anything the model writes after reading untrusted content may have
            # been steered by it. User statements are captured verbatim by the
            # runtime, so they keep their own label.
            for sid, trusted in context:
                if not trusted:
                    untrusted = True
                    sources.add(sid)
        return (Trust.UNTRUSTED if untrusted else Trust.TRUSTED), frozenset(sources)

    def _expiry(self, origin: Origin, trust: Trust, now: int) -> Optional[int]:
        ttl = self.policy.untrusted_ttl
        if ttl is None:
            return None
        if self.policy.track_taint:
            return now + ttl if trust is Trust.UNTRUSTED else None
        return now + ttl if origin is Origin.TOOL_UNTRUSTED else None

    # --------------------------------------------------------------------- read
    def expire(self, now: int) -> None:
        for entry in self._entries.values():
            if (
                entry.status is Status.ACTIVE
                and entry.expires is not None
                and now >= entry.expires
            ):
                entry.status = Status.EXPIRED
                self.audit.append("expire", id=entry.id, at=now)

    def live(self, now: int) -> list[MemoryEntry]:
        """Every entry that could currently be retrieved, oldest first."""
        self.expire(now)
        out = [
            e
            for e in self._entries.values()
            if e.status is Status.ACTIVE and self._valid(e)
        ]
        return sorted(out, key=lambda e: (e.created, e.id))

    def retrieve(self, key: str, now: int) -> list[MemoryEntry]:
        return [e for e in self.live(now) if e.key == key]

    def get(self, entry_id: str) -> MemoryEntry:
        return self._entries[entry_id]

    # -------------------------------------------------------------- consolidate
    def consolidate(self, now: int) -> int:
        """Merge entries about the same key. Returns how many merges happened."""
        groups: dict[tuple, list[MemoryEntry]] = {}
        for entry in self.live(now):
            part = int(entry.trust) if self.policy.partition_consolidation else -1
            groups.setdefault((entry.key, part), []).append(entry)

        merges = 0
        for (key, _), group in groups.items():
            if len(group) < 2:
                continue
            valued = [e for e in group if e.value is not None]
            latest = valued[-1] if valued else None
            actions: list[str] = []
            for e in group:
                for a in e.extra_actions:
                    if a not in actions:
                        actions.append(a)

            if self.policy.track_taint:
                trust = min(e.trust for e in group)
                sources = frozenset().union(*(e.sources for e in group))
                parents = tuple(e.id for e in group)
                expiries = [e.expires for e in group if e.expires is not None]
                expires = (
                    min(expiries)
                    if expiries and self.policy.ttl_survives_consolidation
                    else None
                )
            else:
                # No lineage: the merged entry looks like a fresh note of the
                # agent's own, with no source and no expiry.
                trust, sources, parents, expires = Trust.TRUSTED, frozenset(), (), None

            merged = MemoryEntry(
                id=self._new_id(),
                key=key,
                value=latest.value if latest else None,
                text=latest.text if latest else "",
                origin=Origin.DERIVED,
                trust=Trust(trust),
                sources=sources,
                parents=parents,
                created=now,
                expires=expires,
                extra_actions=tuple(actions),
            )
            for e in group:
                e.status = Status.SUPERSEDED
            self._add(merged, "consolidate")
            merges += 1
        return merges

    # ------------------------------------------------------------------- repair
    def retract_source(self, source_id: str, now: int) -> int:
        """Remove everything a source influenced. Returns the number retracted."""
        count = 0
        for entry in self._entries.values():
            if entry.status is Status.ACTIVE and source_id in entry.sources:
                entry.status = Status.RETRACTED
                self.audit.append("retract", id=entry.id, source=source_id, at=now)
                count += 1
        return count

    def endorse(self, entry_id: str, now: int) -> MemoryEntry:
        """The user confirmed this value. Re-issue it as a user-origin entry.

        Only the value is endorsed. Any actions the old entry asked for are
        dropped, because the user approved a fact, not a standing instruction.
        The source list is kept, so that if a source is later found to be
        malicious, values the user was talked into approving are retracted too.
        """
        old = self._entries[entry_id]
        new = MemoryEntry(
            id=self._new_id(),
            key=old.key,
            value=old.value,
            text=old.text,
            origin=Origin.USER,
            trust=Trust.TRUSTED,
            sources=old.sources,
            parents=(old.id,),
            created=now,
            expires=None,
        )
        old.status = Status.SUPERSEDED
        return self._add(new, "endorse")
