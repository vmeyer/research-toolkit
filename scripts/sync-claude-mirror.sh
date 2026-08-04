#!/usr/bin/env bash
#
# Regenerate the Claude Code standalone mirror (.claude/) from the canonical
# root plugin sources.
#
# The repository root IS the plugin: .claude-plugin/plugin.json plus the
# agents/, skills/, commands/, contract/, and references/ directories. Claude
# Code (via marketplace/plugin install) and GitHub Copilot CLI (shared plugin
# format, auto-detects .claude-plugin/plugin.json) both read the root directly
# — no mirror needed for them.
#
# .claude/ exists only for the "open the repo directly in Claude Code without
# installing" convenience path. It is GENERATED from root — never edit it by
# hand; run this script instead.
#
# Usage:  ./scripts/sync-claude-mirror.sh [--check]
#   --check  exit non-zero if the mirror is out of date (for CI), no writes
#
set -euo pipefail
cd "$(dirname "$0")/.."

CHECK=0
[[ "${1:-}" == "--check" ]] && CHECK=1

# Canonical root source -> generated .claude/ destination.
mirror_pairs=(
  "agents:.claude/agents"
  "commands:.claude/commands"
  "skills:.claude/skills"
  "references:.claude/references"
)
# Single-file copies (root has more than the mirror needs, e.g. the validator).
file_pairs=(
  "contract/contract.md:.claude/contract/contract.md"
)

if [[ "$CHECK" == "1" ]]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  for pair in "${mirror_pairs[@]}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    mkdir -p "$tmp/$(dirname "$dst")"; cp -R "$src" "$tmp/$dst"
    diff -rq "$tmp/$dst" "$dst" >/dev/null 2>&1 || { echo "✗ out of date: $dst (run sync-claude-mirror.sh)"; exit 1; }
  done
  for pair in "${file_pairs[@]}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    diff -q "$src" "$dst" >/dev/null 2>&1 || { echo "✗ out of date: $dst (run sync-claude-mirror.sh)"; exit 1; }
  done
  echo "✓ .claude/ mirror is up to date"
  exit 0
fi

for pair in "${mirror_pairs[@]}"; do
  src="${pair%%:*}"; dst="${pair##*:}"
  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
done
for pair in "${file_pairs[@]}"; do
  src="${pair%%:*}"; dst="${pair##*:}"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
done

echo "✓ .claude/ mirror regenerated from root sources"
