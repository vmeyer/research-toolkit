# Harness Adapter: Copilot CLI

**Platform id:** `copilot-cli`

**Capabilities:** `parallel: no (sequential dispatch)` · `dispatch: agent profile`
· `done-signal: profile completion` · `resume: file re-validate`.

## Tool capability mapping (verified on Copilot CLI 1.0.76)

Copilot's canonical tool names differ from Claude's. Source of truth mirrored in
`contract/capabilities.py`:

| Canonical capability | Copilot tool | Availability (tested) |
|----------------------|--------------|-----------------------|
| `read`               | `view`       | ✅ native |
| `write`              | `create` / `edit` | ✅ native |
| `web_fetch`          | `web_fetch`  | ✅ native builtin — **works** |
| `web_search`         | `web_search` (= GitHub-MCP `github-mcp-server-web_search`) | ⚠️ **plan/org-gated — may be absent** |

**Verified behaviour** (live probe against the installed CLI):

- Declaring `web_fetch` in a custom agent → the agent fetched `https://example.com`
  and returned `<title>Example Domain</title>`. `web_fetch` is a real builtin.
- `web_search` is **not a plain builtin**. It is the GitHub-MCP tool
  `github-mcp-server-web_search`. In testing it was unavailable **even on the
  default agent with `--enable-all-github-mcp-tools`** — the agent reported "only
  web_fetch". Whether it exists depends on the account/org GitHub-MCP entitlement.

So Copilot has native **web fetch** but **web search is not guaranteed**. If your
environment does not expose `web_search`, provision it (enable the GitHub-MCP
`web_search` tool for the account, or register a search-capable MCP server) — or
the research run will (correctly) BLOCK; see below.

## Root cause of the "only view/create/edit" failure

The originally-reported failure was that profiles declared **Claude** tool names
(`WebSearch, WebFetch, Read`) that Copilot's custom-agent loader did not
recognize; it dropped them and fell back to default file tools
(`view`/`create`/`edit`). No permission error — the web tools were never
registered for the agent. (See github/copilot-sdk#1641: tool sets differ across
Copilot surfaces.)

**Fix:** declare **canonical Copilot names** in the profile. The shared
`agents/*.md` profiles declare **both** name sets (Claude + Copilot) so a single
file works on both harnesses; each harness ignores names it does not recognize:

```yaml
tools: WebSearch, WebFetch, Read, Write, web_search, web_fetch, view, create, edit
```

This reliably restores `web_fetch`/`view`/`create`/`edit`. `web_search` resolves
only where the environment actually provides the GitHub-MCP web_search tool — the
live preflight below is what confirms it.

## Capability preflight (mandatory, before research)

Static name resolution first (necessary, not sufficient):

```bash
python -m contract.capabilities copilot-cli web_search web_fetch view create edit
# -> PASS; exit 0  (names resolve — but see the live probe below)

python -m contract.capabilities copilot-cli view create edit
# -> BLOCKED (web_search, web_fetch missing) — the reported regression; exit 1
```

**The live probe is authoritative.** On Copilot, a static PASS does not prove
`web_search` runs — the name may resolve while the GitHub-MCP web_search tool is
not actually provisioned. So after static resolution, actually call each
capability once (`web_search`, `web_fetch`, and a `write`+`read` round-trip) and
record `preflight/capability-probe.json`. If `web_search` (or any required
capability) does not execute, treat it as BLOCKED: set `state.status: blocked`
and stop **before** writing any research artifact. No `curl`/parent-agent/
other-agent/fabricated-source fallback — a search-less "research" run is not an
acceptable degradation for a triangulation pipeline.

URL permissions (`/allow-all`, `--allow-all-urls`) only widen URL access for
tools that exist; they cannot provision the GitHub-MCP web_search tool and never
turn a BLOCKED web preflight into PASS.

## Worker dispatch

- Copilot CLI dispatches profiles **sequentially**. Run each leaf researcher one
  after another — same output folders, same evidence contract, same gate, just
  not parallel.
- Each worker gets its sub-brief, the path to `contract/contract.md` (read, do
  not copy), its exclusive `researchers/sub-NN/` folder, and the absolute output
  paths (`findings.md`, `claims.jsonl`, `sources.jsonl`).
- Workers persist their own output; the orchestrator never reconstructs missing
  output from a profile's chat reply.

## "done" detection

- Do not parse stdout. Treat a profile as done when it returns, then verify the
  sidecars exist and parse: `python -m contract.validate_contract researchers/sub-NN`.

## State/Resume

- `state.yaml` is the source of truth. On re-entry: read it, re-validate the
  referenced files, and resume at the first step not marked `done`. Persistence,
  resume, and the evidence contract are identical to Claude Code — only dispatch
  and tool names differ.
