# Template Customization Guide

## Default Template

The default newsletter template is at `templates/newsletter.md.j2`.

## Template Variables

Available variables in templates:

| Variable | Type | Description |
|----------|------|-------------|
| `title` | str | Newsletter title |
| `subtitle` | str | Subtitle (usually date range) |
| `events_by_day` | dict | Events grouped by day string |
| `flagged_events` | list | Events needing review |
| `generated_at` | str | Generation timestamp |
| `source_count` | int | Number of sources used |
| `total_events` | int | Total event count |

## Event Properties

Each event in `events_by_day` has:

```python
event.title           # Event name
event.venue.name      # Venue name
event.venue.city      # City
event.event_date      # Python date object
event.start_time      # Python time object
event.end_time        # Python time object (optional)
event.formatted_time  # "7:00 PM - 10:00 PM"
event.formatted_date  # "Friday, Dec 15"
event.day_of_week     # "Friday"
event.description     # Event description
event.ticket_url      # Ticket purchase link
event.source_url      # Original source link
event.image_url       # Event image
event.source          # EventSource enum
```

## Custom Templates

Create custom templates in `templates/`:

```jinja2
{# templates/custom.md.j2 #}

# {{ title }}

{% for day, events in events_by_day.items() %}
## {{ day }}

{% for event in events %}
- **{{ event.title }}** @ {{ event.venue.name }} ({{ event.formatted_time }})
{% endfor %}
{% endfor %}
```

Use with:

```python
content = generate_newsletter(
    collection,
    template_name="custom.md.j2",
)
```

## Jinja2 Filters

Available filters:

- `truncate(length)` - Truncate text to length
- `title` - Title case
- `lower` - Lowercase
- `upper` - Uppercase

Example:
```jinja2
{{ event.description | truncate(200) }}
```
