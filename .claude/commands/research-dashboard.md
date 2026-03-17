---
description: Generate a dashboard index page from all research HTML reports
---

You are a research dashboard generator. Your job is to create a static HTML index page that aggregates all research HTML reports in the project.

## Process

1. **Find all HTML reports**: Glob for `./research/**/*.html`, excluding any `index.html` files.

2. **Read metadata from each report**: Open each HTML file and extract:
   - `<meta name="topic">` → topic name
   - `<meta name="date">` → research date
   - `<meta name="completeness-score">` → quality score (1-10)
   - `<meta name="sources-count">` → number of sources
   - Content between `<!-- SECTION:summary -->` and `<!-- /SECTION:summary -->` → summary excerpt
   - The `<title>` tag → report title

3. **Generate `./research/index.html`** with:
   - Clean, self-contained CSS (no external dependencies)
   - A header with "Research Dashboard" title and generation date
   - A card or table layout with one entry per research topic
   - Per topic: title (linked to the HTML report), date, completeness score (color-coded), source count, and a brief summary excerpt
   - Sorted by date descending (newest first)
   - Responsive design (works on desktop and mobile)

4. **Handle edge cases**:
   - If no HTML reports found, generate the page with a "No research reports found" message
   - If a report has missing meta tags, show "N/A" for those fields
   - If multiple versions exist for the same topic, show only the latest version

5. **Confirm** the file path to the user.
