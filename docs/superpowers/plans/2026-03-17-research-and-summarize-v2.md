# research-and-summarize v2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the multi-agent research pipeline from 8 agents to a streamlined 5-agent-type / 4-stage pipeline with parallel researchers, mandatory verification, HTML output, and a dashboard skill.

**Architecture:** Intake (opus) → N × Researcher (sonnet, parallel) → Verifier (opus, merged analyzer+verifier) → Formatter(s) (parallel). Single user interaction point at intake. Source traceability enforced throughout.

**Tech Stack:** Claude Code agents (markdown definitions), CC Workflow Studio (JSON workflow), HTML/CSS (report template)

**Spec:** `docs/superpowers/specs/2026-03-17-research-and-summarize-v2-design.md`

---

### Task 1: Delete Obsolete Agents

**Files:**
- Delete: `.claude/agents/analyzer-1.md`
- Delete: `.claude/agents/bullets-1.md`

- [ ] **Step 1: Delete analyzer-1.md**

```bash
rm .claude/agents/analyzer-1.md
```

- [ ] **Step 2: Delete bullets-1.md**

```bash
rm .claude/agents/bullets-1.md
```

- [ ] **Step 3: Commit**

```bash
git add -u .claude/agents/analyzer-1.md .claude/agents/bullets-1.md
git commit -m "chore: remove analyzer-1 and bullets-1 agents (merged/removed in v2)"
```

---

### Task 2: Rewrite intake-1 Agent

**Files:**
- Modify: `.claude/agents/intake-1.md`

The intake agent is completely rewritten: model changes from sonnet to opus, gains iterative clarification logic (max 5 questions), output format selection, depth configuration, language setting, sub-brief splitting, and slug derivation. See spec section "Stage 1: intake-1" for the full behavior definition and output format.

- [ ] **Step 1: Rewrite intake-1.md**

Replace the entire content of `.claude/agents/intake-1.md` with the new agent definition. The frontmatter must set:
- `name: intake-1`
- `description: Clarify research topic iteratively and produce research brief with sub-briefs`
- `tools: AskUserQuestion`
- `model: opus`
- `color: pink`

The prompt body must implement:
1. **Evaluate input** on 4 dimensions (topic clarity, direction/purpose, scope, time focus) with internal confidence ratings
2. **Iterative clarification** — one question at a time, max 5 questions, stop early if confident
3. **Configuration gathering** — research depth (quick/standard/deep), output formats (multi-select from: detailed, html, keypoints, brief), output language
4. **Sub-brief splitting** — divide topic into 2-4 sub-briefs with focus areas and search angles
5. **Slug derivation** — lowercase, hyphens, no special chars
6. **Output format** — the exact RESEARCH BRIEF template from the spec with all sections including Configuration block (depth, output_formats, language, slug) and Sub-Briefs

- [ ] **Step 2: Verify agent file is valid**

```bash
head -10 .claude/agents/intake-1.md
```

Expected: valid YAML frontmatter with `model: opus`

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/intake-1.md
git commit -m "feat: rewrite intake-1 with iterative clarification and sub-brief splitting"
```

---

### Task 3: Rewrite researcher-1 Agent

**Files:**
- Modify: `.claude/agents/researcher-1.md`

Completely rewritten with triangulation search strategy, three depth variants, counter-argument search, citation chain following, and structured Research Handoff output. See spec section "Stage 2: researcher-1..N" for details.

- [ ] **Step 1: Rewrite researcher-1.md**

Replace the entire content. Frontmatter:
- `name: researcher-1`
- `description: Research a sub-brief using web search with triangulation strategy`
- `tools: WebSearch, WebFetch, Read`
- `model: sonnet`
- `color: blue`

The prompt must include:
1. **Role definition** — receives a single Sub-Brief (not the full Research Brief), executes it
2. **Triangulation strategy (standard/default)** — all 6 steps from spec: query variations, source diversity (3+ types), dual-source backing, WebFetch depth, citation chains, counter-arguments
3. **Depth variants** — quick/standard/deep with specific parameters from spec
4. **Output format** — exact RESEARCH HANDOFF template from spec (Sub-Brief Reference, Sources Consulted with Type/Reliability/Date, Key Facts with [Source N] citations, Perspectives, Counter-Arguments, Recent Developments, Raw Data, Gaps, Open Questions)

- [ ] **Step 2: Verify**

```bash
head -10 .claude/agents/researcher-1.md
```

Expected: frontmatter with `model: sonnet`, `tools: WebSearch, WebFetch, Read`

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/researcher-1.md
git commit -m "feat: rewrite researcher-1 with triangulation strategy and depth variants"
```

---

### Task 4: Rewrite verifier-1 Agent (merged Analyzer + Verifier)

