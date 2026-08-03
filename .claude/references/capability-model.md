# Capability Model & Preflight Gate

The research pipeline is harness-agnostic. `researcher-1` and `verifier-1` do
not depend on specific tool *names*; they depend on four **canonical, platform-
neutral capabilities**:

| Canonical capability | What the agent must be able to do |
|----------------------|-----------------------------------|
| `web_search`         | Run a web search query            |
| `web_fetch`          | Fetch the contents of a URL       |
| `read`               | Read a file from disk             |
| `write`              | Create/overwrite a file on disk   |

Each platform adapter maps every canonical capability to the tool name(s) that
satisfy it on that harness. The single source of truth for these mappings is
[`contract/capabilities.py`](../contract/capabilities.py) (`ADAPTERS`); the
adapter docs (`adapter-claude-code.md`, `adapter-copilot-cli.md`) describe them
in prose. Keep the two in sync.

## Adapter selection

The orchestrator selects the adapter for the harness it is running under:

- Claude Code → `references/adapter-claude-code.md` (`platform: claude-code`)
- Copilot CLI → `references/adapter-copilot-cli.md` (`platform: copilot-cli`)

If the harness is unknown, treat it as **BLOCKED** — do not guess tool names.

## Capability preflight (runs before any research)

Before dispatching researchers, the orchestrator MUST run a preflight that
proves the required capabilities are actually callable — first for itself, then
confirmed inside `researcher-1` and `verifier-1`, which share the same required
set (`web_search`, `web_fetch`, `read`, `write`).

Two layers, both required:

1. **Static resolution.** Resolve the harness's *registered* tools against the
   selected adapter:

   ```bash
   python -m contract.capabilities <platform> <registered_tool> ...
   # exit 0 = PASS, exit 1 = BLOCKED
   ```

   A capability with no matching registered tool is BLOCKED. This is not a
   permission error — the tool simply is not registered.

2. **Live probe.** For a PASS result, the agent performs one trivial call of
   each capability to prove it is wired end-to-end, not merely declared:
   - `web_search`: a throwaway query (e.g. `"example.com"`).
   - `web_fetch`: fetch one stable URL (e.g. `https://example.com`).
   - `read` / `write`: write a probe file into the run's `preflight/` folder and
     read it back.

   Record the outcome in `preflight/capability-probe.json`
   (`platform`, `status`, `resolved`, `missing`).

## BLOCKED semantics — no fallbacks

If either layer fails for `web_search`, `web_fetch`, `read`, or `write`:

- Set `state.status: blocked` with a documented cause **before any research
  artifact is written**. The output folders (`researchers/sub-*/`, `verified/`)
  stay empty — no `findings.md`, `claims.jsonl`, or `sources.jsonl`.
- Do **not** work around a missing tool. Forbidden fallbacks include: shelling
  out to `curl`/`wget`, asking the parent agent to fetch, delegating to another
  research agent, or fabricating sources/quotes. A missing capability is a hard
  stop, not a degradation.

## URL permissions are not capabilities

`--allow-all-urls` (Claude Code) and `/allow-all` (Copilot CLI) only widen which
URLs an **already-registered** web tool may reach. They cannot register a tool
the harness never provided. If `web_fetch`/`web_search` are missing, granting URL
permissions changes nothing — the preflight stays BLOCKED until a web-capable
tool is registered.
