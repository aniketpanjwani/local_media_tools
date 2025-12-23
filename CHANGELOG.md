# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.17.6] - 2025-12-22

### Changed
- **Split web aggregator workflow into two phases** to prevent Claude from writing inline Python
  - `research-web-scrape.md` (Phase 1): Only scrapes, returns JSON
  - `research-web-extract.md` (Phase 2): Extracts events from JSON, saves with CLI only
  - `research-web-aggregator.md` now dispatches to these phases in sequence
  - Strong `<critical>` blocks enforce CLI usage in each phase

### Fixed
- Claude was ignoring CLI tools and writing custom Python scripts to save events

## [0.17.5] - 2025-12-22

### Added
- **`scrape_wait_for` discovery method**: For JavaScript-heavy sites like Eventbrite
  - Profiler now stores actual method that worked (map, scrape_wait_for, or crawl)
  - Research uses the stored method instead of always trying map first
  - Eventbrite and similar JS sites now work correctly

### Fixed
- Eventbrite returned 0 URLs because profiler stored "map" even when scrape+wait_for worked

## [0.17.4] - 2025-12-22

### Fixed
- **Use profile's event_url_regex during web scraping**: Research now uses the URL pattern learned during `/add-source`
  - Scraper was ignoring profile data and applying hardcoded patterns (`/events?/`, `/calendar/`)
  - Sites like Tourism Winnipeg (`/display,event/`) and Eventbrite (`/e/`) returned 0 URLs
  - Now profiling captures site-specific patterns and research uses them

## [0.17.3] - 2025-12-22