**Files:**
- Modify: `.claude/agents/verifier-1.md`

Major rewrite: now performs both analysis (synthesize themes, cross-reference) and verification (gap-filling, brief alignment). Receives N Research Handoffs from parallel researchers. See spec section "Stage 3: verifier-1".

- [ ] **Step 1: Rewrite verifier-1.md**

Replace entire content. Frontmatter:
- `name: verifier-1`
- `description: Synthesize parallel research results, analyze themes, and verify quality`
- `tools: WebSearch, WebFetch, Read`
- `model: opus`
- `color: yellow`

The prompt must implement all 8 process steps from the spec:
1. Merge all Research Handoffs
2. Cross-reference facts across sources and sub-briefs
3. Identify 3-5 themes with confidence levels
4. Weigh source reliability, flag single-source claims
5. Check brief alignment
6. Fill gaps via WebSearch/WebFetch
7. Build deduplicated Source Index with [ID] format
8. Assess completeness (1-10 score)

Output: exact VERIFIED ANALYSIS HANDOFF template from spec, including Source Index, Themes with [Source ID] refs, and Original Configuration pass-through (output_formats, language, topic, slug).

- [ ] **Step 2: Verify**

```bash
head -10 .claude/agents/verifier-1.md
```

Expected: frontmatter with `model: opus`

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/verifier-1.md
git commit -m "feat: rewrite verifier-1 as merged analyzer+verifier with source index"
```

---

### Task 5: Create HTML Report Template

**Files:**
- Create: `templates/report.html`

First draft of the HTML template used by html-report-1 agent. Uses `<!-- SECTION:xxx -->` / `<!-- /SECTION:xxx -->` comment markers as documented in the spec. Self-contained CSS, responsive, clean typography.

- [ ] **Step 1: Create templates directory**

```bash
mkdir -p templates
```

- [ ] **Step 2: Write templates/report.html**

Create the full HTML template with:
- `<!DOCTYPE html>` with `lang="{{language}}"` attribute
- Meta tags for topic, date, version, completeness-score, sources-count
- Self-contained `<style>` block with clean, readable typography (system fonts, good line-height, max-width for readability)
- Section markers using the convention: `<!-- SECTION:name --><!-- /SECTION:name -->`
- Required sections: title, summary, themes, contradictions, takeaways, unknowns, sources
- Responsive design (looks good on both desktop and mobile)
- Source section should use a numbered list format matching the Source Index [ID] convention

- [ ] **Step 3: Verify template has all section markers**

```bash
grep -c "SECTION:" templates/report.html
```

Expected: at least 14 (7 section pairs × 2 markers each)

- [ ] **Step 4: Commit**

```bash
git add templates/report.html
git commit -m "feat: add HTML report template with section markers"
```

---

### Task 6: Create html-report-1 Agent

**Files:**
- Create: `.claude/agents/html-report-1.md`

New agent that reads the template from `templates/report.html` and fills section markers with verified analysis data. See spec section "html-report-1".

- [ ] **Step 1: Write html-report-1.md**

Create with frontmatter:
- `name: html-report-1`
- `description: Produce styled HTML report from template`
- `tools: Bash, Write, Glob, Read`
- `model: opus`
- `color: teal`

The prompt must instruct the agent to:
1. Read the template from `templates/report.html`
2. Fill content between `<!-- SECTION:xxx -->` and `<!-- /SECTION:xxx -->` markers
3. Replace `{{language}}` in the html lang attribute
4. Populate meta tags with actual values
5. Format themes as structured HTML (headings, paragraphs, confidence badges)
6. Format sources as a numbered reference list with clickable URLs
7. Follow the standard file output convention: read slug from config, mkdir, glob for versions, auto-increment, write to `./research/<slug>/report-v<N>.html`

- [ ] **Step 2: Verify**

```bash
head -10 .claude/agents/html-report-1.md
```

Expected: frontmatter with `model: opus`

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/html-report-1.md
git commit -m "feat: add html-report-1 agent with template rendering"
```

---

### Task 7: Update Remaining Formatter Agents

**Files:**
- Modify: `.claude/agents/detailed-1.md`
- Modify: `.claude/agents/keypoints-1.md`
- Modify: `.claude/agents/brief-1.md`

Update all three formatters: add source citation requirements, use slug from config instead of deriving it, update keypoints model to sonnet.

- [ ] **Step 1: Rewrite detailed-1.md**

Enhance the prompt to include:
- Full section list from spec: Introduction, Methodology, Findings by Theme, Analysis, Contradictions, Conclusions, References
- All source citations must use [Source ID] format from the Verified Analysis Handoff
- References section must include full URLs
- YAML frontmatter must include: type, topic, date, version, language, sources_count, completeness_score
- Read slug from Verified Analysis Handoff configuration (not derive independently)
- Language from configuration

