# Getting Started

Create your first hyper-local event newsletter in 10 minutes.

## Prerequisites

Before starting, you'll need:
- [ ] [Claude Code](https://claude.com/claude-code) installed
- [ ] At least one source to scrape (Instagram handle, Facebook page, or event site)

**API keys (at least one required):**
- [ ] [ScrapeCreators API key](https://scrapecreators.com) - Required for Instagram
- [ ] [Firecrawl API key](https://firecrawl.dev) - Required for web aggregators
- [ ] No API key needed for Facebook event URLs

## Step 1: Install the Plugin

```
/plugin marketplace add aniketpanjwani/local_media_tools
/plugin install newsletter-events
```

**Verify:** You should see "Plugin installed successfully"

## Step 2: Run Setup

```
/newsletter-events:setup
```

This command will:
1. Install runtime dependencies (uv, bun)
2. Install Python and Node packages
3. Create config directory at `~/.config/local-media-tools/`
4. Guide you through API key configuration

**Verify:** All checks should show green checkmarks

**If setup fails:** See [Troubleshooting: Setup Errors](troubleshooting.md#setup-errors)

## Step 3: Add Your First Source

```
/newsletter-events:add-source
```

Follow the prompts to add an Instagram account or web aggregator.

**Tip:** Start with one source to test the workflow before adding more.

**Note:** For Facebook events, pass URLs directly to `/research` instead of adding them here.

**Verify:** Source appears when you run `/newsletter-events:list-sources`

## Step 4: Research Events

```
/newsletter-events:research
```

This scrapes events from your configured sources. Takes 1-5 minutes depending on source count.

**Verify:** You see "Research complete. Found X events."

**If no events found:** Check that your source has upcoming events and your API key is valid.

## Step 5: Generate Newsletter

```
/newsletter-events:write
```

Claude generates a markdown newsletter based on your scraped events and formatting preferences.

**Verify:** Newsletter file created in current directory as `newsletter_YYYY-MM-DD.md`

## Next Steps

- [Add more sources](configuration.md#adding-sources) to expand coverage
- [Customize formatting](configuration.md#formatting-preferences) to match your style
- [Add Facebook events](examples/facebook.md) by passing URLs to `/research`

## Quick Reference

| Command | Description |
|---------|-------------|
| `/newsletter-events:setup` | Set up environment and dependencies |
| `/newsletter-events:add-source` | Add Instagram, Facebook, or web sources |
| `/newsletter-events:list-sources` | View all configured sources |
| `/newsletter-events:remove-source` | Remove a source |
| `/newsletter-events:research` | Scrape all configured sources |
| `/newsletter-events:write` | Generate newsletter from scraped events |

---

[Back to Documentation](README.md)
