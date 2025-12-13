# Newsletter Events Write Skill

Generate formatted newsletters from collected event data.

## Trigger

This skill is triggered when the user wants to:
- Generate a newsletter from collected events
- Format events into markdown output
- Create a weekly events summary
- "Write the newsletter"
- "Generate this week's events"
- "Create the events summary"

## Prerequisites

Events must be collected first using the research skill. The events file should exist at `tmp/extraction/events.json`.

## Workflow

Based on the user's request:

1. **Generate newsletter** → Follow `workflows/generate-newsletter.md`
2. **Customize output** → Follow `workflows/customize-template.md`

## Quick Start

```python
from schemas.storage import EventStorage
from scripts.generate_newsletter import generate_newsletter, save_newsletter

# Load events
storage = EventStorage("tmp/extraction/events.json")
collection = storage.load()

# Generate newsletter
content = generate_newsletter(
    collection,
    title="Hudson Valley Events",
    subtitle="Your weekly guide to local happenings"
)

# Save
save_newsletter(content, "output/newsletter.md")
```

## References

- `references/template-guide.md` - Template customization guide
- `references/output-formats.md` - Available output formats
