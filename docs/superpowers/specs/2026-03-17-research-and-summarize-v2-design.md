# research-and-summarize v2 — Design Spec

## Summary

Redesign of the multi-agent research pipeline from 8 agents with mid-flow user questions to a streamlined 5-agent-type / 4-stage pipeline that runs autonomously after a single intake interaction. Key changes: merge analyzer + verifier, remove bullets formatter, add HTML report output, add standalone dashboard skill, enforce source traceability throughout.

## Architecture

### Pipeline Overview

```
Intake (opus) → N × Researcher (sonnet, parallel) → Verifier (opus) → Formatter(s) (parallel)
```

Separate standalone skill: **research-dashboard** (opus)

### Design Principles

1. **Single interaction point**: Only the Intake agent talks to the user. After intake, the pipeline runs to completion without interruption.
2. **Source traceability**: Every claim in every output must link back to a specific source (URL + title). No orphaned facts at any stage.
3. **Parallel where possible**: Researchers run in parallel on sub-briefs. Formatters run in parallel on the verified analysis.
4. **Depth is configurable**: Intake determines research depth (quick/standard/deep) which controls researcher behavior.

## Agent Specifications

### Stage 1: intake-1

**Model:** opus
**Tools:** AskUserQuestion
**Role:** Research intake and planning

**Behavior:**
- Evaluates user input on 4 dimensions: topic clarity, direction/purpose, scope, time focus
- Each dimension gets an internal confidence rating (high/medium/low)
- Asks clarifying questions **one at a time** iteratively until all dimensions are at least medium confidence
- **Max 5 clarifying questions** — if still unclear after 5, proceed with best available understanding and note assumptions in the brief
- Does NOT over-clarify if input is already specific
- Additionally determines:
  - **Research depth**: quick (5 sources) / standard (8-12 sources, triangulation) / deep (15+ sources)
  - **Output formats**: which formatters to run (detailed, html, keypoints, brief — multi-select)
  - **Output language**: language for the final reports
- Splits the research topic into **N sub-briefs** (typically 2-4) based on aspects, perspectives, or sub-questions
- Derives a **topic slug** (lowercase, hyphens) from the topic name for file output

**Output — Research Brief:**
```
## RESEARCH BRIEF

### Topic
### Research Question (central question)
### Direction and Purpose
### Scope Boundaries (in/out/depth preference)
### Time Focus (recent only | last 2-5 years | historical + recent | no constraint)
### Priority Sources or Angles
### User's Existing Knowledge
### Configuration
- depth: quick | standard | deep
- output_formats: [detailed, html, keypoints, brief]
- language: <language code>
- slug: <topic-slug>

### Sub-Briefs
#### Sub-Brief 1: <aspect>
Focus, specific search angles, expected source types
#### Sub-Brief 2: <aspect>
...
```

### Stage 2: researcher-1..N (parallel)

**Model:** sonnet
**Tools:** WebSearch, WebFetch, Read
**Role:** Execute one sub-brief each, in parallel

**Parallelism mechanism:** The orchestrating skill (SKILL.md / slash command) reads the sub-briefs from the intake output and spawns one `researcher-1` Agent call per sub-brief in a single message (Claude Code executes multiple Agent tool calls in one turn in parallel). All researcher instances use the same agent definition (`researcher-1.md`) — the sub-brief content passed in the prompt differentiates them. This is a runtime fan-out, not a static workflow definition.

