# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.10.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.5...v0.10.0
[0.9.5]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.4...v0.9.5
[0.9.4]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.4.3...v0.9.0
[0.4.3]: https://github.com/aniketpanjwani/local_media_tools/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/aniketpanjwani/local_media_tools/releases/tag/v0.4.2
