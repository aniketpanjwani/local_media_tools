# Workflow: Research Instagram

<required_reading>
Read before proceeding:
- `references/scrapecreators-api.md`
- `references/event-detection.md`
</required_reading>

<critical>
**PROCESS EVERY SINGLE POST.** You MUST iterate through ALL posts from ALL accounts. Do not stop early, do not summarize, do not skip posts.

**NOT EVERY POST IS AN EVENT.** You must classify each post first. Only posts that announce specific upcoming events should become Event objects. Skip posts that are:
- Food/drink photos
- Staff/team photos
- Venue interior shots
- Memes or reposts
- General announcements without event details
- Throwback/recap posts of past events
</critical>

<process>
## Step 1: Load Configuration

```python
from config.config_schema import AppConfig
from pathlib import Path

config_path = Path.home() / ".config" / "local-media-tools" / "sources.yaml"
config = AppConfig.from_yaml(config_path)
accounts = config.sources.instagram.accounts
```

## Step 2: Scrape Posts from Each Account

**IMPORTANT:** You MUST track the exact count of posts received from EACH account.

For each Instagram account in the config:

```python
from scripts.scrape_instagram import ScrapeCreatorsClient
from schemas.event import InstagramProfile, InstagramPost

client = ScrapeCreatorsClient()
all_posts_by_account: dict[str, list[InstagramPost]] = {}

for account in accounts:
    result = client.get_instagram_user_posts(account.handle, limit=20)

    # Extract profile info from first post's owner data
    if result.get("posts"):
        first_post = result["posts"][0]["node"]
        owner = first_post.get("owner", {})
        profile = InstagramProfile(
            instagram_id=owner.get("id", ""),
            handle=owner.get("username", account.handle),
        )

    # Create InstagramPost objects from API response
    posts = []
    for post_data in result.get("posts", []):
        node = post_data.get("node", {})
        post = InstagramPost.from_api_response(node)
        posts.append(post)

    all_posts_by_account[account.handle] = posts
    print(f"Received {len(posts)} posts from @{account.handle}")

    # Save raw data
    data_dir = Path.home() / ".config" / "local-media-tools" / "data"
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
```

**After scraping ALL accounts, display a summary table:**

| Account | Posts Fetched |
|---------|---------------|
| @handle1 | 12 |
| @handle2 | 15 |
| **Total** | **27** |

## Step 3: Classify EVERY Post (Caption-First)

**You MUST process EVERY SINGLE POST. Do not stop early. Do not summarize.**

Maintain a counter and announce progress: "Classifying post {i}/{total}..."

### Step 3a: Check Media Type First

For each post, check `media_type`:
- If `media_type` is "video" or "reel": Mark `needs_image_analysis = False` (no static images to analyze)
- If `media_type` is "photo" or "carousel": Image analysis may be needed

### Step 3b: Analyze Caption (Before Looking at Images)

Based on the caption text ALONE, classify the post:

**CLEARLY_NOT_EVENT** (skip image analysis entirely):
- Thank you / gratitude posts ("Thanks to our community...")
- Past event recaps ("Last night was amazing...", "What a show!")
- Promotional content with no dates
- News/announcements without event details
- Behind-the-scenes content
- Food/drink menu posts
- Videos/reels (no static images to analyze)

**CLEARLY_EVENT** (proceed to image analysis for details):
- Contains specific future date ("December 20", "this Saturday", "Jan 15")
- Contains time ("8pm", "doors at 7", "starts at 9")
- Contains venue/location
- Contains event keywords ("show", "concert", "live music", "performance", "DJ set")

**AMBIGUOUS** (requires image analysis to determine):
- Flyer-style post with minimal/no caption
- Caption mentions event but details unclear
- Need to check images for date/time/venue

### Step 3c: Record Classification

For each post, record:
- `classification`: "event" | "not_event" | "ambiguous"
- `classification_reason`: Brief explanation (e.g., "past event recap", "has future date Dec 20")
- `needs_image_analysis`: true | false

**After classifying ALL posts, display a summary table:**

| Classification | Count | Needs Image Analysis |
|---------------|-------|----------------------|
| CLEARLY_EVENT | 8 | Yes (8) |
| CLEARLY_NOT_EVENT | 52 | No |
| AMBIGUOUS | 12 | Yes (12) |
| **Total** | **72** | **20** |

**Verify:** Total in table MUST equal total posts fetched in Step 2.

## Step 4: Download and Analyze Images (Conditional)

**Only for posts where `needs_image_analysis = True`:**

