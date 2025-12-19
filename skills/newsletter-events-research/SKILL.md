---
name: newsletter-events-research
description: Research events from Instagram and Facebook for local newsletter. Use when scraping event sources, downloading flyer images, or extracting event details.
---

<essential_principles>
## How This Skill Works

This skill gathers raw event data from configured sources. It does NOT write newsletter content - use `newsletter-events-write` for that.

### Data Sources

1. **Instagram** - Via ScrapeCreators API (requires API key)
2. **Facebook Pages** - Via facebook-event-scraper npm package (Node.js subprocess)
3. **Facebook Discover** - Via Chrome MCP (location-based discovery, requires Chrome login)

### Output

Research produces structured data saved to `tmp/`:
- `tmp/extraction/raw/<source>_<date>.json` - Raw scraped data
- `tmp/extraction/images/<handle>/` - Downloaded flyer images
- `tmp/extraction/events.json` - Normalized, deduplicated events

### Key Principle

**Images are critical.** Many venues post event details only in flyer images, not captions. Always analyze downloaded images with Claude's vision.
</essential_principles>

<intake>
What would you like to research?

1. **Instagram** - Scrape Instagram accounts for events
2. **Facebook Pages** - Scrape specific Facebook pages for events
3. **Facebook Discover** - Discover events by location (requires Chrome MCP + Facebook login)
4. **All sources** - Full research from all configured sources

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "instagram", "ig" | `workflows/research-instagram.md` |
| 2, "facebook pages", "fb pages" | `workflows/research-facebook.md` |
| 3, "facebook discover", "fb discover", "discover" | `workflows/research-facebook-discover.md` |
| 4, "all", "both", "full" | `workflows/research-all.md` |
</routing>

<reference_index>
All domain knowledge in `references/`:

**APIs:** scrapecreators-api.md, facebook-scraper-api.md
**Detection:** event-detection.md
**Setup:** facebook-location-setup.md (for location-based discovery)
</reference_index>

<workflows_index>
| Workflow | Purpose |
|----------|---------|
| research-instagram.md | Scrape Instagram, download images, extract events |
| research-facebook.md | Scrape Facebook pages for events |
| research-facebook-discover.md | Discover events by location via Chrome MCP |
| research-all.md | Run all research workflows |
</workflows_index>

<success_criteria>
Research is complete when:
- [ ] Raw data saved to `tmp/extraction/raw/`
- [ ] Flyer images downloaded to `tmp/extraction/images/`
- [ ] Events normalized to `tmp/extraction/events.json`
- [ ] Data ready for `newsletter-events-write` skill
</success_criteria>