Keep frontmatter: `model: sonnet`, `tools: Bash, Write, Glob, Read`, `color: orange`

- [ ] **Step 2: Rewrite keypoints-1.md**

Update:
- Change `model: opus` → `model: sonnet` in frontmatter
- Enhance prompt with full structure from spec: Topic/Method Name, Core Concept, Key Principles (max 10), Patterns and Techniques (with name/when/how/pitfalls), Decision Framework, Practical Examples, References with URLs
- Read slug from config
- Source traceability in references

Keep: `tools: Bash, Write, Glob, Read`, `color: red`

- [ ] **Step 3: Rewrite brief-1.md**

Update:
- Add explicit source citation requirement using [Source ID] format
- Read slug from config
- YAML frontmatter includes language field

Keep: `model: sonnet`, `tools: Bash, Write, Glob, Read`, `color: green`

- [ ] **Step 4: Verify model changes**

```bash
grep "model:" .claude/agents/keypoints-1.md
```

Expected: `model: sonnet`

- [ ] **Step 5: Commit**

```bash
git add .claude/agents/detailed-1.md .claude/agents/keypoints-1.md .claude/agents/brief-1.md
git commit -m "feat: enhance formatters with source traceability and config-based slug"
```

---

### Task 8: Rewrite Orchestration Skill (SKILL.md + Commands)

**Files:**
- Modify: `.agent/skills/research-and-summarize/SKILL.md`
- Modify: `.claude/commands/research-and-summarize.md`

This is the critical orchestration file. It must implement the new flow: intake → parse sub-briefs → fan-out N researchers in parallel → collect results → verifier → parse output_formats from config → fan-out selected formatters in parallel.

- [ ] **Step 1: Rewrite `.agent/skills/research-and-summarize/SKILL.md`**

The skill must:
1. Update the Mermaid diagram to the new flow (no analyzer, no ask nodes, parallel researchers, html-report-1)
2. Define execution instructions that explain the runtime fan-out:
   - After intake completes, parse the Research Brief to extract sub-briefs and configuration
   - Spawn one `researcher-1` Agent per sub-brief in a single message (parallel execution)
   - Collect all Research Handoffs, pass them to `verifier-1`
   - After verifier completes, read `output_formats` from configuration
   - Spawn only the selected formatters in parallel
3. Remove all AskUserQuestion node details (no mid-flow questions)
4. Update all agent descriptions, models, and prompts to match new definitions
5. Add html-report-1 to the formatter section

- [ ] **Step 2: Rewrite `.claude/commands/research-and-summarize.md`**

This is the Claude Code slash command. Must match the SKILL.md content but adapted for the Claude Code command format:
- Same Mermaid diagram
- Same execution flow
- Use Claude Code-specific terminology (Agent tool for sub-agents, AskUserQuestion tool for intake)

- [ ] **Step 3: Verify new flow diagram**

```bash
grep -c "analyzer" .agent/skills/research-and-summarize/SKILL.md
```

Expected: 0 (analyzer completely removed)

```bash
grep -c "html-report" .agent/skills/research-and-summarize/SKILL.md
```

Expected: at least 1

- [ ] **Step 4: Commit**

```bash
git add .agent/skills/research-and-summarize/SKILL.md .claude/commands/research-and-summarize.md
git commit -m "feat: rewrite orchestration with parallel researchers and no mid-flow questions"
```

---

### Task 9: Create Research Dashboard Skill

**Files:**
- Create: `.claude/commands/research-dashboard.md`
- Create: `.agent/skills/research-dashboard/SKILL.md`

Standalone skill that aggregates HTML reports into a dashboard index page.

- [ ] **Step 1: Write `.claude/commands/research-dashboard.md`**

Slash command frontmatter:
- `description: Generate a dashboard index page from all research HTML reports`

The command prompt must instruct:
1. Glob `./research/**/*.html` (excluding index.html)
2. Read each file's `<meta>` tags for topic, date, completeness-score, sources-count
3. Extract the `<!-- SECTION:summary -->` content for excerpt
4. Generate `./research/index.html` with:
   - Clean, self-contained styling
   - Table/card layout with all topics
   - Per-topic: title (linked to HTML report), date, completeness score, source count, summary excerpt
   - Sorted by date descending

- [ ] **Step 2: Write `.agent/skills/research-dashboard/SKILL.md`**

