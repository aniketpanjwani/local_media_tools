---
name: newsletter-events:research
description: Research and collect events from all configured sources (Instagram and Facebook)
---

# Research Events

Research and collect events from all configured sources (Instagram and Facebook).

## Configuration Location

Configuration is loaded from `~/.config/local-media-tools/sources.yaml`.
Scraped data is saved to `~/.config/local-media-tools/data/events.db`.

## Instructions

1. Load the configuration from `~/.config/local-media-tools/sources.yaml`
2. For each enabled source, run the appropriate research workflow:
   - Instagram: Use `newsletter-events-research` skill, follow `workflows/research-instagram.md`
   - Facebook: Use `newsletter-events-research` skill, follow `workflows/research-facebook.md`
3. Deduplicate events across sources
4. Save results to SQLite database at `~/.config/local-media-tools/data/events.db`
5. Report summary of findings

## Expected Output

- Raw data saved to `~/.config/local-media-tools/data/raw/`
- Event images saved to `~/.config/local-media-tools/data/images/`
- Events saved to SQLite database
- Summary printed showing:
  - Events found per source
  - Duplicates removed
  - Events flagged for review
