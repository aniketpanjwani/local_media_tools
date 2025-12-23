# Workflow: Scrape Web Aggregators

<purpose>
Scrape configured web aggregators and return JSON with markdown content.
This workflow ONLY scrapes - it does NOT extract events.
</purpose>

<critical>
DO NOT extract events in this workflow.
DO NOT save events to database.
ONLY run the scrape commands and return the JSON output.
</critical>

<process>

## Step 1: Get Plugin Directory

```bash
cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'
```

Save as `PLUGIN_DIR`.

## Step 2: Preview (Optional)

See what URLs will be scraped:

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py discover --all
```

## Step 3: Scrape Pages

```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py scrape --all --limit 50
```

Or for a specific source:
```bash
cd "$PLUGIN_DIR" && uv run python scripts/cli_web.py scrape --source "Source Name"
```

**Output:** JSON array printed to stdout with:
- `source_name`: Web aggregator name
- `original_url`: Page URL
- `normalized_url`: Canonical URL for tracking
- `title`: Page title
- `markdown`: Full page content
- `scraped_at`: Timestamp

## Step 4: Return JSON

The JSON output from Step 3 is the output of this workflow.
Pass it to `research-web-extract.md` for event extraction.

</process>

<output>
JSON array of scraped pages. Example:
```json
[
  {
    "source_name": "Tourism Winnipeg",
    "original_url": "https://example.com/events/jazz-night",
    "title": "Jazz Night",
    "markdown": "# Jazz Night\n\nJoin us Saturday at 8pm...",
    "scraped_at": "2025-01-20T10:30:00"
  }
]
```
</output>

<success_criteria>
- [ ] CLI scrape command executed
- [ ] JSON output captured
- [ ] Ready for extraction workflow
</success_criteria>
