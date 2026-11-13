"""memgate: provenance-gated long-term memory for LLM agents."""
from .entry import MemoryEntry, Origin, Status, Trust
from .policy import (
    Decision,
    Policy,
    gate_argument,
    gate_initiated_action,
    presets,
    resolve_value,
    select_value,
)
from .store import AuditLog, MemoryStore, WriteResult

__all__ = [
    "AuditLog",
    "Decision",
    "MemoryEntry",
    "MemoryStore",
    "Origin",
    "Policy",
    "Status",
    "Trust",
    "WriteResult",
    "gate_argument",
    "gate_initiated_action",
    "presets",
    "resolve_value",
    "select_value",
]
__version__ = "0.1.0"
