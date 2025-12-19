# Discover Event Sources Workflow

## Overview

This workflow discovers Instagram and Facebook event sources for a new city/region using Google search via the ScrapeCreators API.

## Prerequisites

- ScrapeCreators API key configured in `.env`
- City and region information from user

## Step 1: Prepare Search Queries

Based on the user's city and event types, construct targeted search queries.

### Query Templates

For each category, use these patterns:

```python
# Music venues
f"{city} music venues live concerts Instagram"
f"{city} live music bars site:instagram.com"

# Event aggregators
f"{city} events calendar Instagram"
f"{city} what's happening this week Instagram"

# Arts & Culture
f"{city} art gallery museum events Instagram"
f"{city} theatre theater shows Instagram"

# Festivals
f"{city} festivals 2025"
f"{city} annual events festivals"

# Facebook pages
f"{city} events site:facebook.com"
f"{city} concerts events Facebook"
```

### Region Code Mapping

Use the appropriate 2-letter region code:
- Canada: `CA`
- United States: `US`
- United Kingdom: `GB`
- Australia: `AU`

## Step 2: Execute Searches

Use the ScrapeCreators client to run searches:

```python
from scripts.scrape_instagram import ScrapeCreatorsClient

client = ScrapeCreatorsClient()

# Example for Winnipeg
queries = [
    "Winnipeg music venues live concerts Instagram",
    "Winnipeg events calendar Instagram",
    "Winnipeg festivals 2025",
    "Winnipeg concerts events site:facebook.com",
]

all_results = []
for query in queries:
    result = client.google_search(query, region="CA")
    if result.get("success"):
        all_results.extend(result.get("results", []))
```

**Important:** Run 4-6 searches to get comprehensive coverage. Each search costs 1 credit.

## Step 3: Extract Instagram Handles

Parse search results to find Instagram accounts:

```python
import re

def extract_instagram_handles(results: list[dict]) -> set[str]:
    """Extract Instagram handles from search results."""
    handles = set()

    for result in results:
        url = result.get("url", "")
        title = result.get("title", "")
        description = result.get("description", "")

        # From Instagram URLs
        if "instagram.com" in url:
            # Match instagram.com/username or instagram.com/username/
            match = re.search(r"instagram\.com/([a-zA-Z0-9_.]+)", url)
            if match:
                handle = match.group(1)
                # Skip Instagram system pages
                if handle not in ["p", "reel", "stories", "explore", "accounts"]:
                    handles.add(handle)

        # From @mentions in title/description
        mentions = re.findall(r"@([a-zA-Z0-9_.]+)", title + " " + description)
        handles.update(mentions)

    return handles
```

## Step 4: Extract Facebook Pages

Parse results for Facebook event pages:

```python
def extract_facebook_pages(results: list[dict]) -> list[dict]:
    """Extract Facebook pages from search results."""
    pages = []
    seen_urls = set()

    for result in results:
        url = result.get("url", "")
        title = result.get("title", "")

        if "facebook.com" in url and url not in seen_urls:
            # Clean up the URL
            # Extract page name from URL
            match = re.search(r"facebook\.com/([^/]+)", url)
            if match:
                page_id = match.group(1)
                # Skip Facebook system pages
                if page_id not in ["events", "groups", "pages", "watch", "marketplace"]:
                    pages.append({
                        "url": f"https://facebook.com/{page_id}/events",
                        "name": title.split(" - ")[0].split(" | ")[0].strip(),
                    })
                    seen_urls.add(url)

    return pages
```

## Step 5: Validate Instagram Handles

Check each handle exists and is public:

```python
def validate_instagram_handles(client, handles: set[str]) -> list[dict]:
    """Validate handles and get profile info."""
    valid_accounts = []

    for handle in handles:
        try:
            profile = client.get_instagram_profile(handle)

            # Check if profile is valid and public
            if profile and profile.get("username"):
                valid_accounts.append({
                    "handle": profile["username"],
                    "name": profile.get("full_name", profile["username"]),
                    "bio": profile.get("biography", ""),
                    "followers": profile.get("follower_count", 0),
                })
        except Exception as e:
            # Handle doesn't exist or is private
            pass

    return valid_accounts
```

