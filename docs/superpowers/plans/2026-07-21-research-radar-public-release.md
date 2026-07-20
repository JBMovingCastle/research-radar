# Research Radar Public Release Implementation Plan

> **For agentic workers:** Implement each checkbox in order and keep every task independently testable.

**Goal:** Deliver a public, configurable, verified research-radar repository for CI3 classmates.

**Architecture:** A standard-library Python package provides a single CLI, normalized adapters, a deterministic selection pipeline, Markdown rendering, run state, and optional delivery. Codex Skills call the same stable CLI rather than duplicating paths or network logic.

**Tech Stack:** Python 3.11 standard library, `unittest`, Markdown, JSON, GitHub Actions, PowerPoint.

## Global Constraints

- No private vault state, credentials, recipient IDs, absolute local paths, or real run ledgers.
- No browser-login validation and no Feishu send during release verification.
- OpenAlex is optional and requires `OPENALEX_API_KEY`; other keys stay optional.
- Daily output is idempotent unless `--force` is explicitly passed.

---

### Task 1: Release skeleton and configuration

- [ ] Add package metadata, safe defaults, CI3 and blank configuration templates.
- [ ] Implement config loading, validation, repository-safe path resolution, `init`, and `doctor`.
- [ ] Verify valid defaults and rejection of invalid JSON, unsafe paths, empty queries, and invalid ISSNs.

### Task 2: Source adapters

- [ ] Add normalized candidate/result models and bounded HTTP behavior.
- [ ] Implement Crossref, arXiv, Semantic Scholar search/recommendations, OpenAlex, RSS/Atom, and official-page adapters.
- [ ] Verify representative fixtures, disabled/missing-key states, throttling, and isolated failures.

### Task 3: Daily pipeline and delivery

- [ ] Implement merge, hard filtering, venue policy, scoring, quotas, rendering, run state, and ledger updates.
- [ ] Add local, stdout, and optional Feishu delivery with one-attempt idempotency.
- [ ] Verify daily uniqueness, force override, partial coverage, and corrupted-ledger handling.

### Task 4: Skills and public documentation

- [ ] Add research-radar and paper-analyze Skills using the public CLI.
- [ ] Add Skill eval prompts and evidence/failure references.
- [ ] Write quickstart, configuration, adapter, troubleshooting, privacy, contribution, and upstream-license documentation.

### Task 5: Sharing deck

- [ ] Rebuild the supplied visual language into a corrected six-slide public deck.
- [ ] Remove personal metadata, render all slides, and fix overflow or overlap.

### Task 6: Release verification and publication

- [ ] Run offline tests and a clean-clone initialization/doctor cycle.
- [ ] Run one bounded live public-source collection with no send.
- [ ] Scan tracked files and Git history for private data and secrets.
- [ ] Create `JBMovingCastle/research-radar`, push `main`, tag `v0.1.0`, and publish release notes.
