# research-toolkit

A Claude Code plugin for structured, multi-agent web research with parallel execution, source verification, and formatted output generation.

## Installation

**As a plugin (recommended):**
```bash
claude --plugin-dir /path/to/research-toolkit
```

**Or clone and use directly:**
```bash
git clone https://github.com/vmeyer/research-toolkit.git
cd research_template
claude
```

Then run `/research-toolkit:research-and-summarize` (plugin) or `/research-and-summarize` (standalone).

## What it does

You give it a topic. It clarifies what you need, splits the research into parallel tracks, searches the web with a triangulation strategy, verifies and synthesizes the results, and produces formatted reports — all autonomously after the initial intake.

### Pipeline

```
Intake (opus) → N × Researcher (sonnet, parallel) → Verifier (opus) → Formatter(s) (parallel)
```

![Research Pipeline](diagrams/research-pipeline/excalidraw/research-pipeline.png)

**Single interaction point.** The intake agent asks clarifying questions one at a time (max 5). After that, the entire pipeline runs without interruption.

### Agents

| Agent | Model | Role |
|-------|-------|------|
| intake-1 | opus | Clarifies topic iteratively, determines depth/formats/language, splits into 2-4 sub-briefs |
| researcher-1 (×N) | sonnet | Executes one sub-brief each using triangulation search strategy |
| verifier-1 | opus | Merges results, synthesizes themes, verifies quality, fills gaps |
| detailed-1 | sonnet | Comprehensive Markdown report |
| html-report-1 | opus | Styled HTML report from template |
| keypoints-1 | sonnet | Structured key points for skill creation |
| brief-1 | sonnet | Executive summary (2-3 paragraphs) |
| decision-1 | opus | Decision document (ADR style) — recommendation, alternatives, criteria, risks, PoC |
| final-critic-1 | opus | Read-only critic for `assurance: high` runs — checks the draft against the evidence contract |

### Research strategy: Triangulation

Three depth levels, configurable during intake:

- **quick** — 2 query variations, ~5 sources, fast overview
- **standard** (default) — 3-4 query variations, 8-12 sources, 3+ source types, counter-argument search, citation chain following
- **deep** — All of standard plus academic sources, expert tracking, 15+ sources

Every key claim is backed by at least 2 independent sources. Full source traceability from researcher through verifier to final output.

### Evidence-grade orchestration (v3)

v3 adds an evidence-rigor layer on top of the v2 pipeline, controlled by **two
orthogonal dials**:

| Dial | Values | What it controls |
|------|--------|------------------|
| `depth` | `quick` · `standard` · `deep` | How much the researchers search (breadth of sources). |
| `assurance` | `standard` · `high` | How hard the evidence is checked before it ships. |

Every research step now emits a **machine-readable evidence contract** — two
sidecar files, `claims.jsonl` (one atomic claim per line, classified as
`fact` / `inference` / `recommendation` / `gap`) and `sources.jsonl` (one anchored
source per line). A Python validator (`python -m contract.validate_contract <dir>`)
enforces the schema, cross-references, and a dual-source rule for
decision-relevant recommendations. The full contract lives in
[`contract/contract.md`](contract/contract.md).

Runs are **persisted and resumable**. Each run gets a folder under
`research/runs/<run-id>/` with a `brief.md` and a `state.yaml`; the orchestrator
re-validates files on re-entry and continues at the first unfinished step instead
of re-running completed work. `assurance: standard` keeps the v2 behavior
user-visible (sidecars + persistence are added internally). `assurance: high`
additionally runs a **blocking evidence gate**, a targeted **rework loop**
(max 2 rounds), and a read-only **final critic** before any output is formatted.
A new `decision` output format produces an ADR-style decision document from the
verified evidence.

### Output

Reports are saved to `./research/<topic-slug>/` with auto-versioning:

```
./research/webassembly-enterprise-adoption/
  detailed-report-v1.md     # Full report with citations
  report-v1.html            # Styled HTML (from template)
  key-points-v1.md          # Structured for skill creation
  brief-summary-v1.md       # Executive summary
```

All files include YAML frontmatter with topic, date, version, language, sources count, and completeness score.

## Dashboard

After running multiple research sessions, generate an overview page:

```
/research-toolkit:research-dashboard
```

