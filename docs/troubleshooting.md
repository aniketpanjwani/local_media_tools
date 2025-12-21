# Troubleshooting Guide

## Quick Index

| Error | Section |
|-------|---------|
| `node: command not found` | [Missing Node.js](#missing-nodejs) |
| `uv: command not found` | [Missing uv](#missing-uv) |
| `API key invalid` | [Invalid API Keys](#invalid-api-keys) |
| `No events found` | [No Events Found](#no-events-found) |
| Facebook scraper fails | [Facebook Issues](#facebook-issues) |
| Instagram returns empty | [Instagram Issues](#instagram-issues) |

---

## Setup Errors

### Missing Node.js

**Error:** `node: command not found` or `bun: command not found`

**Solution:**
1. Install Node.js: [nodejs.org](https://nodejs.org/) or via package manager
2. Install bun: `curl -fsSL https://bun.sh/install | bash`
3. Restart your terminal
4. Run `/newsletter-events:setup` again

### Missing uv

**Error:** `uv: command not found`

**Solution:**
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Restart your terminal
3. Run `/newsletter-events:setup` again

### Setup Script Fails

**Error:** `./scripts/setup.sh` exits with error

**Solution:**
1. Check Python version: `python3 --version` (needs 3.12+)
2. Check permissions: `chmod +x scripts/setup.sh`
3. Run manually: `uv sync && bun install`

---

## Research Errors

### Invalid API Keys

**Error:** `401 Unauthorized` or `Invalid API key`

**Solution:**
1. Check `.env` file exists: `cat ~/.config/local-media-tools/.env`
2. Verify key format (no quotes needed):
   ```bash
   SCRAPECREATORS_API_KEY=sk_live_xxxxx
   FIRECRAWL_API_KEY=fc-xxxxx
   ```
3. Verify key is active at the provider's dashboard

### No Events Found

**Symptom:** Research completes but "Found 0 events"

**Possible causes:**
1. **Source has no upcoming events** - Check the source manually
2. **Wrong Instagram handle** - Verify handle exists and is public
3. **Facebook page structure changed** - Facebook scraping can be unreliable
4. **Date filter too restrictive** - Check `filters.date_range` in sources.yaml

**Debug steps:**
1. Run research with verbose output (Claude will show progress)
2. Check raw responses in `~/.config/local-media-tools/data/raw/`
3. Try a known-working source first

### Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:**
1. Wait 5-10 minutes before retrying
2. Reduce number of sources per research run
3. Check API plan limits at provider dashboard

---

## Instagram Issues

### Empty Results

**Symptom:** Instagram source returns no posts

**Possible causes:**
1. **Private account** - Only public accounts can be scraped
2. **Handle changed** - Verify current handle at instagram.com
3. **API key exhausted** - Check ScrapeCreators dashboard

### Image Download Fails

**Symptom:** Events found but images missing

**Cause:** Instagram CDN blocks external requests for images.

**Solution:** Images are downloaded locally to `~/.config/local-media-tools/data/images/`. If download fails, the event is still stored but without image data.

### Common Mistakes

| Mistake | Correct Format |
|---------|----------------|
| `@venue_name` | `venue_name` (no @) |
| `https://instagram.com/venue` | `venue` (handle only) |
| `venue-name` | Check for dashes vs underscores |

---

## Facebook Issues

### Page Scraper Fails

**Symptom:** Facebook page returns error or no events

**Possible causes:**
1. **Not a public page** - Page must be public with /events section
2. **HTML structure changed** - Facebook updates break scrapers periodically
3. **Rate limiting** - Too many requests from same IP

**Solution:**
1. Verify page has events: visit URL manually
2. Try location-based discovery instead
3. Wait and retry later

### Location Discovery Fails

**Symptom:** `/newsletter-events:setup-location` doesn't work

**Prerequisites:**
- Chrome browser installed
- Chrome MCP Server running
- Logged into Facebook in Chrome

**Debug steps:**
1. Verify Chrome MCP is configured in Claude Code settings
2. Log into Facebook in Chrome manually
3. Navigate to facebook.com/events to verify access
4. Retry setup-location

### Events Have Sparse Data

**Symptom:** Facebook events missing details (venue, time, description)

**Cause:** Location-based discovery captures limited data from the events listing page.

**Solution:** Events are marked for review. Use `/newsletter-events:write` and Claude will handle incomplete data gracefully.

---

## Web Aggregator Issues

### Firecrawl Fails

**Symptom:** Web aggregator returns error

**Possible causes:**
1. **Invalid API key** - Check FIRECRAWL_API_KEY in .env
2. **Site blocks scraping** - Some sites have bot protection
3. **Complex JavaScript** - SPAs may not scrape well

**Solution:**
1. Test URL at firecrawl.dev playground first
2. Try simpler event listing sites
3. Use `extraction_hints` in sources.yaml to guide extraction

### No Events Extracted

**Symptom:** Scrape succeeds but 0 events parsed

**Cause:** Event extraction relies on Claude interpreting page content.

**Solution:**
1. Add `extraction_hints` to help identify event structure:
   ```yaml
   - url: "https://example.com/events"
     extraction_hints: "Events in table rows with date, title, venue columns"
   ```
2. Check raw response in `data/raw/` to see what was scraped

---

## Database Issues

### Corrupted Database

**Symptom:** SQLite errors or missing data

**Solution:**
1. Check for backup: `~/.config/local-media-tools/data/events.db.backup`
2. If no backup, delete database and re-run research:
   ```bash
   rm ~/.config/local-media-tools/data/events.db
   ```

### Migration Errors

**Symptom:** Error on first run after plugin update

**Solution:**
1. Backup your database first
2. Run setup again: `/newsletter-events:setup`
3. If migration fails, you may need to delete and recreate the database

---

## Still Stuck?

1. **Check raw data:** Look in `~/.config/local-media-tools/data/raw/` for API responses
2. **Enable verbose mode:** Ask Claude to show detailed progress
3. **File an issue:** [GitHub Issues](https://github.com/aniketpanjwani/local_media_tools/issues)
4. **Get help:** [aniket@contentquant.io](mailto:aniket@contentquant.io)

---

[Back to Documentation](README.md)
