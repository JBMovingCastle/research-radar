# Evidence and failure rules

- `metadata`: title, identifiers, authors, venue, and dates only.
- `abstract`: the source supplied an abstract; analysis must remain abstract-level.
- `feed-summary`: a publisher or institution feed supplied a summary.
- `webpage-link`: only the link title and source page are known.
- An open PDF URL means a link exists. It does not prove the file was downloaded or read.
- Mark analysis as full-text only after successfully opening and reading the actual text.
- `limited`, `failed`, `partial`, or `misconfigured` means source coverage is incomplete.
- Zero selected items with incomplete coverage is not evidence that no relevant work exists.
- Never bypass authentication, paywalls, robots controls, or institutional access rules.
- Do not silently replace selected items with lower-scoring content outside the deterministic pipeline.
