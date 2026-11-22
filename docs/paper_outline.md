# Paper outline

**Working title:** Ask, Forget, Repair: What Provenance-Gated Agent Memory Costs Over a Long Deployment

**Target:** arXiv cs.CR (primary), cross-list cs.AI. Workshop submission after results from real models.

**Kind of paper:** a measurement study of existing defenses, not a new defense. (Revised 13 Nov 2026 after reading the closest prior work.)

## One-sentence claim

Provenance-gated memory already stops poisoning in published evaluations, but nobody has measured what it costs over a long deployment: how often users are asked to confirm, how much legitimate memory is lost to expiry, and whether poisoned entries can be cleanly repaired afterwards.

## Prior work, after a fuller read

| Prior work | What it covers | What it leaves open |
|---|---|---|
| TMA-NM (2606.24322) | Write-time origin binding, taint through agent summaries and tool calls, untrusted items cannot authorise actions, single-use user authorisation, corroboration by two independent trusted principals, hash-chained log. Tested on eight real models with a defense-aware attack variant. Code and benchmark released. | No expiry or forgetting. No retraction or repair. At most 8 intervening sessions. Its utility figure counts only corroborated actions; it calls confirmation "added friction" whose frequency in deployment is unquantified. |
| PerMIT (2610.28987) | Quarantined reader, confirmation gate, eviction, shared community endorsement, Lean proofs for the single-user core. Tested on Trojan Hippo with live agents. Counts approvals per user in a simulated community. | No expiry. Forgotten facts not measured. Human review time left to a separate study. Code not yet released. Only the first part of this long paper was read. |
| Audience-Bound Persistent Memory (2609.36373) | Labels that survive summaries and merges, across the memory lifecycle | Confidentiality only, not integrity or actions. Expiry and deletion not evaluated. |
| The Price of Safety (2609.22818) | Benign-use cost of four memory defenses: accuracy, token overhead, withheld memories. One backbone, five conversations. | No attacks. No provenance-gated defense that fires (its origin filter never triggered). No confirmation prompts, expiry, merging or repair. The earlier working title here was too close to this paper's and was changed. |
| MemoryDojo (2611.09721) | Realistic multi-session benchmark: 155 trajectories, four tool-using domains, five memory backends, up to 60 sessions. | Evaluates no defenses and names that as future work. Code promised, not yet released. The natural testbed for this paper, and its authors are well placed to do the same study. |
| Accept Changes, Reject Attacks (2610.41056); Stage-Wise Utility-Risk Trade-offs (2608.30177) | Not yet read. | Read before writing. |
| SMSR (2606.12703) | Signed writes plus randomised retrieval with a certified bound | Append-only memory; attack goal is a false answer, not an action |
| CaMeL, FIDES, Progent | Information-flow control within one session | No persistent memory |
| Trojan Hippo Bench, MemSecBench, WhisperBench | Attack benchmarks across memory backends | Short horizons; defenses are not the focus |
| AgingBench (2605.26302) | Reliability decay over long deployments | Not adversarial |

**Consequence.** Most of memgate's mechanisms (context taint, no untrusted-initiated actions, confirm untrusted arguments, signed entries, audit log) are already in TMA-NM, with proofs and real-model results. They cannot be claimed as contributions. What is still open is expiry interacting with merges, repair after the fact, and long-horizon cost. memgate's role becomes the long-horizon harness plus those lifecycle rules, and the paper must evaluate TMA-NM's released code directly rather than only our own implementation.

## Threat model

- Attacker controls the content of some documents the agent reads. No access to the model, the runtime, the memory database or the user channel.
- Goal: cause a consequential action in a later session.
- The model is assumed fully compliant with any instruction it reads.
- Trusted: the runtime, the signing key, the user channel, tools the deployer marks trusted.
- Out of scope: a malicious user, a compromised trusted tool, attacks whose goal is only a false statement.

## Contributions

1. A long-horizon workload (tens to hundreds of sessions, with periodic consolidation) for measuring memory defenses, including legitimate facts that only ever arrive through untrusted sources.
2. Cost measurements for provenance-gated memory: confirmation prompts per task, legitimate memory lost, and how both move with expiry length and merge interval. Run on TMA-NM's released implementation and on memgate.
3. Lifecycle findings that prior work does not cover: expiry that is reset by merging, label creep that makes a user's own value expire with the poison, and repair by cascading retraction.
4. Residual risk as a function of how often a user approves a bad prompt.
5. Open-source harness.

## Experiments

| # | Question | Status |
|---|---|---|
| E1 | Which mechanism stops which attack class under a compliant model? | Simulated. See `results/summary.md` |
| E2 | How does residual attack success scale with user misclick rate? | Simulated |
| E3 | What does the defense cost with no attacker? | Simulated |
| E4 | Expiry length and merge interval sweep | Not run |
| E5 | Same scenarios with real models (two open-weight, two API) | Not run. Needs an agent adapter and compute |
| E6 | Run TMA-NM's released code and MEM-INV-Bench inside the long-horizon workload; compare with `full` | Not run. First check the repository's license |
| E7 | Adaptive attacks aimed at the confirmation prompt and at the trusted-tool boundary | Not run. Needs a collaborator to author the attacks |
| E8 | Small user study of confirmation prompts | Optional |

A paper with only E1 to E3 is a design note, not a security paper. E5 and E6 are the minimum for cs.CR. E7 is what would make the result hold up.

## Sections

1. Introduction
2. Background and threat model
3. How memory maintenance breaks provenance
4. Design: five rules
5. Evaluation method: the compliant-model bound
6. Results (E1 to E7)
7. Limitations: runtime trust, user fatigue, retrieval by similarity, synthetic workloads
8. Related work
9. Conclusion

## Risks

- **Novelty.** Confirmed: TMA-NM and PerMIT cover the design. The paper stands only on lifecycle and cost. Finish reading PerMIT, and search again before submitting, because this area gets several new papers a month.
- **Simulation scepticism.** Reviewers will discount E1 to E3 alone. Mitigation: E5 and E6.
- **The honest headline is a cost.** The defense works by asking the user more often. That is a real finding, but it has to be presented as one.
