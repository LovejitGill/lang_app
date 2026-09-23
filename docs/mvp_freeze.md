# Milestone 7 — MVP Freeze, Then (Optional) Phase 2

**Current status:** Source-copy verification passed: the locked environment was
recreated from cached packages and all 96 tests passed in the separate copy.
The user handles Git operations; `mvp-v1` has not been created by the assistant.
Commands below that inspect/recover the tag apply only after creating it.

## What the checkpoint will contain

`mvp-v1` is the planned local annotated Git tag for the functional recorded-turn demo:
text or recorded English input → editable transcript → local Qwen reply and
experimental feedback → SQLite history. Dependencies, tests, setup scripts,
evaluation evidence, and this learning roadmap are included.

This is a recoverable engineering baseline, not an endorsement of teaching
accuracy or completed capstone submission. False grammar corrections, failed
recall, and latency above two seconds remain documented in `docs/evaluation.md`.
Live automatic turns, speech output, pronunciation assessment, final presentation,
and public GitHub publication are not completed by making a tag.

## Concepts to understand

A **commit** records the tracked project files at a point in time. A **tag** gives
that commit a stable name; an annotated tag also records a message and author.
A **worktree** is a separate checkout of the repository, useful for inspecting
the baseline without overwriting current development. None includes ignored
model weights, environments, or personal SQLite history.

Keep `mvp-v1` fixed. Create a new commit/tag for later validated releases instead
of moving it. Optional work should start on a separate branch after this freeze.

## Verify the checkpoint

Create the checkpoint from your own terminal. Review the files before committing:

```bash
git add .gitignore .python-version AGENTS.md README.md app.py db.py docs errors.py evaluate.py implementation_plan.md improvement_plan.md llm_client.py model_manifest.json prompts.py pyproject.toml scripts stt.py tests uv.lock
git diff --cached --stat
```

**Purpose/typical use:** `git add` stages the explicit project files and
`git diff --cached --stat` summarizes them for pre-commit review.
**Expected:** Source, docs, tests and lockfile entries; no `.models`, `.venv`,
`data`, personal recordings, or database files.

```bash
git commit -m "Freeze recorded-turn SpeakWell MVP baseline"
git tag -a mvp-v1 -m "Functional recorded-turn baseline; known feedback and latency limitations"
```

**Purpose/typical use:** `git commit` records the staged snapshot; `git tag -a`
names it as a recoverable baseline for later development.
**Expected:** A commit summary, then no tag-command output on success. Run the
tag command only after the commit succeeds; do not force-replace an existing tag.

Run these commands from the project directory:

```bash
git show --no-patch mvp-v1
```

**Purpose/typical use:** Displays the named release checkpoint and its commit;
normally used to confirm what a tag identifies.
**Expected snippets:** `tag mvp-v1`, its annotation, and a `commit ...` line.

```bash
git status --short
```

**Purpose/typical use:** Lists tracked edits and untracked files; normally used
before committing or changing branches.
**Expected:** No output immediately after the freeze. Ignored model caches and
learner data still exist locally but are not part of the checkpoint.

```bash
uv run --locked python -m pytest -q
```

**Purpose/typical use:** Runs the baseline's regression suite after setup or
changes. **Expected:** `96 passed in ...`; this verifies the tested application
behavior, not model teaching accuracy.

## Inspect or recover without replacing current work

Choose a new sibling folder that does not already exist:

```bash
git worktree add --detach ../speakwell-mvp-v1 mvp-v1
```

**Purpose/typical use:** Creates a separate checkout of the frozen tag; normally
used to compare or test an older version without changing current files.
**Expected snippets:** `Preparing worktree (detached HEAD ...)` and
`HEAD is now at ...`. Detached means this copy is for inspection, not ongoing
branch development; create a branch before making changes you intend to keep.

```bash
cd ../speakwell-mvp-v1
uv sync --locked
```

**Purpose/typical use:** `cd` enters the baseline copy and `uv sync --locked`
recreates its environment from the saved lockfile.
**Expected:** No output from `cd`, then dependency-resolution/installation output.

Model files are not in Git. For a fully independent demonstration, follow
`docs/recorded_voice.md`: bootstrap the local Ollama runtime with
`scripts/setup.sh`, download Qwen and the pinned speech model, then start Ollama
and Streamlit. Follow each guide's command explanations and expected outputs.
Do not start a second Ollama on the same port while the original is running.
Initial setup requires internet; prepared inference uses local models.

The Ollama model tag can change upstream. Compare its full digest with
`model_manifest.json` after pulling; preserve the existing model cache for your
demo. Git alone cannot recreate an upstream artifact that is no longer hosted.

## Optional Phase 2 checkpoint

No optional enhancement is included in this freeze. Before adding one, choose a
single objective and record its success criteria. The most urgent existing
quality problem is false grammar feedback; spoken output would not fix it.
If you later choose Kokoro, first check Intel macOS/CPU compatibility and measure
latency, then implement it in a separate branch without moving `mvp-v1`.

**Your exercise:** Explain the difference between a branch, tag, and ignored
model cache. Inspect the tag, run its tests, and identify the documented failures
that must remain visible in a presentation. Do not describe this checkpoint as
validated pronunciation tutoring or a completed submission.
