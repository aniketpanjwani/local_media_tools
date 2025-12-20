# Workflow: Research Instagram

<critical>
## Use CLI Tool - Never curl

**ALWAYS use the CLI tool to scrape Instagram.** Never use curl or raw API calls.

```bash
# Scrape all configured accounts
uv run python scripts/cli_instagram.py scrape --all

# Scrape specific account
uv run python scripts/cli_instagram.py scrape --handle wayside_cider

# Check what's in the database
uv run python scripts/cli_instagram.py list-posts --handle wayside_cider
uv run python scripts/cli_instagram.py show-stats
```

The CLI ensures:
- Correct API parameters (`handle`, not `username`)
- Rate limiting (2 calls/second)
- Automatic retry on 429/5xx errors
- Proper database storage with FK relationships
</critical>

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
## Step 1: Scrape Posts Using CLI

**Run the CLI tool to scrape all configured Instagram accounts:**

```bash
uv run python scripts/cli_instagram.py scrape --all
```

This will:
- Fetch posts from all accounts in `~/.config/local-media-tools/sources.yaml`
- Save posts to the SQLite database
- Save raw API responses to `~/.config/local-media-tools/data/raw/`
- Show you a summary of fetched vs new posts

Example output:
```
Scraping 5 Instagram account(s)...

  @wayside_cider... 12 posts (12 new)
  @basilicahudson... 12 posts (0 new)

==================================================
SUMMARY: 24 posts fetched, 12 new
==================================================

Account                      Fetched        New      In DB
-------------------------------------------------------
@wayside_cider                    12         12          0
@basilicahudson                   12          0         12
-------------------------------------------------------
TOTAL                             24         12         12
```

## Step 2: Check Which Posts Need Classification

**List unclassified posts for each account:**

```bash
uv run python scripts/cli_instagram.py list-posts --handle wayside_cider
```

This shows all posts with their classification status. Focus on "unclassified" posts.

**To see all classified posts only:**

```bash
uv run python scripts/cli_instagram.py list-posts --handle wayside_cider --classified-only
```

**Skip accounts where all posts are already classified.**

## Step 3: Classify NEW Posts Only (Caption-First)

**You MUST process every unclassified post from Step 2.** Already-classified posts keep their existing classification.

Maintain a counter and announce progress: "Classifying post {i}/{total} (new posts only)..."

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

**After classifying all NEW posts, display a summary table:**

| Classification | New Posts | Skipped (Already Analyzed) |
|---------------|-----------|---------------------------|
| CLEARLY_EVENT | 2 | 6 |
| CLEARLY_NOT_EVENT | 2 | 46 |
| AMBIGUOUS | 1 | 5 |
| **Total** | **5** | **57** |

**Verify:** New Posts total MUST equal "New to Analyze" from Step 2b.

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
| Total posts from API | 72 |
| Already analyzed (skipped) | 57 |
| **New posts analyzed** | **15** |
| New posts → events | 3 |
| New posts → not events | 10 |
| New posts → ambiguous | 2 |
| Image analyses performed | 5 |
| Total events extracted (new) | 4 |
| Events from skipped posts (re-used) | 11 |
| Events needing review | 1 |

**Verify:** "New posts analyzed" MUST equal "New to Analyze" from Step 2b.
</process>

<success_criteria>
Instagram research complete when:
- [ ] CLI tool used to scrape accounts (NOT curl!)
- [ ] All configured accounts scraped via `uv run python scripts/cli_instagram.py scrape --all`
- [ ] Raw data saved to `~/.config/local-media-tools/data/raw/`
- [ ] Unclassified posts identified via `list-posts` command
- [ ] New posts classified as event, not_event, or ambiguous
- [ ] Videos/reels skipped for image analysis (no static images)
- [ ] Caption-first classification reduced unnecessary image analysis
- [ ] All carousel images considered (not just first image)
- [ ] All events from multi-event posts extracted separately
- [ ] Only actual events saved to database (not all posts!)
- [ ] Final summary shows new vs skipped breakdown
</success_criteria>
