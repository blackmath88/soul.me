# Ecosystem fit for soul.me — 2026-10-06

Status: research assessment and proposed experiments. No dependency, service, schema or settled decision is changed.

Reviewed repository main `fc72159f3e5e0074288f7d09844501710b6c351a`: README, AGENTS, concept, vision, architecture, spec, decisions, research and roadmap. No repository-owned Observatory snapshot/configuration is present in that tree; the Actions artifact inventory was not readable through the available fetch endpoint. No authenticated Weavr state was available, and no Mission status is inferred.

## The product boundary

soul.me describes a human to assistants working with them. The reviewed Markdown vault is the portable product; an agent runtime or chat workspace is a consumer. The public soul.me repository contains tools and fictional fixtures; real vaults remain separate and private.

Keep the settled decisions:
- D-002/003: Markdown in Git; four layers and scoped loading.
- D-004/006/009: only human-confirmed `[stated]` lines are served as facts; proposals stay in inbox/review.
- D-005: FTS5 before vectors.
- D-013: drop-in exports before optional MCP.
- D-014/015: source-side sanitising; real data outside this public repository.
- D-019/026: existing brand; a short ranked review list, never auto-acceptance.

Do not mistake assistant-persona files, automatic agent learning or persistent agent conversations for a portable human self.

## Fit table

| Candidate / pattern | Fit for soul.me | Proposed use | Constraint |
| --- | --- | --- | --- |
| agent-memory | Closest technical fit | v4 optional lexical retrieval pilot; progressive path/outline/full reads | Its lifecycle writes and store schema cannot become soul.me authority |
| Caveman / context budgeting | Strong pattern fit | v2 bounded exports; small core and on-demand procedures/episodic context | Preserve hard rules, provenance and validity; no arbitrary lossy compression |
| Strands Decider | Useful bounded intake experiment | Triage already extracted candidates: layer, correction type, review priority | Cannot generate quoted findings, confirm truth or authorize disclosure |
| OpenDots / CopilotKit | Later interaction reference | Draft/review cards, changed-draft reapproval, source links | Do not adopt its conversation stack or automatic learning as the vault |
| Operator Memory | Extraction pattern only | Proposed inbox candidates from permitted sources | Exact upstream identity/write behavior needs verification; no live writes |
| vLLM Semantic Router | Infrastructure outside core | Optional execution plumbing for intake model calls | Model selection does not decide provenance, privacy or sealing |
| Magnitude | Local backend candidate | Evaluate only if intake inference becomes a measured bottleneck | Host/model support and format compatibility first; not a soul.me dependency |
| Worktrees + skills | Useful existing convention | Versioned procedure exports; isolated tool development | Human skill steps retain their tags; agent repo instructions are a separate concern |
| Open Ontologies | Research vocabulary | Type/validity/contradiction impact reasoning | No ontology engine for the current four-layer vault |
| FalkorDB | Premature | Defer until repeated relationship queries defeat simpler storage | No graph migration based on ecosystem popularity |
| Cua | Weak current fit | Possible later assisted intake surface | Employer boundaries and review still apply; no computer-use build now |
| RL through harnesses | Distant research | Preserve fictional evaluation cases and outcomes | No training on real personal exports by default |

Only agent-memory, Strands Decider, OpenDots, vLLM Semantic Router and Magnitude upstream material was directly inspected for this assessment. Other posts supply patterns to consider; exact dependencies/performance remain unverified.

## 1. agent-memory: reuse retrieval, preserve the vault

Its README describes Markdown as store truth, a rebuildable SQLite index, ranked local path recall, optional vectors and progressive reads. It also describes automatic boundary-triggered distillation and unattended consolidation that may add/update memories. Those writes conflict with D-006 if pointed at live soul.me files.

Proposed v4 pilot:
1. Use a disposable read-only view of fictional, validated live vault content. Keep soul.me syntax unchanged; do not convert the canonical vault into another tool's schema.
2. Index only profile-permitted, unexpired `[stated]` lines. Exclude inbox, raw exports, archived/invalid facts and unrelated profiles **before ranking**, snippets or serialization.
3. Return bounded paths/anchors, then outline or exact approved lines, then full permitted content on request. A whole-file read must not reintroduce excluded lines.
4. Record source revision/digest, profile, validity and index version. Rebuild from Markdown; stale indexes cannot resurrect retired facts.
5. Disable global injection, automatic writes, trace copying and sleep-time management. If read-only integration or schema mapping is not demonstrable, benchmark a copied corpus offline and reuse the retrieval pattern only.
6. Compare plain FTS5 with recall-assisted retrieval on labelled queries. Add vectors only after a measured FTS miss, consistent with D-005.
7. Prove index-off fallback to direct core/drop-in exports and permitted file reads.

Measure relevant-hit recall, obsolete/forbidden-hit leakage, tokens actually read, latency and portability. Reject the integration if better recall depends on a second authoritative store or requires automatic live writes.

## 2. Strands Decider: classify after extraction, never seal