### Fixed
- **Remove EVENT_PATTERNS pre-filtering**: Profiler now discovers ALL URLs, not just "event-like" ones
  - Previous approach missed valid events (e.g., Tourism Winnipeg's `/display,event/` URLs)
  - Pre-filtering is fundamentally flawed - every site has different URL structures
  - Real filtering happens via per-source `event_url_regex` in sources.yaml at scrape time
  - Profiler now only excludes obvious noise (about, contact, static assets)

## [0.17.2] - 2025-12-22

### Fixed
- **Eventbrite URL pattern**: Added `/e/` pattern to match Eventbrite event URLs
  - Eventbrite uses `/e/event-name-123` not `/events/`, so URLs were being filtered out
  - Now correctly discovers 40+ event URLs on Eventbrite

## [0.17.1] - 2025-12-22

### Fixed
- **Firecrawl SDK API compatibility**: Updated to use new SDK method signatures
  - Changed `app.scrape_url(url, params={"waitFor": ...})` to `app.scrape(url, wait_for=...)`
  - Fixed snake_case parameter names (`wait_for` instead of `waitFor`)
  - This was causing JS-heavy site profiling to silently fail

## [0.17.0] - 2025-12-22

### Added
- **Post classification CLI command**: `scripts/cli_instagram.py classify`
  - `--post-id <id> --classification <event|not_event|ambiguous> --reason "..."` - Single post
  - `--batch-json '[{"post_id": "...", "classification": "...", "reason": "..."}]'` - Batch mode
- **SqliteStorage classification methods**:
  - `update_post_classification()` - Update single post
  - `update_post_classifications_batch()` - Batch update for efficiency
- **JavaScript rendering for web profiler**: `scripts/profile_source.py`
  - Now tries `scrape(waitFor=3000, formats=["links"])` for JS-heavy sites
  - Fallback chain: `map()` → `scrape+waitFor` → `crawl()`
  - Tested: Eventbrite Winnipeg now returns 60+ event URLs (was 0)
- **Firecrawl JS docs**: `references/firecrawl-api.md`
  - `waitFor` parameter for JavaScript rendering
  - `actions` for complex interactions (scroll, click)

### Fixed
- Web profiler now works on JavaScript-heavy sites (Eventbrite, SPAs)
- Documented schema constraint: `discovery_method` must be "map" or "crawl"
- Workflows now use CLI commands instead of pseudo-code that referenced non-existent methods

## [0.16.0] - 2025-12-21

### Added
- **CLI tool for events**: `scripts/cli_events.py`
  - `save --json '{...}'` - Save single event with validation
  - `save-batch --file events.json` - Save multiple events from JSON file
  - `query --days 7` - Query events by date range
  - `stats` - Show event database statistics
  - Time parsing for 12-hour ("7pm", "7:30 PM") and 24-hour ("19:00") formats
- **CLI tool for newsletter loading**: `scripts/cli_newsletter.py`
  - `load --days 7` - Load events and formatting preferences as JSON
  - Claude generates markdown creatively from structured data
- **Time extraction guide** in web aggregator workflow
  - Conversion table for common time patterns
  - Doors/Show time handling (use show time)

### Changed
- All scripts now use centralized path handling via `scripts/paths.py`
  - `cli_instagram.py`, `cli_web.py`, `profile_source.py`, `config_schema.py` updated
- Rewrote `newsletter-events-write/SKILL.md` to use CLI-first workflow
  - CLI loads data (narrow bridge), Claude generates markdown (open field)
- Updated `research-web-aggregator.md` to use `cli_events.py` for saving events

### Fixed
- Skills no longer require inline Python for fragile operations (paths, types, queries)
- Newsletter generation now has consistent data structure from CLI

## [0.15.2] - 2025-12-21

### Added
- **CLI tool for web aggregators**: `scripts/cli_web.py`
  - `discover --all` - Preview URLs without scraping
  - `scrape --source "Name"` - Scrape pages and return markdown JSON
  - `mark-scraped` - Mark URLs as processed after event extraction
  - `show-stats` - Show scraping statistics

### Changed
- Updated `commands/research.md` to include web aggregator scraping instructions
- Rewrote `workflows/research-web-aggregator.md` to use CLI instead of Python imports
- Web aggregator research now matches Instagram pattern (CLI tool + Claude extraction)

### Fixed
- Web aggregator research no longer falls back to Firecrawl MCP when running from user projects

## [0.15.1] - 2025-12-21

### Changed
- Standardized plugin path discovery using `installed_plugins.json` lookup
  - All commands and skills now use: `cat ~/.claude/plugins/installed_plugins.json | jq -r '.plugins["newsletter-events@local-media-tools"][0].installPath'`
  - Removed reliance on `$CLAUDE_PLUGIN_ROOT` env var (not reliably set in all contexts)
  - Matches pattern already used in `commands/research.md`

### Fixed
- Claude no longer needs to search for plugin scripts when running from user projects

## [0.15.0] - 2025-12-21

### Added
- **CLI profiler tool**: `scripts/profile_source.py` for web aggregator profiling
  - Self-contained: uses bundled `firecrawl-py` from plugin's virtual environment
  - No external MCP dependency required
  - Outputs JSON with discovery_method, event_urls, and suggested regex

### Changed
- Commands and skills now call CLI tool instead of importing Python modules
- Updated `firecrawl-py` API usage to match v1.x (`.map()`, `.scrape()`, `.crawl()`)
- Fixed `scrape_firecrawl.py` to handle new Firecrawl SDK response types

### Fixed
- Plugin now works when Claude runs in user projects (not just plugin directory)

## [0.14.2] - 2025-12-21

### Fixed
- **Root cause found**: `commands/add-source.md` was being loaded instead of skill file
- Updated command file with full profiling workflow (was missing entirely)
- Command now includes `<critical>` block requiring Firecrawl profiling for web sources

## [0.14.1] - 2025-12-21

### Fixed
- Added `<required_reading>` and `<stop>` directives to force Claude to read workflow files
- Claude was invoking skill but not following the skill instructions

## [0.14.0] - 2025-12-21

### Changed
- Split `/add-source` skill into dispatcher + workflows pattern
  - `SKILL.md` now routes to type-specific workflows
  - `workflows/add-instagram.md` for Instagram accounts (simple)
  - `workflows/add-web-aggregator.md` for web sources (with mandatory profiling)
- Profiling step marked as `<critical>` and cannot be skipped
- SKILL.md reduced from 317 lines to 113 lines

### Fixed
- Claude no longer skips profiling step when adding web sources
- Clearer separation of concerns between source types

## [0.13.0] - 2025-12-21

### Added
- Source profiling for web aggregators ("learn once, apply forever")
  - `/add-source` now probes sites to discover optimal scraping strategy
  - Auto-detects when `map` fails and `crawl` is needed
  - Learns URL patterns from discovered event pages
  - Stores profile in sources.yaml for future runs
- `WebAggregatorProfile` schema with discovery_method, crawl_depth, event_url_regex
- Crawl fallback when Firecrawl's map_url() finds too few URLs

### Changed
- `/research` now uses stored profiles instead of re-discovering each run
- Web aggregator workflow checks profile.discovery_method before choosing map vs crawl

### Fixed
- Sites like I Love NY and Catskills Visitor Center now work (map_url failed, crawl succeeds)

## [0.12.0] - 2025-12-21

### Added
- URL-level tracking for web aggregators (incremental scraping)
  - Only scrape NEW event URLs on subsequent runs
  - Track scraped URLs in `scraped_pages` table
  - Shows progress: "Found 55 URLs, 10 new"
- `/newsletter-events:update-event` command to refresh specific event pages
- Fuzzy title matching for better event deduplication
  - Strips common prefixes (live:, tonight:, presents:)
  - Normalizes punctuation and whitespace
- URL normalization to handle tracking params and trailing slashes
- `scripts/migrate_unique_keys.py` to recompute keys after upgrade

### Changed
- Database schema upgraded to 2.2.0 (auto-migrates)
- Web aggregator workflow saves events BEFORE marking URL as scraped (prevents data loss)
- Improved configuration documentation for web aggregator fields

### Migration
- Run `uv run python scripts/migrate_unique_keys.py --dry-run` to preview key changes
- Then `uv run python scripts/migrate_unique_keys.py` to apply
- Existing events will get updated unique_keys for better deduplication

## [0.11.0] - 2025-12-21

### Changed
- **Breaking:** Facebook events are now ad-hoc only - pass URLs directly to `/research`
- Removed Facebook page scraping and location-based discovery
- Removed `/newsletter-events:setup-location` command
- Removed Chrome MCP dependency for Facebook
- Simplified config schema (no `facebook:` section in sources.yaml)

### Removed
- `FacebookConfig`, `FacebookPage`, `FacebookLocation` config classes
- `scrape_page_events()` method from Facebook bridge
- Location discovery workflow and references
- `scripts/facebook_discover.py`

### Migration
- Existing `facebook:` config in sources.yaml is now ignored (won't break, just unused)
- To scrape Facebook events: `/research https://facebook.com/events/123456`

## [0.10.0] - 2025-12-20

### Added
- Source attribution links in newsletter output via `source_url` field
- "Available Fields for Formatting" documentation section
- Users can now add `Include [Source](source_url)` to formatting preferences

### Changed
- Updated `docs/configuration.md` with all available formatting fields
- Updated `config/sources.example.yaml` with source link examples

## [0.9.5] - 2025-12-20

### Added
- Dedicated `docs/` folder with comprehensive documentation
- Platform-specific guides for Instagram, Facebook, and web aggregators
- Troubleshooting guide organized by workflow stage
- Architecture and development documentation

### Changed
- Slimmed README.md from 242 to ~80 lines with links to docs/

### Fixed
- Document image download requirements for Instagram CDN

## [0.9.4] - 2025-12-19

### Fixed
- Add classification workflow to research command file

## [0.9.3] - 2025-12-19

### Fixed
- Use installed_plugins.json to get correct plugin path

## [0.9.2] - 2025-12-19

### Fixed
- Add plugin directory discovery for CLI commands

## [0.9.1] - 2025-12-19

### Fixed
- Add explicit CLI instructions to prevent tool improvisation

## [0.9.0] - 2025-12-19

### Added
- CLI tool for Instagram research (`scripts/scrape_instagram.py`)
- `/newsletter-events:list-sources` command to view configured sources
- `/newsletter-events:remove-source` command to remove sources
- `/newsletter-events:add-source` skill for interactive source configuration
- Post classification workflow (skip re-analyzing already-classified posts)
- Carousel image support in Instagram workflow

### Changed
- Improved Instagram workflow with better image handling

## [0.4.3] - 2025-12-18

### Fixed
- Handle multi-event posts (weekly schedules, event series)

## [0.4.2] - 2025-12-18

### Fixed
- Add explicit post classification step to Instagram workflow

[0.16.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.15.2...v0.16.0
[0.15.2]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.15.1...v0.15.2
[0.15.1]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.14.2...v0.15.0
[0.14.2]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.14.1...v0.14.2
[0.14.1]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.14.0...v0.14.1
[0.14.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.5...v0.10.0
[0.9.5]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.4...v0.9.5
[0.9.4]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.4.3...v0.9.0
[0.4.3]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/aniketpanjwani/local_media_tools/releases/tag/v0.4.2
