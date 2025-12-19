# Full Newsletter Run

Complete end-to-end newsletter generation: research all sources and write the newsletter.

## Instructions

1. **Research Phase**
   - Load configuration from `config/sources.yaml`
   - Scrape Instagram accounts for events
   - Scrape Facebook pages for events
   - Download event images
   - Deduplicate events across sources
   - Save to `tmp/extraction/events.json`

2. **Write Phase**
   - Load collected events
   - Filter to next 7 days
   - Generate newsletter markdown
   - Save to `output/newsletter_YYYY-MM-DD.md`

3. **Report**
   - Print comprehensive summary
   - List any events needing review
   - Show output file location

## Arguments

- `$ARGUMENTS` - Optional: Custom newsletter title

## Example

```
/full-run
/full-run Catskills Weekend Events
```
