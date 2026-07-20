# Research Radar Public Release Design

## Goal

Publish a clean, reusable CI3 research-radar repository that works on first run without API keys, remains fully configurable, and records partial source coverage honestly.

## Architecture

The Python 3.11 standard-library package exposes `init`, `doctor`, `run`, and `deliver` commands. Source adapters normalize remote records into one candidate model; the pipeline then deduplicates, filters, scores, selects, renders, and records one daily Markdown brief. Codex Skills operate the same CLI and add evidence-bounded synthesis or paper analysis.

The default source baseline is Crossref, arXiv, RSS/Atom, and configured official pages. Semantic Scholar search and recommendations can run without a key but report shared throttling; OpenAlex is optional and requires `OPENALEX_API_KEY`. Local Markdown is the default delivery. Stdout and Feishu are replaceable delivery adapters.

## Safety and publishing boundaries

- Build from an explicit release allowlist; do not copy the private Obsidian workspace.
- Keep secrets in environment variables and runtime data in ignored directories.
- Reject output paths that are absolute or escape the repository.
- Treat a failed source as partial coverage, not proof of no relevant research.
- Do not scrape Google Scholar, bypass paywalls, or include Sci-Hub workflows.

## Acceptance

A clean clone can initialize, pass `doctor`, and generate a factual Markdown brief from at least one public source without a key. Users can change tracks, queries, journals/ISSNs, seed papers, feeds, official pages, scoring, and output paths. Offline tests cover validation, normalization, deduplication, scoring, ledger behavior, and source failures; a bounded live smoke test verifies public APIs without sending messages.