**Note:** Each validation costs 1 credit. Consider limiting to top candidates.

## Step 6: Categorize Sources

Infer source type from bio and name:

```python
def categorize_source(account: dict) -> str:
    """Infer source type from profile info."""
    bio = account.get("bio", "").lower()
    name = account.get("name", "").lower()
    text = bio + " " + name

    if any(word in text for word in ["venue", "club", "bar", "lounge", "stage"]):
        return "music_venue"
    elif any(word in text for word in ["theatre", "theater", "playhouse"]):
        return "theater"
    elif any(word in text for word in ["gallery", "museum", "art"]):
        return "arts_center"
    elif any(word in text for word in ["festival", "fest"]):
        return "festival"
    elif any(word in text for word in ["events", "what's on", "happenings"]):
        return "aggregator"
    elif any(word in text for word in ["promoter", "presents", "productions"]):
        return "promoter"
    else:
        return "venue"
```

## Step 7: Generate YAML Config

Output the discovered sources as YAML:

```python
def generate_yaml_config(city: str, region: str, accounts: list[dict], fb_pages: list[dict]) -> str:
    """Generate YAML config snippet."""
    lines = [
        f"# Discovered sources for {city}, {region}",
        f"# Generated on {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "newsletter:",
        f'  name: "{city} Events Weekly"',
        f'  region: "{city}, {region}"',
        "",
        "sources:",
        "  instagram:",
        "    enabled: true",
        "    accounts:",
    ]

    # Sort by followers (most popular first)
    accounts.sort(key=lambda x: x.get("followers", 0), reverse=True)

    for account in accounts:
        lines.extend([
            f'      - handle: "{account["handle"]}"',
            f'        name: "{account["name"]}"',
            f'        type: "{categorize_source(account)}"',
            f'        location: "{city}, {region}"',
        ])
        if account.get("bio"):
            # Truncate long bios
            bio = account["bio"][:50] + "..." if len(account["bio"]) > 50 else account["bio"]
            lines.append(f'        notes: "{bio}"')
        lines.append("")

    if fb_pages:
        lines.extend([
            "",
            "  facebook:",
            "    enabled: true",
            "    pages:",
        ])
        for page in fb_pages:
            lines.extend([
                f'      - url: "{page["url"]}"',
                f'        name: "{page["name"]}"',
                "",
            ])

    return "\n".join(lines)
```

## Step 8: Present Results

Show the user:

1. **Summary of discovered sources:**
   - Number of Instagram accounts found
   - Number of Facebook pages found
   - Total API credits used

2. **The generated YAML config**

3. **Next steps:**
   - Review and edit the config
   - Add to `config/sources.yaml`
   - Run `newsletter-events-research` skill to test

## Example Output

```yaml
# Discovered sources for Winnipeg, MB
# Generated on 2025-12-13

newsletter:
  name: "Winnipeg Events Weekly"
  region: "Winnipeg, MB"

sources:
  instagram:
    enabled: true
    accounts:
      - handle: "thewecc"
        name: "West End Cultural Centre"
        type: "music_venue"
        location: "Winnipeg, MB"
        notes: "Winnipeg's best venue for live music since 1987"

      - handle: "pyramidcabaret"
        name: "Pyramid Cabaret"
        type: "music_venue"
        location: "Winnipeg, MB"

      - handle: "winnipegdowntownevents"
        name: "Winnipeg Downtown Events"
        type: "aggregator"
        location: "Winnipeg, MB"

  facebook:
    enabled: true
    pages:
      - url: "https://facebook.com/TheForks/events"
        name: "The Forks"

      - url: "https://facebook.com/RoyalMTC/events"
        name: "Royal Manitoba Theatre Centre"
```

## Tips for Better Discovery

1. **Run multiple searches** - Different queries find different sources
2. **Check follower counts** - Higher follower accounts are usually more active
3. **Review bios** - Helps with categorization and filtering
4. **Start broad, then narrow** - Begin with "city events" then drill into specific types
5. **Validate before adding** - Not all discovered accounts post events regularly