**Search Strategy — Triangulation (default / standard depth):**
1. Generate 3-4 search query variations (synonyms, English/German, technical terms)
2. Enforce source diversity: minimum 3 different source types (news, academic/professional publication, official docs, industry reports)
3. Every key claim backed by ≥2 independent sources
4. WebFetch on at least 3-5 sources for depth (don't rely on snippets)
5. Follow citation chains: if Source A references Study B, also fetch Study B
6. Explicitly search for counter-arguments ("criticism of X", "problems with X")

**Depth variants:**
- **quick**: 2 search variations, top 3 results scanned, 1-2 WebFetch, ~5 sources total
- **standard**: Full triangulation as above, 8-12 sources
- **deep**: All of standard, plus systematic academic search, temporal layering (current + historical), identify and follow key authors/experts, 15+ sources

**Output — Research Handoff:**
```
## RESEARCH HANDOFF: Researcher → Verifier

### Sub-Brief Reference
### Sources Consulted
For each: Title, URL, Type (news/academic/official/industry/blog), Reliability (high/medium/low), Date accessed
### Key Facts
Numbered list. Each fact cites [Source N].
### Perspectives and Viewpoints
### Counter-Arguments Found
### Recent Developments
### Raw Data and Statistics
### Gaps and Limitations
### Open Questions
```

### Stage 3: verifier-1

**Model:** opus
**Tools:** WebSearch, WebFetch, Read
**Role:** Synthesize parallel research results, analyze, and verify

**Process:**
1. **Merge** all Research Handoffs into unified view
2. **Cross-reference** facts across sources and sub-briefs
3. **Identify 3-5 themes** with confidence levels
4. **Weigh source reliability** — flag single-source claims
5. **Check brief alignment** — does research answer the original Research Question? Were scope boundaries respected?
6. **Fill gaps** — use WebSearch/WebFetch to resolve remaining unknowns or verify dubious claims
7. **Build source index** — unified, deduplicated list of all sources with reliability ratings
8. **Assess completeness** — score 1-10

**Output — Verified Analysis Handoff:**
```
## VERIFIED ANALYSIS HANDOFF: Verifier → Formatters

### Verification Summary
- Completeness score (1-10)
- Brief alignment assessment
- Sources total / Sources added by verifier
- Gaps filled

### Source Index
Complete deduplicated list: [ID] Title, URL, Type, Reliability, Used by (sub-briefs)

### Themes
For each theme:
- Theme name
- Key findings (citing [Source ID])
- Confidence level (high/medium/low)
- Supporting sources

### Contradictions and Tensions
### Key Takeaways (max 7)
### Remaining Unknowns (verified as unresolvable)

### Original Configuration (passed through)
- output_formats, language, topic, slug
```

### Stage 4: Formatters (parallel, only selected ones run)

#### detailed-1

**Model:** sonnet
**Tools:** Bash, Write, Glob, Read
**Role:** Produce comprehensive Markdown report

**Sections:** Introduction, Methodology, Findings by Theme, Analysis, Contradictions, Conclusions, References (full source list with URLs)

**File output:** `./research/<slug>/detailed-report-v<N>.md` with YAML frontmatter:
```yaml
---
type: detailed-report
topic: <topic>
date: <YYYY-MM-DD>
version: <N>
language: <lang>
sources_count: <N>
completeness_score: <N>
---
```

#### html-report-1

**Model:** opus
**Tools:** Bash, Write, Glob, Read
**Role:** Produce styled HTML report based on template

Reads the HTML template from `templates/report.html`, fills it with the verified analysis data. The template defines layout, typography, and styling. The agent populates content sections while preserving the template structure.

**Template placeholder convention:** The template uses HTML comments as section markers: `<!-- SECTION:title -->`, `<!-- SECTION:summary -->`, `<!-- SECTION:themes -->`, `<!-- SECTION:sources -->`, `<!-- SECTION:metadata -->`, etc. The agent replaces the content between matching `<!-- SECTION:xxx -->` and `<!-- /SECTION:xxx -->` markers. The template skeleton:

```html
<!DOCTYPE html>
<html lang="{{language}}">
<head>
  <meta charset="utf-8">
  <meta name="topic" content="...">
  <meta name="date" content="...">
  <meta name="version" content="...">
  <meta name="completeness-score" content="...">
  <meta name="sources-count" content="...">
  <title><!-- SECTION:title --><!-- /SECTION:title --></title>
  <style>/* Report styling */</style>
</head>
<body>
  <header><!-- SECTION:title --><!-- /SECTION:title --></header>
  <section id="summary"><!-- SECTION:summary --><!-- /SECTION:summary --></section>
  <section id="themes"><!-- SECTION:themes --><!-- /SECTION:themes --></section>
  <section id="contradictions"><!-- SECTION:contradictions --><!-- /SECTION:contradictions --></section>
  <section id="takeaways"><!-- SECTION:takeaways --><!-- /SECTION:takeaways --></section>
  <section id="unknowns"><!-- SECTION:unknowns --><!-- /SECTION:unknowns --></section>
  <section id="sources"><!-- SECTION:sources --><!-- /SECTION:sources --></section>
</body>
</html>
```

**File output:** `./research/<slug>/report-v<N>.html` with metadata embedded in HTML meta tags.

#### keypoints-1

**Model:** sonnet
**Tools:** Bash, Write, Glob, Read
**Role:** Extract structured key points optimized for skill creation

**Structure:** Topic/Method Name, Core Concept, Key Principles (max 10), Patterns and Techniques (name, when to use, how it works, pitfalls), Decision Framework, Practical Examples, References.

**File output:** `./research/<slug>/key-points-v<N>.md` with YAML frontmatter.

#### brief-1

**Model:** sonnet
**Tools:** Bash, Write, Glob, Read
**Role:** Executive summary, 2-3 paragraphs with source citations

**File output:** `./research/<slug>/brief-summary-v<N>.md` with YAML frontmatter.

### File Output Convention (all formatters)

1. Read slug from the Verified Analysis Handoff configuration
2. Create output directory via Bash `mkdir -p ./research/<slug>` (formatters need **Bash** tool for this)
3. Glob for existing versions of the output type
4. Auto-increment version number
5. Write with YAML frontmatter
6. Confirm written file path in agent output

## Standalone Skill: research-dashboard

**Model:** opus
**Tools:** Glob, Read, Write
**Trigger:** Separate slash command `/research-dashboard`

**Behavior:**
1. Glob `./research/**/*.html` to find all HTML reports
2. Read each report's metadata (title, topic, date, sources count, completeness score)
3. Generate static `./research/index.html` with:
   - Overview table of all research topics
   - Per-topic: title, date, completeness score, source count, link to HTML report
   - Brief summary excerpt per topic
   - Clean, readable styling (self-contained CSS)

## Handoff Document Chain (traceability)

```
Research Brief (intake)
  ↓ contains: topic, scope, sub-briefs, config
Research Handoff × N (researchers)
  ↓ contains: facts with [Source N] citations, source list with URLs
Verified Analysis Handoff (verifier)
  ↓ contains: deduplicated Source Index, themes with [Source ID] refs
Final Outputs (formatters)
  → contains: full references section with clickable URLs
```

Every fact at every stage is traceable back to a specific URL.

## Changes from v1

| What | v1 | v2 |
|------|----|----|
| Agents | 8 (intake, researcher, analyzer, verifier, brief, detailed, bullets, keypoints) | 5 types (intake, researcher, verifier, formatters × 4, dashboard) |
| Analyzer | Separate agent, no tools | Merged into verifier |
| Verifier | Optional (user chooses) | Always runs |
| Bullets formatter | Separate agent | Removed (overlap with keypoints) |
| User interaction | Intake + 2 mid-flow questions | Intake only, then autonomous |
| Researchers | Single | N parallel (sub-brief splitting) |
| Search strategy | Undefined | Triangulation with 3 depth levels |
| Source traceability | Not enforced | Enforced at every stage |
| HTML output | None | New: html-report-1 with template |
| Dashboard | None | New: standalone skill |
| Output format selection | Mid-flow question | Intake determines upfront |
| Language | Implicit English | Configurable via intake |

## New Files Required

- `templates/report.html` — HTML report template (first draft, iterative refinement expected)
- `.claude/agents/html-report-1.md` — New agent definition
- `.claude/commands/research-dashboard.md` — New slash command
- `.claude/agents/research-dashboard.md` — New agent definition (if needed as sub-agent)

## Files to Modify

### Core Agent Definitions
- `.claude/agents/intake-1.md` — Rewrite: iterative clarification, sub-brief splitting, config fields, model → opus
- `.claude/agents/researcher-1.md` — Rewrite: triangulation strategy, depth variants, structured handoff
- `.claude/agents/verifier-1.md` — Rewrite: merge analyzer role, source index, completeness scoring
- `.claude/agents/detailed-1.md` — Enhance: proper section structure, source references
- `.claude/agents/keypoints-1.md` — Minor update: model change (opus → sonnet)
- `.claude/agents/brief-1.md` — Minor update: source citations

### Skill & Command Definitions
- `.agent/skills/research-and-summarize/SKILL.md` — Rewrite: new flow, remove mid-flow questions, add parallel researcher fan-out logic
- `.claude/commands/research-and-summarize.md` — Rewrite: match new SKILL.md

### Workflow JSON
- `.vscode/workflows/research-and-summarize.json` — Rewrite: remove analyzer node, remove ask_verify/ask_format nodes, add html-report-1 node, update connections. Note: parallel researcher fan-out is handled at runtime by the skill, not in the static workflow JSON.

### Cross-Platform Exports (keep in sync)
- `.gemini/skills/` — Update to match new agent definitions and flow
- `.github/prompts/` — Update to match new agent definitions and flow
- `.agent/skills/` — Already covered above

## Files to Delete

- `.claude/agents/analyzer-1.md`
- `.claude/agents/bullets-1.md`
