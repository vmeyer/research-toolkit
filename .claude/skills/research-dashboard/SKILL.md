---
name: research-dashboard
description: Generate a dashboard index page from all research HTML reports. Use when the user wants to see an overview of all their research, create a research index, or build a dashboard from existing HTML reports in the ./research/ directory.
---

# research-dashboard

You are a research dashboard generator. Create a static HTML index page aggregating all research HTML reports.

## Process

1. **Find reports**: Glob `./research/**/*.html` (exclude `index.html`)

2. **Extract metadata** from each report:
   - `<meta name="topic">` → topic
   - `<meta name="date">` → date
   - `<meta name="completeness-score">` → score
   - `<meta name="sources-count">` → source count
   - `<!-- SECTION:summary -->` content → excerpt
   - `<title>` → title

3. **Generate `./research/index.html`**:
   - Self-contained HTML + CSS
   - Header: "Research Dashboard" + generation date
   - Card/table layout, one entry per topic
   - Per entry: title (linked), date, score (color-coded), sources, summary
   - Sorted by date descending
   - Responsive design
   - If multiple versions exist, show latest only
   - If no reports found, show "No research reports found"

4. Confirm file path.
