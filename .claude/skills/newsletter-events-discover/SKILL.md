---
name: newsletter-events-discover
description: Discover Instagram and Facebook event sources for a new city or region. Use when setting up a newsletter for a new location, finding local venues, or expanding source coverage.
---

<essential_principles>
## How This Skill Works

This skill helps you find Instagram accounts and Facebook pages that post local events for any city or region. It uses Google search to discover sources, then validates them.

### What It Does

1. **Searches** for local venues, promoters, and event aggregators
2. **Extracts** Instagram handles and Facebook page URLs from results
3. **Validates** that Instagram accounts exist and are public
4. **Outputs** ready-to-use YAML config for `sources.yaml`

### Requirements

- ScrapeCreators API key (same one used for Instagram scraping)
- City/region name to search for

### Output

Discovery produces a YAML snippet you can add to `config/sources.yaml`.
</essential_principles>

<intake>
What city or region do you want to find event sources for?

Please provide:
1. **City name** (e.g., "Winnipeg", "Austin", "Portland")
2. **Region/Country** (e.g., "Manitoba, Canada", "Texas, USA")
3. **Event types** (optional) - music, arts, festivals, markets, etc.

Example: "Find event sources for Winnipeg, Manitoba, Canada focusing on music venues and festivals"

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| City provided | `workflows/discover-sources.md` |
</routing>

<reference_index>
All domain knowledge in `references/`:

**Search Patterns:** search-patterns.md - Effective queries for finding local sources
</reference_index>

<workflows_index>
| Workflow | Purpose |
|----------|---------|
| discover-sources.md | Search, extract, validate, and output source config |
</workflows_index>

<success_criteria>
Discovery is complete when:
- [ ] Google searches executed for the city
- [ ] Instagram handles extracted from results
- [ ] Facebook event pages identified
- [ ] Handles validated via ScrapeCreators profile check
- [ ] YAML config snippet generated for `sources.yaml`
</success_criteria>
