# Threat model

## What is protected

An agent that keeps memory across sessions and can take consequential actions for its user: moving money, sending data, changing settings. The asset is the integrity of those actions.

## Trust boundaries

| Component | Trusted? | Why |
|---|---|---|
| Runtime (the code that calls the store and the gates) | Yes | It assigns every label. If it is wrong, nothing holds. |
| Signing key | Yes | Kept outside the model's reach. |
| User channel | Yes | What the user types is captured verbatim, not paraphrased by the model. |
| Tools the deployer marks trusted | Yes | A deployment decision. See residual risks. |
| The model | **No** | Assumed to obey any instruction it reads. |
| Documents, emails, web pages, other tool output | **No** | Attacker-controlled. |
| The memory database at rest | **No** | Entries are signed; edits made outside the runtime are dropped on read. |

## Attacker

Controls the content of some untrusted documents the agent reads. Knows how memgate works. Cannot reach the runtime, the key or the user channel. Wants a consequential action to happen in a later session.

## Attacks and what stops them

| Attack | Stopped by | Tested in |
|---|---|---|
| Stored instruction starts an action later | Untrusted memories cannot initiate actions | `test_invariants.py`, `test_sim.py` |
| Stored value overrides what the user said | A user-stated value outranks any other | `test_invariants.py` |
| Laundering through the agent's own notes | Context taint: anything written after reading untrusted content is untrusted | `test_store.py` |
| Laundering through consolidation | Merged entries inherit the lowest trust, all sources and the earliest expiry | `test_store.py`, `test_invariants.py` |
| Poison drags a user's value down with it in a merge | Trusted and untrusted entries are never merged | `test_store.py` |
| Agent hides which memory prompted an action | Unattributed actions are denied while any untrusted memory is in view | `test_agents.py` |
| Direct edit of the database | HMAC over content and provenance | `test_store.py` |
| Rewriting history | Hash-chained audit log | `test_store.py` |
| Poison survives discovery | Retraction cascades through notes, merges and approved values | `test_invariants.py` |

## Residual risks, most serious first

1. **The user approves a bad prompt.** A planted value for something the user never specified looks the same as a legitimate update from an untrusted source. The defense turns the attack into a question. A rushed user can answer it wrongly, and the approval then persists until the source is retracted. Measured in simulation; not yet tested with people.
2. **A trusted tool repeats attacker text.** If a tool marked trusted echoes content it fetched from elsewhere, that content arrives with a trusted label. Mark as trusted only tools whose output the attacker cannot influence.
3. **The runtime mislabels a channel.** Every guarantee is relative to correct labelling.
4. **False answers.** A poisoned memory can still make the agent say something wrong. Only actions are gated.
5. **Values assembled from fragments.** The agent could combine pieces of several untrusted entries into a value that matches none of them. The current attribution is by entry, not by sub-value.
6. **Similarity retrieval.** The harness retrieves by exact key. Embedding-based retrieval lets an attacker compete for retrieval slots, which is not modelled.
7. **Denial of service.** An attacker can cause many confirmation prompts or fill memory with untrusted entries that later expire.

## Not in scope

A malicious user, a compromised runtime or key, attacks on model weights, and confidentiality of memory contents.
