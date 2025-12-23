# Workflow: Research Web Aggregators

<purpose>
Scrape web aggregator sites and extract events.
This is a two-phase workflow to keep responsibilities clear.
</purpose>

<phases>

## Phase 1: Scrape

Read and execute: `workflows/research-web-scrape.md`

This phase:
- Runs CLI to scrape configured web sources
- Returns JSON array of pages with markdown content

**Capture the JSON output before proceeding.**

## Phase 2: Extract

Read and execute: `workflows/research-web-extract.md`

Pass the JSON from Phase 1 to this workflow.

This phase:
- Extracts events from each page's markdown
- Saves events using `cli_events.py` CLI
- Marks URLs as scraped

</phases>

<critical>
COMPLETE PHASE 1 BEFORE STARTING PHASE 2.

Phase 1 produces JSON. Phase 2 consumes it.
Do not skip ahead or combine phases.
</critical>

<success_criteria>
- [ ] Phase 1: Scrape completed, JSON captured
- [ ] Phase 2: Events extracted and saved via CLI
- [ ] All URLs marked as scraped
- [ ] Statistics displayed
</success_criteria>
