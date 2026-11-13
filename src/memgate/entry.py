"""Memory entries and their labels.

An entry records *what* was remembered and, separately, *where it came from*.
The provenance fields are set by the trusted runtime, never by the model.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional


class Origin(str, Enum):
    """Who directly produced the write."""

    USER = "user"                      # captured verbatim from the user channel
    AGENT = "agent"                    # written by the model (notes, summaries)
    TOOL_TRUSTED = "tool_trusted"      # output of a tool the deployer vouches for
    TOOL_UNTRUSTED = "tool_untrusted"  # web pages, emails, shared documents
    DERIVED = "derived"                # produced by consolidating other entries


class Trust(IntEnum):
    UNTRUSTED = 0
    TRUSTED = 1


class Status(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RETRACTED = "retracted"
    SUPERSEDED = "superseded"


@dataclass
class MemoryEntry:
    id: str
    key: str                      # what the memory is about (retrieval handle)
    value: Optional[str]          # the remembered value; None for pure directives
    text: str                     # natural-language form, as the model would see it
    origin: Origin
    trust: Trust
    sources: frozenset            # ids of every external source that influenced it
    parents: tuple                # ids of entries it was derived from
    created: int
    expires: Optional[int]
    extra_actions: tuple = ()     # actions this memory asks the agent to take
    status: Status = Status.ACTIVE
    sig: str = ""

    def canonical(self) -> bytes:
        """Stable byte encoding of every field covered by the signature.

        ``status`` is left out: retraction and expiry are lifecycle changes made
        by the runtime and recorded in the audit log.
        """
        return json.dumps(
            {
                "id": self.id,
                "key": self.key,
                "value": self.value,
                "text": self.text,
                "origin": self.origin.value,
                "trust": int(self.trust),
                "sources": sorted(self.sources),
                "parents": list(self.parents),
                "created": self.created,
                "expires": self.expires,
                "extra_actions": list(self.extra_actions),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
