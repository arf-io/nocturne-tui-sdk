#!/usr/bin/env sh
# Explicit publishing helper: uses an existing local checkout and caller-supplied
# GitHub destination. Never guesses the user's owner, creates a repo, or force-pushes.
set -eu
if [ "$#" -ne 2 ]; then
  printf 'Usage: sh scripts/continue_git.sh GITHUB_OWNER EXISTING_REPOSITORY\n' >&2; exit 2
fi
case "$1/$2" in *[!A-Za-z0-9_./-]*|*..*) printf 'Invalid owner/repository\n' >&2; exit 2;; esac
cd "$(dirname "$0")/.."
git rev-parse --is-inside-work-tree >/dev/null
branch=$(git branch --show-current)
[ "$branch" = feature/vol5-spatial-atelier ] || { printf 'Switch to feature/vol5-spatial-atelier first.\n' >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { printf 'Commit or preserve local changes before publishing.\n' >&2; exit 1; }
command -v gh >/dev/null || { printf 'GitHub CLI gh is required.\n' >&2; exit 1; }
gh auth status
url="git@github.com:$1/$2.git"
if git remote get-url publish >/dev/null 2>&1; then
  [ "$(git remote get-url publish)" = "$url" ] || { printf 'Existing publish remote differs; inspect it manually.\n' >&2; exit 1; }
else git remote add publish "$url"; fi
printf 'Publishing %s to %s\n' "$branch" "$url"
git push -u publish "$branch"
gh pr create --repo "$1/$2" --head "$branch" --title 'Spatial Atelier: direct camera, layouts, text and kinetic windows' --body-file docs/atelier/PR_BODY.md
