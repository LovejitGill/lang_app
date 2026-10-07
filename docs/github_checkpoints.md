# GitHub checkpoints and experiment versions

Recommendation after planned_v3 verification: **yes, this is a useful experimental
commit/push checkpoint**, after you review the accumulated changes. The full suite
passed 703 tests and the frozen run completed, but conversation review and actual
spoken latency remain pending. This is not a stable app release.

Local inspection found branch `main`, remote name `origin`, latest existing commit
`991d368`, and tag `mvp-v1`. Remote publication has not been verified. The working
tree includes many earlier untracked modules and evidence files, so the checkpoint
must include reviewed dependencies rather than only the newest two helpers.

## Keep three kinds of version separate

- `planned_v3`: the frozen experiment, code identities, cases and results.
- A Git checkpoint: your commit, optionally labeled `conversation-planned-v3`.
- An application release: package version and integrated, app-tested behavior.

The next experiment can be `planned_v4` after reviewing this iteration; that does
not imply a stable app v4 release. A meaningful commit is sufficient for a checkpoint;
a tag is optional. Preserve `mvp-v1` and never move an existing tag to new work.

## User-managed checkpoint steps

Run these from the project directory after reviewing the results. None of the
staging, commit, tag or push commands below has been executed by the assistant.

### One-time cleanup after `git add .`

Inspection on 2026-10-06 found 349 staged files and an already-tracked `AGENTS.md`.
The ignore rules now exclude the root `AGENTS.md`, but Git continues tracking it
until you remove it from the index (Git's staging area). Keep the file locally;
you are adding its path to `.gitignore`, not moving its contents into that file.

1. Unstage everything while preserving your working files.

   ```bash
   git restore --staged .
   ```

   `git restore --staged` normally resets the selected staging entries to the last
   commit; here it undoes `git add .` without discarding your edits or new files.
   Expected: no output on success.

   ```bash
   git diff --cached --name-only
   ```

   `git diff --cached --name-only` normally lists paths with staged changes; here
   an empty result verifies that everything was unstaged.

2. Stop tracking the local instructions file.

   ```bash
   git rm --cached -- AGENTS.md
   ```

   `git rm --cached` normally removes a path from the index while retaining its
   working copy; here it stages removal of `AGENTS.md` from future commits.
   Expected: `rm 'AGENTS.md'`. This is an intentional repository deletion, not a
   deletion of your local file; it does not erase the file from earlier commits.

3. Verify the file remains local, untracked, and ignored.

   ```bash
   ls AGENTS.md
   git ls-files -- AGENTS.md
   git check-ignore -v AGENTS.md
   ```

   `ls` normally lists files; `AGENTS.md` in its output confirms the local copy remains.
   `git ls-files` normally lists indexed paths; no output confirms this file is no
   longer tracked in the index. `git check-ignore -v` normally identifies the ignore
   rule for a path; expect `.gitignore:2:/AGENTS.md` followed by `AGENTS.md`.

4. Stage the ignore rule and review this cleanup.

   ```bash
   git add .gitignore
   git status --short -- .gitignore AGENTS.md
   ```

   `git add` normally stages file contents for the next commit; this command stages
   only the updated ignore rules. `git status --short` normally shows concise file
   states; here the path filter isolates the two cleanup changes.

   Expected:

   ```text
   M  .gitignore
   D  AGENTS.md
   ```

   The first-column `M` and `D` mean the ignore update and repository removal are
   staged. Your other project changes remain unstaged until you select them below.
   Once these steps are complete, ordinary `git add .` will respect the ignore rule;
   do not use `git add -f` on the local instructions file.

The audit found no indexed files matching the previous ignore rules. Existing
rules already exclude model weights, installers, the environment, runtime data,
recordings and caches. Preventive additions cover Python build/coverage output,
type-checker/notebook caches, SQLite companion files and Streamlit secrets; these
were not observed as accidentally staged artifacts. Keep `uv.lock`,
`.python-version`, `model_manifest.json`, source, tests, plans and the synthetic
evaluation cases/results/frozen snapshots: they support reproducibility and review.

### Review and publish the intended checkpoint

1. Inspect everything changed, including untracked files.

   ```bash
   git status --short
   git diff --stat
   ```

   `git status --short` normally lists tracked changes and untracked files; here
   it shows the complete checkpoint inventory. `git diff --stat` summarizes tracked
   edits and normally omits untracked contents, so read both outputs together.

   Expected markers include ` M` for edited files and `??` for new source/tests/docs/evidence.
   After the cleanup above, also expect `M ` for `.gitignore` and `D ` for `AGENTS.md`.
   Review their contents before proceeding; a file count does not verify correctness.

   The existing ignore rules cover `.venv`, caches, tools/installers, model weights,
   `.env` configuration, runtime data, databases and recordings. Keep private learner
   content out of evaluation artifacts if real inputs are introduced later.

2. After reviewing the complete project changes, stage the intended checkpoint.

   ```bash
   git add -A -- .
   git diff --cached --stat
   git diff --cached --check
   ```

   `git add -A -- .` normally stages additions, edits and deletions under this directory;
   use it here only if you intend to checkpoint all reviewed accumulated project changes.
   Otherwise stage your chosen explicit paths instead, including required earlier dependencies.

   `git diff --cached --stat` normally summarizes the staged snapshot.
   `git diff --cached --check` checks staged whitespace errors before committing.

   Expected: intended source, tests, docs and synthetic evidence in the summary,
   and no output from `--check`. These checks verify the staged contents/format,
   not semantic quality or GitHub state; inspect the staged diff as needed.

3. Save the local checkpoint.

   ```bash
   git commit -m "Checkpoint tutoring experiments through planned_v3"
   ```

   `git commit` normally records the staged snapshot in local history; this message
   identifies the accumulated experimental work without labeling it a stable release.

   Expected shape: `[main <new-hash>] Checkpoint tutoring experiments through planned_v3`.
   This confirms a local commit, not publication. If it says there is nothing to commit,
   inspect the current log/status rather than creating an empty commit.

4. Publish the commit when you are ready.

   ```bash
   git push
   ```

   `git push` normally sends local commits to the configured upstream; here it publishes
   your reviewed checkpoint using the repository’s existing configuration.

   Expected success may include `main -> main`; `Everything up-to-date` means there
   were no new commits to send. Resolve authentication or rejected-push messages
   normally; do not force-push to bypass them.

5. Optional: add a distinct experimental label after confirming it is unused.

   ```bash
   git tag --list conversation-planned-v3
   ```

   `git tag --list` normally lists matching local tags; here an empty result verifies
   only that this proposed label is unused locally. Check GitHub for remote-only tags
   before creating a label, and do not overwrite an existing tag.

   If the label is unused and you want it:

   ```bash
   git tag conversation-planned-v3
   git push origin conversation-planned-v3
   ```

   `git tag` normally labels the current commit locally; the explicit tag push publishes
   that label to `origin` without pushing all local tags.

   Expected: no output when creating the tag and a `[new tag] ... -> ...` push line.
   This labels the experiment; it does not create a stable release or deploy the app.

## Next improvement

Review the actual planned_v3 replies, particularly conversational tone, then prepare
fresh multi-turn validation as planned_v4 while keeping the same quality/latency focus.
**GitHub checkpoint: yes for the tested experiment after the ignore/untracking cleanup
and your file review; no stable app-version promotion yet.** Future Next improvement
notes will state both checkpoint readiness and version guidance. You continue to own
commits, tags and pushes.
