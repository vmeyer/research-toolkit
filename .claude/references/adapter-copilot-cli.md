# Harness Adapter: Copilot CLI

**Platform id:** `copilot-cli`

**Capabilities:** `parallel: no (sequential dispatch)` · `dispatch: agent profile`
· `done-signal: profile completion` · `resume: file re-validate`.

## Tool capability mapping

Copilot CLI does **not** use Claude tool names. The canonical capabilities map to
Copilot tool names as follows (source of truth: `contract/capabilities.py`):

| Canonical capability | Copilot tool(s) | Notes |
|----------------------|-----------------|-------|
| `read`               | `view` (alias `read`) | native |
| `write`              | `edit`, `create` (alias `write`) | native |
| `web_search`         | `web` (alias `web_search`) | **not native — see below** |
| `web_fetch`          | `web` (aliases `web_fetch`, `fetch`) | **not native — see below** |

Do **not** declare `WebSearch`/`WebFetch`/`Read`/`Write` on a Copilot profile.
Those names are unknown to Copilot CLI, so it registers **nothing** for them —
no permission error, the tools are simply absent. The observed failure is that
`researcher-1`/`verifier-1` end up with only `view`, `create`, `edit`.

## Web tools are not shipped by Copilot CLI

Copilot CLI provides file tools (`view`/`create`/`edit`) but **no web tool** out
of the box. `web_search` and `web_fetch` must be supplied by a **web-capable MCP
server** registered in the Copilot config, exposing a tool named `web` (or
`web_search`/`web_fetch`/`fetch`). Until such a tool is registered, the capability
preflight for research is **BLOCKED** — by design.

URL permissions (`/allow-all`, `--allow-all-urls`) only widen URL access for a
web tool that already exists. They cannot register a missing tool and never turn
a BLOCKED web preflight into PASS.

## Capability preflight (mandatory, before research)

Run the shared preflight from [`capability-model.md`](capability-model.md):

```bash
python -m contract.capabilities copilot-cli view create edit
# -> BLOCKED (web_search, web_fetch missing); exit 1

python -m contract.capabilities copilot-cli web view create edit
# -> PASS; exit 0
```

Then live-probe `web_search`, `web_fetch`, `read`, `write` and record
`preflight/capability-probe.json`. On any BLOCKED capability, set
`state.status: blocked` and stop **before** writing any research artifact. No
`curl`/parent-agent/other-agent/fabricated-source fallback.

## Worker dispatch

- Copilot CLI dispatches profiles **sequentially**. Run each leaf researcher one
  after another — same output folders, same evidence contract, same gate, just
  not parallel. See "Sequenzielle Degradation" in the Claude adapter for the
  identical file/gate contract.
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
