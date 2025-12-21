# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