This reads all HTML reports from `./research/` and creates a static `index.html` with links, scores, and summary excerpts.

## Skills

| Skill | Description |
|-------|-------------|
| `research-and-summarize` | Full research pipeline |
| `research-dashboard` | Aggregate HTML reports into dashboard |

## Project structure

```
research-toolkit/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── agents/                      # Agent definitions (plugin)
│   ├── intake-1.md
│   ├── researcher-1.md
│   ├── verifier-1.md
│   ├── detailed-1.md
│   ├── html-report-1.md
│   ├── keypoints-1.md
│   └── brief-1.md
├── skills/                      # Skills (plugin)
│   ├── research-and-summarize/
│   └── research-dashboard/
├── commands/                    # Slash commands (plugin)
├── templates/
│   └── report.html              # HTML report template
├── .claude/                     # Standalone config (for direct use)
│   ├── agents/
│   └── commands/
├── .gemini/skills/              # Gemini CLI support
└── .github/prompts/             # GitHub Copilot support
```

## Cross-platform support

| Platform | How to use |
|----------|------------|
| Claude Code (plugin) | `claude --plugin-dir .` → `/research-toolkit:research-and-summarize` |
| Claude Code (standalone) | Clone repo → `/research-and-summarize` |
| Gemini CLI | Clone repo, skills auto-detected |
| GitHub Copilot CLI | Clone repo, prompts auto-detected (see web-tool requirement below) |

### Harness adapters & capability preflight

Tool names differ per harness, so the pipeline is written against four
**canonical capabilities** — `web_search`, `web_fetch`, `read`, `write` — that
each harness adapter maps to native tool names. The mappings live in
[`contract/capabilities.py`](contract/capabilities.py) and are documented in
[`references/capability-model.md`](references/capability-model.md),
[`references/adapter-claude-code.md`](references/adapter-claude-code.md), and
[`references/adapter-copilot-cli.md`](references/adapter-copilot-cli.md).

The researcher and verifier roles dispatch differently per harness:

| Harness | Researcher / verifier dispatch | Web access | Who writes sidecars |
|---------|-------------------------------|------------|---------------------|
| Claude Code | custom `researcher-1`/`verifier-1` (`WebSearch, WebFetch, Read, Write`) | native | the worker |
| Copilot CLI | built-in **`research`** agent (`agent_type: research`) | native (`web_fetch` + `web_search` via its github-mcp toolset) | the orchestrator (the `research` agent has no write tool) |

On Copilot CLI, run it with `copilot --agent=research --autopilot --allow-all`
(or `/allow-all` + `/autopilot` + `/research …` interactively).

Before any research runs, the orchestrator runs a **two-layer capability
preflight**: static name resolution
(`python -m contract.capabilities <platform> <registered_tool> ...`) **plus a
live probe** that actually calls `web_search`, `web_fetch`, and a write/read
round-trip. If any required capability does not execute, the run is **BLOCKED
before any artifact is written** — no `curl`, parent-agent, other-agent, or
fabricated-source fallback. A search-less run is not an acceptable degradation
for a triangulation pipeline.

> **Why not a custom Copilot agent for web search?** You can — but `web_search`
> is the github-mcp tool `github-mcp-server-web_search`, which only registers
> when the agent engages the github-mcp-server (by declaring `github/*` tools, as
> the built-in `research` agent does). A custom agent that declares a bare
> `web_search` without github/* tools gets only `web_fetch`. Rather than
> re-declare the github-mcp toolset, the toolkit uses the ready-made `research`
> agent.
>
> **URL permissions are not capabilities.** `--allow-all-urls` / `/allow-all`
> only widen which URLs an *existing* web tool may reach; they never provision a
> missing tool.

### Cross-harness mirrors

The canonical v3 sources live in `agents/`, `skills/`, `commands/`, `contract/`,
and `references/`, and are mirrored into `.claude/` for Claude Code. The Copilot
CLI entrypoint (`.github/prompts/`) carries the adapter-selection and capability
preflight so a Copilot run BLOCKS correctly when web tools are missing. The
remaining harness mirrors — `.gemini/`, `.vscode/`, `.agent/`, and `.agents/` —
are **not** updated to the full v3 pipeline in this release and continue to track
v2 until a separate cross-harness sync is performed.

## License

MIT
