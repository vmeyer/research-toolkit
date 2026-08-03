# Harness Adapter: Copilot CLI

**Platform id:** `copilot-cli`

**Capabilities:** `parallel: no (sequential dispatch)` · `dispatch: agent profile`
· `done-signal: profile completion` · `resume: file re-validate`.

## Tool capability mapping

Copilot CLI ships **native** web and file tools. Its canonical tool names differ
from Claude's; the bundled Copilot SDK carries this alias table (verified against
`~/.copilot/pkg/universal/*/app.js`) — source of truth mirrored in
`contract/capabilities.py`:

| Canonical capability | Copilot native tool | Claude alias |
|----------------------|---------------------|--------------|
| `web_search`         | `web_search`        | `WebSearch`  |
| `web_fetch`          | `web_fetch`         | `WebFetch`   |
| `read`               | `view`              | `Read`       |
| `write`              | `create` / `edit`   | `Write` / `Edit` |

So Copilot CLI **does** provide web search and web fetch out of the box — no MCP
server is required for research. (Confirmed by the bundled SDK, by Copilot's own
built-in `research` agent which declares `web_search`/`web_fetch`/`view`, and by
real session logs.)

## Root cause of the "only view/create/edit" failure

The failure was **not** a missing web tool. `researcher-1`/`verifier-1` declared
Claude tool names (`WebSearch, WebFetch, Read`) in their profile `tools:` field.
Copilot's custom-agent loader does not reliably resolve Claude names in that
field, dropped the unrecognized web names, and fell back to its default file
tools (`view`/`create`/`edit`). No permission error — the web tools were never
registered for the agent. (See github/copilot-sdk#1641: the tool set can differ
across Copilot surfaces.)

**Fix:** declare the **canonical Copilot names** in the profile, exactly like
Copilot's own research agent does:

```yaml
tools: web_search, web_fetch, view, create, edit
```

The shared `agents/*.md` profiles declare **both** name sets (Claude + Copilot)
so a single file works on both harnesses; unrecognized names are ignored per
harness. Do not rely on the alias map alone.

## Capability preflight (mandatory, before research)

Run the shared preflight from [`capability-model.md`](capability-model.md):

```bash
python -m contract.capabilities copilot-cli web_search web_fetch view create edit
# -> PASS; exit 0

python -m contract.capabilities copilot-cli view create edit
# -> BLOCKED (web_search, web_fetch missing) — the exact regression; exit 1
```

Then live-probe `web_search`, `web_fetch`, `read`, `write` and record
`preflight/capability-probe.json`. On any BLOCKED capability, set
`state.status: blocked` and stop **before** writing any research artifact. No
`curl`/parent-agent/other-agent/fabricated-source fallback.

URL permissions (`/allow-all`, `--allow-all-urls`) only widen URL access for the
existing web tools; they cannot register a tool the profile failed to request and
never turn a BLOCKED web preflight into PASS.

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