The inspected implementation uses a pretrained Qwen torso with a pointer head instead of a language-generation head. It selects among request-defined options or scores an ordered scale in one forward pass. It remains probabilistic; a typed output is not proof that the classification is right.

A useful thin experiment is **candidate layer triage**:
- Input: a redacted, quote-verified finding already produced by the existing extractor.
- Options: core / procedure / episodic / session / needs-review.
- Output: candidate label, model/checkpoint, confidence and latency.
- Consequence: review ordering or suggested destination only.

A second possible task is correction classification: standing preference / situational request / pasted material / ambiguous. Neither task replaces extraction: the model cannot write a new evidence-backed statement or quote. It must not replace deterministic redaction, quote matching, validator checks or source/destination policy.

Use fictional held-out cases covering paraphrases, conflicting dates, negation, multilingual text and quoted/pasted instructions. Compare current judge/classifier with Decider; distinguish accuracy from accepted coverage after abstention. Measure confusion matrix, per-class precision/recall, calibration, reviewer changes, latency/memory and total inference work. Set a confidence threshold from soul.me cases, not the upstream benchmark. Low confidence, malformed/oversized inputs, unsupported labels and service outage retain existing review/fallback.

Upstream reports limits on unfamiliar scoring and long multi-step documents. Keep the first trial short and categorical; do not use a score as a gate that silently discards important corrections or approves sensitive disclosure.

Serving has its own HTTP endpoint (`/v1/systemone`), not a presumed OpenAI chat completion API. The documented devices are CUDA, Apple MPS/MLX and CPU; Intel Arc support is not established. Hardware admission and a narrow client would be separate work, not a reason to rebuild intake now.

## 3. OpenDots: borrow a review interaction, defer the stack

The strongest pattern is its draft review card: inspect a draft, approve or decline, recover the same approved draft on retry, and require another review when the draft changes.

A later soul.me review surface could show:
- proposed line with quote/source and suggested layer;
- current conflicting/obsolete line;
- accept, edit or reject;
- destination profile and excluded-content explanation.

Approval should bind the exact reviewed content and base vault revision. Changed content or a concurrent edit requires fresh review. The committed vault remains canonical; UI pages and thread state do not become another live self. Any visual implementation follows the existing kitsune/sumi/seal brand, not OpenDots branding.

Do not build this before drop-in exports and weekly curation prove useful (D-013, vision). GitHub review remains the current surface.

The current OpenDots README/setup distinguishes the MIT application template from its conversation dependency: conversations require CopilotKit Intelligence, either hosted, local evaluation or licensed self-hosting. SQLite stores pages/metadata, not standalone conversation history. Local evaluation requires an account and renewable evaluation license; a remote model remains remote. Therefore “open-source template” does not establish a fully independent production memory stack.

Automatic Learning is about improving agent workflows; it is not human-confirmed soul.me facts. Do not enable it on private vault material or assume its user-memory feature interoperates with soul.me tags/profiles.

## Proposed sequence without changing the roadmap

1. **v2 first:** implement work/personal drop-in profiles and explicit export budgets, with tests for inbox/expired/private-line exclusion. Existing profile details remain proposals where marked as such in DECISIONS.
2. **v1 optional evaluation:** run Decider layer triage in shadow on fictional extracted findings; no live ranking/filter change.
3. **v3:** prove weekly review, contradiction handling and expiry using existing Git/PR mechanics.
4. **v4 optional evaluation:** compare native FTS5 with a read-only recall adapter; no vectors by default.
5. **Later:** prototype one review card only if GitHub batch review creates a demonstrated usability problem.

No model/tool choice changes what travels, who seals it or where the real vault lives. The caller may consume a scoped soul.me export; Weavr owns software Mission authority separately.

## Primary sources inspected

Inspected on 2026-10-06; pin releases/commits and recheck behavior before installation:
- [agent-memory README](https://github.com/tigerless-labs/agent-memory/blob/main/README.md), blob `f5cf510c7eefcf78b80c20f168fb8076997fabe9`.
- [Strands Decider README](https://github.com/strands-labs/strands-decider/blob/main/README.md), blob `ac9dd2eea28fe8b72f389b78135259456ac86978`; [results](https://github.com/strands-labs/strands-decider/blob/main/evaluation/results.md) and [inference](https://github.com/strands-labs/strands-decider/blob/main/docs/inference.md).
- [OpenDots README](https://github.com/CopilotKit/OpenDots/blob/main/README.md), blob `027f60d73ed81d322b36f23b2f6d245884123138`; [setup](https://github.com/CopilotKit/OpenDots/blob/main/docs/SETUP.md), blob `0a6c56b26601683f129e581941e3cbd54a391c45`.
- [vLLM Semantic Router](https://github.com/vllm-project/semantic-router), README blob `71e8cae18a9db06980220288126653f98b9d9dd6`.
- [Magnitude](https://github.com/magnitudedev/magnitude), README blob `fb2882c03d9123af6743bec31d628dcfc67773f8`.

Upstream accuracy, speed and confidence figures are vendor/project measurements, not soul.me evidence. No dependencies were installed and no personal vault data was used.
