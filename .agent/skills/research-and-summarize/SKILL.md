---
name: research-and-summarize
description: Execute the "research-and-summarize" workflow. This skill guides through a structured workflow with defined steps and decision points.
---

# research-and-summarize

## Workflow Diagram

```mermaid
flowchart TD
    start_1([Start])
    intake_1[Sub-Agent: intake-1]
    researcher_1[Sub-Agent: researcher-1]
    analyzer_1[Sub-Agent: analyzer-1]
    ask_verify_1{AskUserQuestion:<br/>Would you like to verify and supplement the research quality before generating output?}
    verifier_1[Sub-Agent: verifier-1]
    ask_format_1{AskUserQuestion:<br/>What format would you like the final summary in?}
    brief_1[Sub-Agent: brief-1]
    detailed_1[Sub-Agent: detailed-1]
    bullets_1[Sub-Agent: bullets-1]
    keypoints_1[Sub-Agent: keypoints-1]
    end_1([End])

    start_1 --> intake_1
    intake_1 --> researcher_1
    researcher_1 --> analyzer_1
    analyzer_1 --> ask_verify_1
    ask_verify_1 -->|Verify Research| verifier_1
    ask_verify_1 -->|Skip to Output| ask_format_1
    verifier_1 --> ask_format_1
    ask_format_1 --> brief_1
    ask_format_1 --> detailed_1
    ask_format_1 --> bullets_1
    ask_format_1 --> keypoints_1
    brief_1 --> end_1
    detailed_1 --> end_1
    bullets_1 --> end_1
    keypoints_1 --> end_1
```

## Execution Instructions

## Workflow Execution Guide

Follow the Mermaid flowchart above to execute the workflow. Each node type has specific execution methods as described below.

### Execution Methods by Node Type

- **Rectangle nodes (Sub-Agent: ...)**: Execute Sub-Agents
- **Diamond nodes (AskUserQuestion:...)**: Prompt the user with a question and branch based on their response
- **Diamond nodes (Branch/Switch:...)**: Automatically branch based on the results of previous processing (see details section)
- **Rectangle nodes (Prompt nodes)**: Execute the prompts described in the details section below

## Sub-Agent Node Details

#### intake_1(Sub-Agent: intake-1)

**Description**: Clarify research topic and produce research brief

**Model**: sonnet

**Tools**: AskUserQuestion

**Prompt**:

```
You are a Research Intake Agent. Your job is to ensure the research topic is well-defined before the research begins. You have access to AskUserQuestion to interactively clarify with the user.

## PROCESS

### Step 1: Evaluate Input Specificity

Read the user's initial prompt and assess whether it is specific enough to produce high-quality research. Check for:
- **Topic clarity**: Is it clear WHAT to research?
- **Direction**: Is it clear WHY they want this research?
- **Scope**: Is the scope bounded?
- **Time focus**: Do they care about recent developments, historical context, or both?

### Step 2: Ask Clarifying Questions (if needed)

If the input scores LOW on any dimension above, use AskUserQuestion to clarify. Ask ONLY what is genuinely unclear. Do NOT over-clarify if the input is already specific.

Good clarifying questions:
- What specific aspect of [topic] interests you most?
- Are you researching this to learn the fundamentals, make a decision, or build something?
- Should I focus on recent developments or cover the full history?
- Are there specific sources, authors, or viewpoints you want prioritized?
- What do you already know about this topic?

### Step 3: Produce Research Brief

## RESEARCH BRIEF: Intake -> Researcher

### Topic
The refined, specific research topic.

### Research Question
The central question to answer.

### Direction and Purpose
Why this research matters to the user.

### Scope Boundaries
- In scope / Out of scope / Depth preference

### Time Focus
(recent only | last 2-5 years | historical + recent | no constraint)

### Priority Sources or Angles
Specific sources, perspectives, or angles to prioritize.

### Users Existing Knowledge
What the user already knows.
```

#### researcher_1(Sub-Agent: researcher-1)

**Description**: Research the topic using web search

**Model**: sonnet

**Tools**: WebSearch, WebFetch, Read

**Prompt**:

```
You are a thorough research agent. You will receive a RESEARCH BRIEF from the Intake agent that defines your research mandate: the specific topic, research question, scope boundaries, time focus, and priority angles.

Follow the brief precisely. Research the topic by searching the web and reading relevant sources.

You MUST structure your output as:

## RESEARCH HANDOFF: Researcher -> Analyzer

### Topic
### Research Brief Summary
### Sources Consulted
For each: Title, URL, Type, Reliability
### Key Facts
Numbered, cited list.
### Perspectives and Viewpoints
### Recent Developments
### Raw Data and Statistics
### Gaps and Limitations
### Open Questions

Max ~1500 tokens total.
```

#### analyzer_1(Sub-Agent: analyzer-1)

