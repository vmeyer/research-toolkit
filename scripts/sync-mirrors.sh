#!/usr/bin/env bash
#
# Regenerate all generated artifacts from the canonical root plugin sources.
#
# The repository root IS the plugin: .claude-plugin/plugin.json plus the
# agents/, skills/, commands/, contract/, and references/ directories. This is
# the single source of truth. Claude Code (via marketplace/plugin install) and
# GitHub Copilot CLI (shared plugin format, auto-detects .claude-plugin/
# plugin.json) both read the root directly — no mirror needed for them.
#
# This script generates:
#   1. .claude/                  — Claude Code standalone mirror, for the
#                                  "open the repo without installing" path.
#   2. .codex-plugin/plugin.json — Codex CLI manifest (Codex reads only this,
#                                  never .claude-plugin/plugin.json). Derived
#                                  from plugin.json + a skills pointer. Codex
#                                  plugins consume skills only (no agents).
#
# Never edit generated files by hand — change the root sources and re-run.
#
# Usage:  ./scripts/sync-mirrors.sh [--check]
#   --check  exit non-zero if any generated artifact is out of date (for CI),
#            without writing anything.
#
set -euo pipefail
cd "$(dirname "$0")/.."

CHECK=0
[[ "${1:-}" == "--check" ]] && CHECK=1

# --- .claude/ standalone mirror -------------------------------------------
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

# --- .codex-plugin/plugin.json --------------------------------------------
# Emit the Codex manifest to stdout, derived from the canonical plugin.json so
# name/version/description/author/repo stay in sync automatically. Codex only
# consumes skills, so the sole component pointer is "skills".
codex_manifest() {
  python3 - <<'PY'
import json
with open(".claude-plugin/plugin.json") as f:
    p = json.load(f)
out = {"name": p["name"], "version": p["version"], "description": p["description"]}
if "author" in p:
    out["author"] = p["author"]
for k in ("homepage", "repository", "license"):
    if k in p:
        out[k] = p[k]
out["skills"] = "./skills/"
print(json.dumps(out, indent=2))
PY
}

if [[ "$CHECK" == "1" ]]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  for pair in "${mirror_pairs[@]}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    mkdir -p "$tmp/$(dirname "$dst")"; cp -R "$src" "$tmp/$dst"
    diff -rq "$tmp/$dst" "$dst" >/dev/null 2>&1 || { echo "✗ out of date: $dst (run sync-mirrors.sh)"; exit 1; }
  done
  for pair in "${file_pairs[@]}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    diff -q "$src" "$dst" >/dev/null 2>&1 || { echo "✗ out of date: $dst (run sync-mirrors.sh)"; exit 1; }
  done
  diff <(codex_manifest) .codex-plugin/plugin.json >/dev/null 2>&1 || { echo "✗ out of date: .codex-plugin/plugin.json (run sync-mirrors.sh)"; exit 1; }
  echo "✓ generated artifacts are up to date"
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
mkdir -p .codex-plugin
codex_manifest > .codex-plugin/plugin.json

echo "✓ regenerated .claude/ and .codex-plugin/plugin.json from root sources"
