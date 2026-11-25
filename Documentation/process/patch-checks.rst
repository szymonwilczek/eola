.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

============
Patch checks
============

``scripts/check-patch`` checks the commits of a branch against the rules in
:doc:`contributing` before the branch is offered for review.
``scripts/format-patch`` rewraps commit messages that fail the line-length or
whitespace checks.

Usage
=====

.. code-block:: console

   $ scripts/check-patch [<base-commit> [<head-commit>]]
   $ scripts/format-patch [<base-commit> [<head-commit>]]

Both scripts work on the commits in *base*..*head*. Without a base they use
the merge-base with the upstream branch, then with ``origin/eola-next``, then
with ``eola-next``, whichever exists first. *head* defaults to ``HEAD``.

Each check prints one line: ``PASS``, ``FAIL`` followed by a ``fix:`` line,
``SKIP`` followed by the reason, or ``INFO``. ``check-patch`` exits with 1
when any check fails, with 2 when it runs outside the repository, and with 0
otherwise.

Checks
======

commit signatures
   Every commit has a good GPG or SSH signature (``%G?`` is ``G`` or ``U``).
   With ``PATCH_SIGNATURES=github``, every commit is one GitHub marks
   verified.

Developer Certificate of Origin
   Every commit carries ``Signed-off-by: Name <email>``, preceded by one
   blank line or by another ``*-by:`` trailer.

commit subjects
   A subject is at most 75 columns and has no Conventional Commits scope.
   A subject of the form ``a/b:`` or ``a: b:`` prints an ``INFO`` line
   recalling what each form means.

commit body line length
   Body lines are at most 75 columns. Indented lines, trailers and lines
   carrying a URL keep their length.

commit body prose
   No body line starts with ``Problem:`` or ``Solution:``.

commit body detail
   A commit that touches three or more files or 40 or more lines carries a
   body of at least 40 words; five or more files or 100 or more lines, at
   least 80 words. A short body prints ``INFO`` and does not fail.

commit message whitespace
   Commit messages have no trailing whitespace and no trailing blank lines.

branch name
   The current branch name, or ``PATCH_BRANCH`` when set, is at most 75
   columns. Skipped on ``eola-next``, on ``main`` and on a detached ``HEAD``.

pull request title
   ``PATCH_TITLE`` passes the commit subject checks. Skipped when it is not
   set.

patch whitespace
   ``git show --check`` passes on every commit, and ``git diff --check``
   passes on staged and unstaged changes.

file trailing blank lines
   No changed text file ends with a blank line. Files whose ``whitespace``
   attribute is unset in ``.gitattributes``, such as the test vectors, are
   skipped here and by ``git diff --check``.

documentation build
   When a reStructuredText file or a file under ``Documentation/`` changes,
   ``make -C Documentation html`` builds without warnings. Skipped when
   ``sphinx-build`` is missing.

sphinx-lint
   When the documentation build runs, every tracked ``.rst`` file passes
   ``sphinx-lint`` with all checks except line length. Skipped when
   ``sphinx-lint`` is missing.

Merge commits are exempt from the commit message checks.

Environment
===========

``PATCH_BRANCH``
   Branch name checked in place of the current branch.

``PATCH_TITLE``
   Pull request title, checked under the commit subject rules.

``PATCH_SIGNATURES``
   ``github`` asks the GitHub API whether each commit is verified, for the
   repository named by ``GITHUB_REPOSITORY``, with the token in
   ``GH_TOKEN``. The commits must be on GitHub already. When unset, the local
   keyring decides.

Continuous integration
======================

``.github/workflows/checks.yml`` runs on every pull request and on every push
to ``eola-next`` and ``main``:

patch checks
   ``scripts/check-patch`` over the pull request commits, with
   ``PATCH_BRANCH``, ``PATCH_TITLE`` and ``PATCH_SIGNATURES=github`` set.
   Pull requests only.

documentation
   ``make -C Documentation lint`` and ``make -C Documentation html``. The
   ``linkcheck`` result is reported without failing the job, and the built
   HTML is kept as a workflow artifact for 14 days.

specification
   ``make -C spec``, with xml2rfc warnings as errors, ``make -C spec
   check``, and ``vectors/generate.py --check``. The rendered drafts are
   kept as a workflow artifact for 14 days.

libeola
   ``make -C libeola check``, ``check-sanitize`` and ``check-valgrind``,
   once with gcc and once with clang.

libeola formatting
   ``make -C libeola format-check`` with the clang-format version of
   ``libeola/requirements.txt``.

Go
   ``go test -race ./...`` and ``golangci-lint run ./...`` in ``go/``, with
   the Go version of ``go/go.mod``.

shell scripts
   ``shellcheck -x`` on every file under ``scripts/``.

workflow security
   ``zizmor`` on the workflows, configured by ``.github/zizmor.yml``: actions
   from ``actions/*`` and ``github/*`` are referenced by version tag, every
   other action by full commit hash.

Rewrapping messages
===================

``format-patch`` rewrites the commits in the range so that their messages pass
the message checks. It removes trailing whitespace and trailing blank lines,
keeps one blank line before the first ``Signed-off-by``, and wraps body
paragraphs to 75 columns. Indented lines, trailers and lines carrying a URL are
left as written.

Each rewritten commit keeps its tree, author, committer and dates, and is
signed again when ``commit.gpgsign`` is ``true``. The script refuses a range
with merge commits, a dirty working tree or index, and a *head* other than the
tip of the current branch. The previous tip is kept on a branch named
``backup-<branch>-before-format-patch-<UTC time>``.

Files
=====

``scripts/check-patch``
   The checks.

``scripts/format-patch``
   The message rewrite.

``.github/workflows/checks.yml``
   The continuous integration jobs.

``scripts/lib/commit-limits.sh``
   The column limit and the pattern of body lines exempt from it, shared by
   both scripts.
