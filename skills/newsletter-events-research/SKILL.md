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

Research produces structured data saved to `~/.config/local-media-tools/data/`:
- `data/raw/instagram_<handle>.json` - Raw API responses
- `data/images/instagram/<handle>/` - Downloaded flyer images
- `data/events.db` - SQLite database with profiles, posts, events, venues

### Key Principle

**Images are critical.** Many venues post event details only in flyer images, not captions. Always analyze downloaded images with Claude's vision.
</essential_principles>

<critical>
## Use CLI Tools - Never curl

**NEVER use curl or raw API calls.** Always use the CLI tools provided:

**Instagram:**
```bash
# Scrape all configured accounts
uv run python scripts/cli_instagram.py scrape --all

# Scrape specific account
uv run python scripts/cli_instagram.py scrape --handle wayside_cider

# List posts from database
uv run python scripts/cli_instagram.py list-posts --handle wayside_cider

# Show database statistics
uv run python scripts/cli_instagram.py show-stats
```

The CLI tools ensure:
- Correct API parameters (`handle`, not `username`)
- Rate limiting (2 calls/second)
- Automatic retry on 429/5xx errors
- Proper database storage with FK relationships
- Raw responses saved to `~/.config/local-media-tools/data/raw/`

**Do NOT:**
- Use `curl` to call ScrapeCreators API directly
- Write raw SQL to insert data
- Guess API parameter names
</critical>

<intake>
What would you like to research?

1. **Instagram** - Scrape Instagram accounts for events
2. **Facebook Pages** - Scrape specific Facebook pages for events
3. **Facebook Discover** - Discover events by location (requires Chrome MCP + Facebook login)
4. **Web Aggregators** - Scrape web event aggregator sites
5. **All sources** - Full research from all configured sources

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "instagram", "ig" | `workflows/research-instagram.md` |
| 2, "facebook pages", "fb pages" | `workflows/research-facebook.md` |
| 3, "facebook discover", "fb discover", "discover" | `workflows/research-facebook-discover.md` |
| 4, "web", "aggregator", "websites" | `workflows/research-web-aggregator.md` |
| 5, "all", "both", "full" | `workflows/research-all.md` |
</routing>

<reference_index>
All domain knowledge in `references/`:

**APIs:** scrapecreators-api.md, facebook-scraper-api.md, firecrawl-api.md
**Detection:** event-detection.md
**Setup:** facebook-location-setup.md (for location-based discovery)
</reference_index>

<workflows_index>
| Workflow | Purpose |
|----------|---------|
| research-instagram.md | Scrape Instagram, download images, extract events |
| research-facebook.md | Scrape Facebook pages for events |
| research-facebook-discover.md | Discover events by location via Chrome MCP |
| research-web-aggregator.md | Scrape web event aggregator sites |
| research-all.md | Run all research workflows |
</workflows_index>

<success_criteria>
Research is complete when:
- [ ] CLI tool used to scrape accounts (not curl)
- [ ] Raw data saved to `~/.config/local-media-tools/data/raw/`
- [ ] Posts saved to database with profiles
- [ ] Posts classified as event/not_event/ambiguous
- [ ] Events extracted from classified posts
- [ ] Data ready for `newsletter-events-write` skill
</success_criteria>
