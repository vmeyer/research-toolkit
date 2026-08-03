# Harness Adapter: Copilot CLI

**Platform id:** `copilot-cli`

**Capabilities:** `parallel: no (sequential dispatch)` · `dispatch: built-in
research agent (agent_type: research)` · `done-signal: agent completion` ·
`resume: file re-validate`.

## Web research uses the built-in `research` agent

Copilot CLI ships a built-in subagent, **`research`**, that already has working
web access. Under this harness the researcher and verifier roles dispatch to it
(`agent_type: research`) instead of loading our custom `researcher-1`/`verifier-1`
profiles. It runs today:

```bash
# interactive
/allow-all
/autopilot
/research <query>

# non-interactive
copilot --agent=research --autopilot --allow-all -p "<query>"
```

Its declared tools (from `definitions/research.agent.yaml`, verified in 1.0.77):
13 `github/*` tools **+ `web_fetch`, `web_search`, `grep`, `glob`, `view`**.

## Why our custom agent could not web-search (answer to the open question)

Web access in a custom agent is **not impossible** — we defined ours incompletely:

| | Built-in `research` | Our probe (`web_search, web_fetch, view, create, edit`) |
|---|---|---|
| `web_fetch` | ✅ (native builtin) | ✅ worked |
| `web_search` | ✅ | ❌ missing |
| `github/*` tools | ✅ 13 declared → **engages github-mcp-server** | ❌ none declared |
| write (`create`/`edit`) | ❌ not in its tools | ✅ |

`web_search` **is** the github-mcp-server tool `github-mcp-server-web_search`. It
only registers when the github-mcp-server is engaged for the agent — which the
built-in `research` agent triggers by declaring `github/*` tools. Our probe
declared bare `web_search` with **no** `github/*` tools, so github-mcp never
loaded and search never registered. `web_fetch` worked because it is a standalone
builtin. So a custom agent *can* web-search if it also declares `github/*` tools;
we simply use the ready-made `research` agent instead.

## Consequence: the built-in `research` agent cannot write files

Its tool list has **no `create`/`edit`** — it reads and searches, then reports
findings **inline** to the caller. So under Copilot the evidence-contract sidecars
are written by the **orchestrator**, not the worker:

1. Dispatch `agent_type: research` per sub-brief with the sub-brief text, the
   triangulation instructions, and `contract/contract.md` read for the schema.
   It returns prose findings + citations inline.
2. The **orchestrator** (which has `create`/`edit`) writes
   `researchers/sub-NN/{findings.md, claims.jsonl, sources.jsonl}` from those
   findings, following `contract/contract.md`. Same schema, same validator — only
   *who writes* differs from Claude Code (where the worker writes its own files).
3. Verifier step: same pattern — dispatch `agent_type: research` for gap-filling
   web work, then the orchestrator writes `verified/{analysis.md, claims.jsonl,
   sources.jsonl}` (+ `issues.yaml` at `assurance: high`).

This is the single documented divergence from the Claude adapter. Persistence,
resume, the evidence contract, and the gate are otherwise identical.

## Tool capability mapping (verified on Copilot CLI 1.0.76/1.0.77)

Source of truth mirrored in `contract/capabilities.py`:

| Canonical capability | Copilot tool | Availability |
|----------------------|--------------|--------------|
| `read`               | `view`       | ✅ native |
| `write`              | `create` / `edit` | ✅ native (orchestrator) |
| `web_fetch`          | `web_fetch`  | ✅ native builtin |
| `web_search`         | `web_search` (= `github-mcp-server-web_search`) | ✅ via the `research` agent's github-mcp toolset |

## Capability preflight (mandatory, before research)

Static name resolution (necessary, not sufficient):

```bash
python -m contract.capabilities copilot-cli web_search web_fetch view create edit
# -> PASS (names resolve — the live probe is authoritative)
python -m contract.capabilities copilot-cli view create edit
# -> BLOCKED (web_search, web_fetch missing) — the original regression; exit 1
```

**The live probe is authoritative.** Before real research, dispatch
`agent_type: research` once and have it perform one `web_search` and one
`web_fetch`, and confirm the orchestrator can `create`+`view` a probe file.
Record `preflight/capability-probe.json`. If web search or web fetch does not
execute, set `state.status: blocked` and stop **before** writing any research
artifact. No `curl`/parent-agent/other-agent/fabricated-source fallback — a
search-less run is not an acceptable degradation for triangulation.

URL permissions (`/allow-all`, `--allow-all-urls`) only widen URL access for
tools that exist; they never turn a BLOCKED web preflight into PASS.

## Dispatch, "done", state/resume

- **Sequential** dispatch (one `research` agent at a time). Each gets its
  sub-brief, `contract/contract.md`, and its target `researchers/sub-NN/` paths.
- Do not parse stdout for control flow. When the agent returns, the orchestrator
  writes the sidecars, then verifies: `python -m contract.validate_contract
  researchers/sub-NN`.
- `state.yaml` is the source of truth; on re-entry, re-validate referenced files
  and resume at the first step not `done`.
