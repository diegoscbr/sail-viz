---
name: progress
description: Use when the user says "/progress", asks to log progress, write session notes, update the progress folder, or sync the README with recent changes on main. Maintains a progress/ folder of dated session entries and refreshes the top-level README when new commits have landed on origin/main since the last entry.
---

# Progress

Keep a running log of work in `progress/` and keep the top-level `README.md` in sync with what has landed on `origin/main`.

## When to use

- User types `/progress`, "log progress", "update progress", or "write session notes"
- End of a working session where something meaningful changed
- Right after pushing to main, to refresh the top-level README

## What this skill does

1. Bootstraps `progress/` if missing (creates `progress/README.md` as an index).
2. Writes a new dated entry capturing what changed, why, what's next, and open questions.
3. Prepends a link to the new entry in `progress/README.md`.
4. Refreshes the top-level `README.md` if commits have been pushed to `origin/main` since the previous entry's recorded HEAD.

## Steps

### 1. Inspect state

Run these (Bash tool) to gather context. Don't guess — read the output.

```bash
REPO=$(git rev-parse --show-toplevel)
cd "$REPO"
git fetch origin main 2>/dev/null || true
git branch --show-current
git rev-parse HEAD
git log -n 10 --oneline
git log -n 10 --oneline origin/main 2>/dev/null || true
git status --short
```

### 2. Bootstrap `progress/` if missing

If `progress/` doesn't exist, create `progress/README.md` with:

```markdown
# Progress Log

Running log of work on this repo. Each entry is a dated markdown file in this folder.
Newest entries first. Read the latest entry at the start of a session to catch up.

## Entries
<!-- managed by the /progress skill — newest first -->
```

### 3. Find the previous entry

List `progress/*.md` excluding `README.md`, sorted by filename descending. Read the newest one with the Read tool and pull out its `head:` frontmatter value as `PREV_HEAD`. If none exists, `PREV_HEAD=none`.

### 4. Compose the new entry

Filename: `progress/YYYY-MM-DD-HHMM.md` using local time.

Template (fill every section from the actual conversation + git output — no placeholder text):

```markdown
---
date: YYYY-MM-DD HH:MM
branch: <current branch>
head: <current HEAD sha>
prev_head: <PREV_HEAD or "none">
---

# <Short, specific title>

## What changed
- <bullet per concrete change>

## Why
- <motivation / decisions made>

## Next
- <what the next session should pick up>

## Open questions
- <anything unresolved, or remove the section>

## Commits since previous entry
<output of: git log --oneline PREV_HEAD..HEAD  (or "none" if PREV_HEAD=none)>
```

Be concrete. Bullets over prose. If you don't know something, ask the user rather than inventing it.

### 5. Update `progress/README.md` index

Prepend one line under `## Entries` (newest first):

```
- [YYYY-MM-DD HH:MM — Short title](YYYY-MM-DD-HHMM.md)
```

### 6. Refresh top-level `README.md` if main moved

```bash
git log --oneline "$PREV_HEAD..origin/main" 2>/dev/null
```

If that produces commits (or `PREV_HEAD=none` and `README.md` is missing or stale):

- If `README.md` doesn't exist: create a minimal one with project name, a one-paragraph purpose inferred from the repo, and a `## Recent changes` section listing the relevant commits.
- If `README.md` exists: update only the `## Recent changes` (or `## Changelog`) section with the new commits. Do NOT rewrite prose the user has written elsewhere in the file.

Keep edits minimal and factual. User-visible changes only — skip pure refactors, chore commits, and formatting.

### 7. Report and stop

Print the path of the new entry and a one-line summary of what was updated (progress entry + index + whether README was touched). Do NOT run `git add`, `git commit`, or `git push`. Leave the changes for the user to review.

## Rules

- Never auto-commit or push. Leave changes unstaged for the user to review.
- Never overwrite an existing progress entry — always create a new file.
- If unsure what changed, ask the user before writing.
- Keep entries terse. Bullets, not paragraphs.
- Do not edit other people's prose in `README.md` — only the changes section.

## Session-start behavior (reference)

The project `CLAUDE.md` tells Claude to read `progress/README.md` and the most recent entry at session start. This skill does not need to do anything for that — it's handled by `CLAUDE.md` being loaded automatically.