Cross-platform skill version with same behavior. Frontmatter:
- `name: research-dashboard`
- `description: Generate a dashboard index page from all research HTML reports`

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/research-dashboard.md .agent/skills/research-dashboard/SKILL.md
git commit -m "feat: add research-dashboard skill for aggregating HTML reports"
```

---

### Task 10: Update Workflow JSON

**Files:**
- Modify: `.vscode/workflows/research-and-summarize.json`

Update the CC Workflow Studio JSON to reflect the new pipeline. Note: the static workflow cannot express dynamic parallel fan-out (N researchers), so it shows a single researcher node. The actual parallelism is handled at runtime by the SKILL.md.

- [ ] **Step 1: Rewrite the workflow JSON**

Changes:
1. **Remove nodes:** `analyzer-1`, `ask-verify-1`, `ask-format-1`, `bullets-1`
2. **Add node:** `html-report-1` (type: subAgent, with full prompt from agent definition)
3. **Update node:** `intake-1` — model: opus, updated prompt
4. **Update node:** `researcher-1` — updated prompt with triangulation strategy
5. **Update node:** `verifier-1` — merged analyzer+verifier prompt
6. **Update node:** `keypoints-1` — model: sonnet
7. **Update connections:**
   - start → intake-1 → researcher-1 → verifier-1 → [brief-1, detailed-1, html-report-1, keypoints-1] → end
8. **Reposition nodes** for clean left-to-right layout
9. **Update** `updatedAt` timestamp

- [ ] **Step 2: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('.vscode/workflows/research-and-summarize.json')); print('valid')"
```

Expected: `valid`

- [ ] **Step 3: Verify no references to removed nodes**

```bash
grep -c "analyzer\|ask-verify\|ask-format\|bullets" .vscode/workflows/research-and-summarize.json
```

Expected: 0

- [ ] **Step 4: Commit**

```bash
git add .vscode/workflows/research-and-summarize.json
git commit -m "feat: update workflow JSON for v2 pipeline"
```

---

### Task 11: Sync Cross-Platform Exports

**Files:**
- Modify: `.gemini/skills/research-and-summarize/SKILL.md`
- Modify: `.github/prompts/research-and-summarize.prompt.md`

These files must reflect the same pipeline as the primary skill definition but adapted for their respective platforms.

- [ ] **Step 1: Update Gemini skill**

Rewrite `.gemini/skills/research-and-summarize/SKILL.md` to match the new `.agent/skills/research-and-summarize/SKILL.md` but with Gemini-specific adaptations:
- Use `ask_user` instead of `AskUserQuestion`
- Use `#runSubagent` instead of Agent tool
- Same Mermaid diagram, same agent prompts, same execution flow

- [ ] **Step 2: Update GitHub Copilot prompt**

Rewrite `.github/prompts/research-and-summarize.prompt.md` to match new flow. Adapt tool references for Copilot's prompt format.

- [ ] **Step 3: Create dashboard entries for other platforms**

Create Gemini and GitHub versions of the dashboard skill if those directories follow the same pattern.

- [ ] **Step 4: Commit**

```bash
git add .gemini/ .github/prompts/
git commit -m "feat: sync cross-platform exports with v2 pipeline"
```

---

### Task 12: Final Verification

- [ ] **Step 1: Verify all agent files exist and have correct models**

```bash
for f in intake-1 researcher-1 verifier-1 detailed-1 html-report-1 keypoints-1 brief-1; do
  echo "$f: $(grep 'model:' .claude/agents/$f.md)"
done
```

Expected:
```
intake-1: model: opus
researcher-1: model: sonnet
verifier-1: model: opus
detailed-1: model: sonnet
html-report-1: model: opus
keypoints-1: model: sonnet
brief-1: model: sonnet
```

- [ ] **Step 2: Verify deleted agents are gone**

```bash
ls .claude/agents/analyzer-1.md .claude/agents/bullets-1.md 2>&1
```

Expected: "No such file or directory" for both

- [ ] **Step 3: Verify template exists**

```bash
ls templates/report.html
```

Expected: file exists

- [ ] **Step 4: Verify workflow JSON references no removed nodes**

```bash
python3 -c "
import json
wf = json.load(open('.vscode/workflows/research-and-summarize.json'))
nodes = [n['id'] for n in wf['nodes']]
assert 'analyzer-1' not in nodes, 'analyzer still present'
assert 'bullets-1' not in nodes, 'bullets still present'
assert 'ask-verify-1' not in nodes, 'ask-verify still present'
assert 'ask-format-1' not in nodes, 'ask-format still present'
assert 'html-report-1' in nodes, 'html-report missing'
print('All checks passed')
"
```

- [ ] **Step 5: Verify SKILL.md has no analyzer references**

```bash
grep -c "analyzer" .agent/skills/research-and-summarize/SKILL.md .claude/commands/research-and-summarize.md
```

Expected: 0 for both files

- [ ] **Step 6: Final commit (if any uncommitted changes)**

```bash
git status
```