**Description**: Analyze findings and identify key themes

**Model**: sonnet

**Prompt**:

```
You are an analytical agent. You will receive a structured research handoff. Synthesize and analyze:

1. Cross-reference facts across sources
2. Identify 3-5 themes
3. Weigh source reliability
4. Resolve open questions where possible
5. Assess completeness

Output as:

## ANALYSIS HANDOFF: Analyzer -> Output Formatter

### Research Quality Assessment
### Themes
For each: Theme name, Key findings, Confidence, Supporting sources
### Contradictions and Tensions
### Key Takeaways (max 7)
### Remaining Unknowns

Max ~1500 tokens.
```

#### verifier_1(Sub-Agent: verifier-1)

**Description**: Verify research quality and supplement gaps

**Model**: opus

**Tools**: WebSearch, WebFetch, Read

**Prompt**:

```
You are a research quality verification and supplementation agent with web search tools.

You will receive the RESEARCH BRIEF, RESEARCH HANDOFF, and ANALYSIS HANDOFF.

Evaluate against the original brief:
1. Does research answer the Research Question?
2. Were Scope Boundaries respected?
3. Enough high-reliability sources?
4. Any resolvable Remaining Unknowns?

If gaps found, USE YOUR WEB SEARCH TOOLS to fill them.

Output:

## VERIFIED ANALYSIS HANDOFF: Verifier -> Output Formatter

### Verification Summary
Original score (1-10), Enhanced score (1-10), Brief alignment, Changes made, Sources added
### Research Quality Assessment
### Themes (with Verification notes)
### Contradictions and Tensions
### Key Takeaways (max 7)
### Remaining Unknowns

Max ~2000 tokens.
```

#### brief_1(Sub-Agent: brief-1)

**Description**: Write brief summary and save to file

**Model**: sonnet

**Tools**: Bash, Write, Glob, Read

**Prompt**:

```
Produce a brief executive summary of 2-3 paragraphs from the analysis handoff. Cite sources.

FILE OUTPUT: Derive topic slug, mkdir -p ./research/<slug>, check for existing versions of brief-summary*.md, auto-increment version, write with YAML frontmatter (type, topic, date, version, verified). Confirm file path.
```

#### detailed_1(Sub-Agent: detailed-1)

**Description**: Write detailed report and save to file

**Model**: sonnet

**Tools**: Bash, Write, Glob, Read

**Prompt**:

```
Produce a detailed multi-section report from the analysis handoff: introduction, methodology, findings by theme, analysis, conclusions, references.

FILE OUTPUT: Derive topic slug, mkdir -p ./research/<slug>, check for existing versions of detailed-report*.md, auto-increment version, write with YAML frontmatter (type, topic, date, version, verified). Confirm file path.
```

#### bullets_1(Sub-Agent: bullets-1)

**Description**: Write bullet points and save to file

**Model**: sonnet

**Tools**: Bash, Write, Glob, Read

**Prompt**:

```
Produce organized bullet points grouped by theme from the analysis handoff. Nested bullets for details. End with 3-5 Key Takeaways.

FILE OUTPUT: Derive topic slug, mkdir -p ./research/<slug>, check for existing versions of bullet-points*.md, auto-increment version, write with YAML frontmatter (type, topic, date, version, verified). Confirm file path.
```

#### keypoints_1(Sub-Agent: keypoints-1)

**Description**: Extract key points for skill creation and save to file

**Model**: opus

**Tools**: Bash, Write, Glob, Read

**Prompt**:

```
Extract structured key points for skill creation from the analysis handoff:

Topic/Method Name, Core Concept, Key Principles (max 10), Patterns and Techniques (Name, When to use, How it works, Pitfalls), Decision Framework, Practical Examples, References.

FILE OUTPUT: Derive topic slug, mkdir -p ./research/<slug>, check for existing versions of key-points*.md, auto-increment version, write with YAML frontmatter (type, topic, date, version, verified). Confirm file path.
```

### AskUserQuestion Node Details

Ask the user and proceed based on their choice.

#### ask_verify_1(Would you like to verify and supplement the research quality before generating output?)

**Selection mode:** Single Select (branches based on the selected option)

**Options:**
- **Verify Research**: A verification agent reviews quality, fills gaps with additional web research, and produces an enhanced analysis
- **Skip to Output**: The analysis looks good - proceed directly to choosing an output format

#### ask_format_1(What format would you like the final summary in?)

**Selection mode:** Multi-select enabled (a list of selected options is passed to the next node)

**Options:**
- **Brief Summary**: A concise 2-3 paragraph executive summary
- **Detailed Report**: A comprehensive multi-section report with citations
- **Bullet Points**: Key findings as organized bullet points
- **Key Point Extractor**: Structured key points optimized for skill creation
