# LiveLead — live-search lead research for small businesses

**Entry for the SerpApi India Hackathon 2026** · by Shivam Kumar (VisionQuantech)

Give LiveLead a business category and a city; it uses **SerpApi** (Google Maps
+ organic Google Search, all live data) to find real businesses, enrich each
with ratings, reviews, phone, website and hours, then scores them as outreach
leads with explainable reasons.

## Why SerpApi does real work here

Every data point in the output comes from a live SerpApi call — no static
lists, no cached data:

| Step | SerpApi engine | What it contributes |
|------|---------------|---------------------|
| 1. Discovery | `google_maps` (type=search) | real businesses for "query in location": name, phone, website, rating, review count, address |
| 2. Enrichment | `google_maps` (type=place) | hours, reviews link, business description |
| 3. Web-presence check | `google` (organic) | does the business have a findable website? (drives the "needs a website pitch" signal) |

The lead score (0–100) is computed from these live signals, so the output is
only as good as the search data — which is the point.

## Quick start

```bash
export SERPAPI_KEY=your_key   # free plan: serpapi.com (100 searches/month)
python3 livelead.py "dental clinic" "Birmingham, UK" --limit 10 --out leads.json
python3 livelead.py "salon" "Mumbai" --limit 10 --format csv --out leads.csv
```

Options: `--limit N` (default 10), `--format json|csv`, `--out FILE`,
`--no-enrich` (skips place-details calls to save API quota).

Example output (JSON):

```json
[
  {
    "name": "Smile Dental Studio",
    "phone": "+44 ...",
    "website": null,
    "rating": "4.6",
    "reviews": 87,
    "score": 85,
    "reasons": ["has phone", "rating 4.6", "87 reviews (sweet spot)",
                "no website found -> needs a website pitch"]
  }
]
```

## Lead scoring (explainable)

- has phone: +25 · has website: +20 · rating ≥ 4.0: +15
- review count 10–200 (sweet spot): +15 · hours listed: +10
- has phone but **no website found**: +15 → flagged "needs a website pitch"

## Tests

```bash
python3 test_livelead.py   # 10 tests, SerpApi mocked, no key needed
```

## Files

- `livelead.py` — the tool (stdlib only: no dependencies to install)
- `test_livelead.py` — unit tests
- `DEMO_SCRIPT.md` — 3-minute demo video script

## Author

Shivam Kumar — Founder, VisionQuantech (visionquantech.com).
AI research + done-for-you AI automation for small businesses.
Contact: contact@visionquantech.com
