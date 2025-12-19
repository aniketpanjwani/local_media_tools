---
name: newsletter-events:research
description: Research and collect events from all configured sources (Instagram and Facebook)
---

# Research Events

Research and collect events from all configured sources (Instagram and Facebook).

## Instructions

1. Load the configuration from `config/sources.yaml`
2. For each enabled source, run the appropriate research workflow:
   - Instagram: Use `newsletter-events-research` skill, follow `workflows/research-instagram.md`
   - Facebook: Use `newsletter-events-research` skill, follow `workflows/research-facebook.md`
3. Deduplicate events across sources
4. Save results to `tmp/extraction/events.json`
5. Report summary of findings

## Expected Output

- Raw data saved to `tmp/extraction/raw/`
- Event images saved to `tmp/extraction/images/`
- Combined events saved to `tmp/extraction/events.json`
- Summary printed showing:
  - Events found per source
  - Duplicates removed
  - Events flagged for review
