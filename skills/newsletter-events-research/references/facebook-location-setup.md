# Setting Up Facebook location_id

Facebook Events uses an internal `location_id` to filter events by geographic area.
This ID must be configured manually (one-time setup per city).

## Why Manual Setup?

1. **No Public API**: Facebook does not provide a way to look up location IDs programmatically
2. **Disambiguation**: Many city names exist in multiple places (e.g., "Medellín" in Colombia vs Philippines)
3. **Reliable**: Once configured, location_ids are stable and rarely change

## Step-by-Step Instructions

### 1. Open Facebook Events in Chrome

Navigate to: https://www.facebook.com/events/

**Important**: Use the same Chrome browser that Claude Code's Chrome MCP will use.

### 2. Open the Location Filter

Click on the location/city filter. It usually shows your current location or "Nearby" near the top of the page.

### 3. Search and Select Your City

Type your city name in the search box.

**Critical**: Select the **correct** city from the dropdown. Many cities share names:

| Search Term | Correct Selection | Incorrect |
|-------------|-------------------|-----------|
| "Medellín" | Medellín, Antioquia, Colombia | Medellín, Philippines |
| "San José" | San José, Costa Rica | San Jose, CA |
| "Valencia" | Valencia, Venezuela | Valencia, Spain |

### 4. Copy the location_id from URL

After selecting your city, the URL bar will update. Find the `location_id` parameter:

```
https://web.facebook.com/events/?location_id=111841478834264&...
                                             ^^^^^^^^^^^^^^^^
                                             Copy this number
```

### 5. Add to Configuration

Edit `config/sources.yaml`:

```yaml
sources:
  facebook:
    enabled: true
    locations:
      - location_id: "111841478834264"        # <-- Paste your ID here
        location_name: "Medellín, Antioquia"  # <-- Human-readable name
        date_filter: "THIS_WEEK"              # Or THIS_WEEKEND, THIS_MONTH
        scroll_count: 3                       # How many times to scroll (more = more events)
        scroll_delay_seconds: 5.0             # Delay between scrolls (higher = safer)
```

### 6. Verify Setup

Run the research skill to verify events are discovered:

```
/research facebook-discover
```

You should see events appear for your location.

## Adding Multiple Cities

You can configure multiple locations for multi-city newsletters:

```yaml
sources:
  facebook:
    locations:
      - location_id: "111841478834264"
        location_name: "Medellín, Antioquia"
      - location_id: "987654321"
        location_name: "Bogotá, Colombia"
        date_filter: "THIS_MONTH"  # Different filter per city
```

## Known location_id Values

| City | location_id | Notes |
|------|-------------|-------|
| Medellín, Antioquia | 111841478834264 | Colombia |
| Hudson Valley, NY | _(contribute!)_ | USA |
| Brooklyn, NY | _(contribute!)_ | USA |

_Help grow this list! Add your city's location_id when you discover it._

## Troubleshooting

### "No events found" but I know there are events

1. **Check disambiguation**: Did you select the right city? Re-copy the location_id.
2. **Broaden date range**: Try `THIS_MONTH` instead of `THIS_WEEK`
3. **Check login status**: Open Facebook in Chrome and verify you're logged in
4. **Try more scrolls**: Increase `scroll_count` to 5 or more

### "Authentication required" error

1. Open Chrome (the same browser Claude Code uses)
2. Navigate to facebook.com
3. Log in manually
4. Keep Chrome open while running the skill

### Events are missing data (no venue, wrong date)

This is expected for discovery mode. Facebook's event cards show limited info. Events are marked `needs_review: true` so you can verify them before publishing.

### Rate limiting / errors after many requests

1. Increase `scroll_delay_seconds` to 7-10
2. Decrease `scroll_count` to 2-3
3. Wait 10-15 minutes before retrying
