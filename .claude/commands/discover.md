# Discover Event Sources

Discover Instagram and Facebook event sources for a new city or region.

## Arguments

- `$ARGUMENTS` - City and region to search for (e.g., "Winnipeg, Manitoba, Canada")

## Instructions

1. Parse the city and region from the arguments
2. Use the `newsletter-events-discover` skill
3. Follow the `workflows/discover-sources.md` workflow
4. Run Google searches via ScrapeCreators API:
   - `{city} music venues live concerts Instagram`
   - `{city} events calendar Instagram`
   - `{city} festivals 2025`
   - `{city} events site:facebook.com`
5. Extract Instagram handles and Facebook pages from results
6. Validate Instagram handles exist (check profiles)
7. Generate YAML config snippet for `sources.yaml`

## Expected Output

- List of discovered Instagram accounts with:
  - Handle
  - Name
  - Follower count
  - Inferred type (venue, aggregator, etc.)
- List of Facebook event pages
- Ready-to-use YAML config snippet
- API credit usage summary

## Example Usage

```
/discover Winnipeg, Manitoba, Canada
/discover Austin, Texas, USA
/discover Portland, Oregon focusing on music venues
```

## Next Steps

After discovery:
1. Review the generated YAML config
2. Edit `config/sources.yaml` to add the sources
3. Run `/research` to test scraping
4. Run `/write` to generate newsletter
