# Workflow: Generate Newsletter

<required_reading>
Read before proceeding:
- `references/template-guide.md`
</required_reading>

<process>
## Step 1: Load Event Data

```python
from schemas.storage import EventStorage
from schemas.event import EventCollection

storage = EventStorage("tmp/extraction/events.json")

try:
    collection = storage.load()
except FileNotFoundError:
    # Run research skill first
    raise RuntimeError("No events found. Run the research skill first.")
```

## Step 2: Filter Events

Filter to only include events in the target date range:

```python
from datetime import date, timedelta

# Default to next 7 days
today = date.today()
week_end = today + timedelta(days=7)

# Filter events
events = [
    e for e in collection.events
    if e.event_date and today <= e.event_date <= week_end
]
```

## Step 3: Generate Newsletter

```python
from scripts.generate_newsletter import generate_newsletter, save_newsletter

content = generate_newsletter(
    collection,
    title="This Week's Events",  # Or user-provided title
    subtitle=None,  # Auto-generates from date range
)
```

## Step 4: Save Output

```python
from datetime import date

# Generate output filename
output_path = f"output/newsletter_{date.today().isoformat()}.md"

save_newsletter(content, output_path)
print(f"Newsletter saved to: {output_path}")
```

## Step 5: Report Summary

Print summary for user:
- Total events included
- Events by day breakdown
- Any flagged events needing review
- Output file location
</process>

<success_criteria>
Newsletter generation complete when:
- [ ] Events loaded from `tmp/extraction/events.json`
- [ ] Events filtered to target date range
- [ ] Newsletter generated with all events
- [ ] Output saved to `output/` directory
- [ ] Summary reported to user
</success_criteria>