### For Carousel Posts (media_type = "carousel"):
1. The post contains MULTIPLE images in `image_urls` list
2. Event flyers are often in positions 2, 3, or 4 (not always the first image!)
3. Analyze each image in order until you find clear event information
4. Note which image index contained the event flyer

### For Single Image Posts:
1. Analyze the single `display_url` image
2. Extract event details if visible

### Image Analysis Prompt:
```
Analyze this image from an Instagram post.

Is this an event flyer or promotional image with event details?

If YES, extract:
- Event title
- Date (format: YYYY-MM-DD)
- Time (format: HH:MM)
- Venue name
- Price/admission (or "Free" or "Unknown")

If NO (e.g., food photo, venue shot, meme), respond: "NOT_EVENT_IMAGE"
```

## Step 5: Extract Event Details

For posts classified as events (after caption + image analysis):

**For ONE_EVENT posts:**
1. Combine caption + image data
2. Extract: title, date, time, venue, price, ticket URL
3. Create ONE Event object

**For MULTIPLE_EVENTS posts:**
1. Identify each distinct event in the post
2. For EACH event, extract: title, date, time, venue, price
3. Create SEPARATE Event objects for each
4. All events share the same source_url (the post URL)

**Extraction format:**
```
1. Jazz Night | 2025-01-20 | 20:00 | MAMM | Free
2. Open Mic | 2025-01-22 | 19:00 | MAMM | Free
3. Live Band | 2025-01-24 | 21:00 | MAMM | $10
```

## Step 6: Create Event Objects and Track by Post

**Only for classified events with extractable details:**

```python
from schemas.event import Event, Venue, EventSource

# Track which events came from which post
events_by_post: dict[str, list[Event]] = {}

for post in posts:
    if post.classification == "event":
        extracted_events = extract_events_from_post(post)
        for event_data in extracted_events:
            event = Event(
                title=event_data["title"],
                venue=Venue(name=event_data["venue"], instagram_handle=account.handle),
                event_date=event_data["date"],
                source=EventSource.INSTAGRAM,
                source_url=post.post_url,
                image_url=post.display_url,
                confidence=event_data.get("confidence", 0.8),
            )
            if post.instagram_post_id not in events_by_post:
                events_by_post[post.instagram_post_id] = []
            events_by_post[post.instagram_post_id].append(event)
```

## Step 7: Save Results

```python
from schemas.sqlite_storage import SqliteStorage

db_path = Path.home() / ".config" / "local-media-tools" / "data" / "events.db"
storage = SqliteStorage(db_path)

# Save profile, posts, and events with FK relationships
result = storage.save_instagram_scrape(
    profile=profile,
    posts=posts,
    events_by_post=events_by_post
)
```

## Step 8: Report Final Summary

**REQUIRED:** Display a complete summary showing ALL posts were processed.

### Per-Account Breakdown:
```
@elmamm: 12 posts scraped
  Classification:
    - 3 CLEARLY_EVENT (image analysis: 3)
    - 7 CLEARLY_NOT_EVENT (skipped: 4 food photos, 2 past recaps, 1 meme)
    - 2 AMBIGUOUS (image analysis: 2)
  Events extracted:
    - 2 posts with single events -> 2 events
    - 1 post with weekly schedule -> 5 events
    - Total: 7 events

@cineplexcol: 12 posts scraped
  Classification:
    - 4 CLEARLY_EVENT (image analysis: 4)
    - 8 CLEARLY_NOT_EVENT (skipped: movie stills)
    - 0 AMBIGUOUS
  Events extracted:
    - 4 posts with single events -> 4 events
    - Total: 4 events
```

### Overall Summary Table:
| Metric | Count |
|--------|-------|
| Total posts scraped | 72 |
| Posts classified as events | 12 |
| Posts classified as not events | 52 |
| Posts classified as ambiguous | 8 |
| Image analyses performed | 20 |
| Image analyses skipped | 52 |
| Total events extracted | 15 |
| Events needing review | 2 |

**Verify:** "Total posts scraped" MUST match the sum from Step 2.
</process>

<success_criteria>
Instagram research complete when:
- [ ] All configured accounts scraped
- [ ] Post count from API matches posts processed (verify with summary table)
- [ ] Each post classified as event, not_event, or ambiguous
- [ ] Videos/reels skipped for image analysis (no static images)
- [ ] Caption-first classification reduced unnecessary image analysis
- [ ] All carousel images considered (not just first image)
- [ ] All events from multi-event posts extracted separately
- [ ] Only actual events saved to database (not all posts!)
- [ ] Final summary shows complete breakdown with matching totals
- [ ] Raw data saved to `~/.config/local-media-tools/data/raw/`
</success_criteria>
