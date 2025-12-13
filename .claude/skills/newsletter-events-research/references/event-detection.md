# Event Detection Reference

## Overview

Detecting events from social media posts requires analyzing both text (captions) and images (flyers). Many venues only post event details in flyer images, so image analysis is critical.

## Text-Based Detection

### Event Indicators in Captions

Look for these patterns:
- Date formats: "Dec 15", "12/15", "Saturday"
- Time patterns: "8pm", "doors at 7"
- Action words: "tonight", "this weekend", "join us"
- Event types: "live music", "show", "performance"
- Ticket mentions: "tickets", "RSVP", "free entry"

### Confidence Scoring (Text)

| Pattern Found | Confidence Boost |
|---------------|------------------|
| Explicit date | +0.3 |
| Time mentioned | +0.2 |
| "Tonight" or "This [day]" | +0.2 |
| Ticket/entry info | +0.2 |
| Event type keyword | +0.1 |

## Image-Based Detection

### Vision Analysis Prompt

```
Analyze this image. Is this an event flyer or promotional poster?

If yes, extract:
1. Event title/name
2. Date (format: YYYY-MM-DD if possible)
3. Time (format: HH:MM, 24-hour)
4. Venue name
5. Price/admission
6. Any URL or ticket link

If information is unclear or not visible, note "unclear" for that field.
Rate your confidence for each field (high/medium/low).
```

### Flyer Characteristics

Event flyers typically have:
- Bold text with event name
- Date prominently displayed
- Venue name/logo
- Artist/performer names
- Time and door info
- Ticket price or "FREE"
- Visual design elements (not just a photo)

### Non-Event Posts

Skip posts that are:
- Food/drink photos only
- Staff/team photos
- Venue interior shots
- Reposted memes
- Generic announcements

## Combining Sources

When same event appears on multiple platforms:

1. **Date conflicts**: Trust structured data (Facebook) over image extraction
2. **Time conflicts**: Trust the source with higher confidence
3. **Price conflicts**: Flag for manual review
4. **Venue conflicts**: Trust the source that matches config

## Date Parsing

Common formats to handle:
- "December 15, 2025"
- "Dec 15"
- "12/15"
- "12/15/25"
- "Saturday, Dec 15"
- "This Saturday"
- "Tonight"

For relative dates:
- "Tonight" → today's date
- "Tomorrow" → today + 1
- "This Saturday" → next Saturday from today
- "Next week" → flag for review
