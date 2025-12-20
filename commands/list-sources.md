---
name: newsletter-events:list-sources
description: List all configured event sources (Instagram, Facebook, web aggregators)
---

# List Event Sources

View all configured event sources in your `sources.yaml` configuration.

## Configuration Location

Sources are stored in `~/.config/local-media-tools/sources.yaml`.

## Usage Examples

```bash
# List all sources
/newsletter-events:list-sources

# List only Instagram accounts
/newsletter-events:list-sources instagram

# List only Facebook sources
/newsletter-events:list-sources facebook

# List only web aggregators
/newsletter-events:list-sources web
```

## Filter Keywords

| Filter | Aliases | Shows |
|--------|---------|-------|
| `all` (default) | blank | All configured sources |
| `instagram` | `ig` | Instagram accounts only |
| `facebook` | `fb` | Facebook pages, groups, locations |
| `web` | - | Web aggregator sites only |

## Output Format

Sources are grouped by type with relevant metadata:

```
INSTAGRAM ACCOUNTS (3 configured)
| Handle       | Name          | Type        | Location     |
|--------------|---------------|-------------|--------------|
| @localvenue  | Local Venue   | music_venue | Kingston, NY |
| @themusicbar | The Music Bar | bar         | -            |
| @artgallery  | Art Gallery   | gallery     | Hudson, NY   |

FACEBOOK PAGES (2 configured)
| URL                              | Name           |
|----------------------------------|----------------|
| facebook.com/thevenue/events     | The Venue      |
| facebook.com/kingstonmusic/events| Kingston Music |

WEB AGGREGATORS (1 configured)
| URL                      | Name        | Type    | Max Pages |
|--------------------------|-------------|---------|-----------|
| https://hvmag.com/events | HV Magazine | listing | 50        |

Total: 6 sources configured
```

## Empty State

If no sources are configured:

```
No sources configured.

To add sources: /newsletter-events:add-source @handle
```

If a filter matches nothing:

```
No instagram sources found.

You have:
- 3 Facebook pages
- 1 web aggregator

To add Instagram accounts: /newsletter-events:add-source @handle
```

## Related Commands

| Command | Description |
|---------|-------------|
| `/newsletter-events:add-source` | Add new sources |
| `/newsletter-events:remove-source` | Remove existing sources |
| `/newsletter-events:research` | Scrape configured sources |
