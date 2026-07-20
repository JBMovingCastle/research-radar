---
name: research-radar
description: Initialize, configure, diagnose, run, schedule, and deliver the Research Radar daily paper and industry brief. Use this whenever the user mentions research radar, paper radar, daily research brief, changing research keywords or journals, adding RSS/API sources, checking collection coverage, or installing a daily Codex task.
compatibility: Requires Python 3.11+. Public sources need network access. OpenAlex and Feishu are optional and require their own runtime configuration.
---

# Research Radar

Operate the repository through its public CLI so configuration, source behavior, paths, and run state stay consistent.

## Locate the repository

Starting from the working directory, locate both:

- `pyproject.toml` containing `ci3-research-radar`
- `research_radar/__main__.py`

Use that directory as `REPO_ROOT`. Do not treat a user's broader Obsidian vault as the release repository.

## Choose the workflow

### Initialize

When the user asks to install, initialize, set up, or make the radar usable:

```bash
python3 -m research_radar init --preset ci3
python3 -m research_radar doctor
```

Use `--preset blank --interactive` for a non-CI3 group. Do not overwrite an existing config unless the user explicitly asks for replacement.

### Modify research settings

Read `research-radar.config.json` and the relevant section of `docs/CONFIGURATION.md`.

Edit only the requested fields, such as:

- `context_keywords`
- `tracks[].keywords` and `tracks[].queries`
- `target_sources` and `selection.venue_mode`
- `authors` and `seed_papers`
- `sources.feeds` and `sources.web_pages`
- `paths`

Then run:

```bash
python3 -m research_radar validate
python3 -m research_radar doctor
```

Paths must remain relative to the repository. Keep keys, recipient IDs, and tokens out of JSON.

### Generate today's brief

Run from `REPO_ROOT`:

```bash
python3 -m research_radar run --json
```

Read the reported candidates file and brief before summarizing completion. Report:

- brief path;
- selected count and focus track;
- coverage status;
- failed, limited, partial, or misconfigured sources.

Do not infer that there were no relevant papers when coverage is partial. Do not describe abstract-only material as full-text reading.

Use `--force` only after confirming that an intentional same-day rebuild is wanted.

### Install a daily Codex task

When the user asks for daily automation, use the Codex automation mechanism available in the current environment. Schedule a local task whose prompt instructs Codex to:

1. change to `REPO_ROOT`;
2. run `python3 -m research_radar run --json`;
3. inspect source status and brief output;
4. keep the local brief even when optional delivery fails;
5. avoid committing personal configuration or reports to GitHub.

Use the user's timezone and requested time. If no time is given, ask rather than inventing a schedule.

### Deliver

Local delivery happens when the Markdown file is written. Stdout is safe for inspection:

```bash
python3 -m research_radar deliver --date YYYY-MM-DD --channel stdout
```

Only use `--channel feishu` when the user explicitly authorizes the recipient, content, and bot identity or an existing automation already contains that authorization. Never print or store the recipient value.

## Failure boundaries

Read `references/evidence-and-failure-rules.md` when a source fails, zero items are selected, or a full-text claim is being considered.

One provider failure must not trigger repeated retries or stop the remaining sources. Preserve the source status emitted by the CLI.
