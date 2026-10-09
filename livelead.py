#!/usr/bin/env python3
"""
LiveLead — live-search lead research for small businesses.
Built for the SerpApi India Hackathon 2026.

Given a business category + city, LiveLead uses SerpApi (Google Maps +
organic Google Search) to find real businesses, enrich each with live data
(rating, reviews, phone, website, hours), and score them as outreach leads.

Usage:
    export SERPAPI_KEY=your_key
    python3 livelead.py "dental clinic" "Birmingham, UK" --limit 10 --out leads.json
    python3 livelead.py "salon" "Mumbai" --limit 10 --format csv --out leads.csv

SerpApi free plan (100 searches/month) is enough for the demo.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

SERPAPI_BASE = "https://serpapi.com/search.json"


class SerpApiError(Exception):
    pass


def serpapi_get(params, api_key, retries=2):
    """GET SerpApi with key injected; raises SerpApiError on failure."""
    q = dict(params)
    q["api_key"] = api_key
    url = SERPAPI_BASE + "?" + urllib.parse.urlencode(q)
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LiveLead/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                raise SerpApiError(data["error"])
            return data
        except SerpApiError:
            raise
        except Exception as e:  # noqa: BLE001 - network flakiness, retry
            last_err = e
            time.sleep(1 + attempt)
    raise SerpApiError(f"request failed after {retries + 1} tries: {last_err}")


def maps_search(query, location, api_key, limit=10):
    """Google Maps search via SerpApi. Returns list of local_results dicts."""
    # SerpApi google_maps needs ll (@lat,lng,zoom) when using location param
    # Default to Mumbai coordinates if location mentions Mumbai, else use generic
    coords = "@19.0760,72.8777,14z"  # Mumbai
    if "delhi" in location.lower():
        coords = "@28.6139,77.2090,14z"
    elif "birmingham" in location.lower():
        coords = "@52.4862,-1.8904,14z"
    data = serpapi_get(
        {"engine": "google_maps", "q": f"{query} in {location}", "ll": coords, "type": "search"},
        api_key,
    )
    return (data.get("local_results") or [])[:limit]


def enrich_place(place, api_key):
    """Fetch place details (hours, reviews snippet) via SerpApi Maps."""
    data_id = place.get("data_id")
    if not data_id:
        return {}
    try:
        data = serpapi_get(
            {"engine": "google_maps", "type": "place", "data": f"!4m5!3m4!1s{data_id}"},
            api_key,
        )
        result = data.get("place_results") or {}
        return {
            "hours": result.get("hours"),
            "reviews_link": result.get("reviews_link"),
            "description": (result.get("about") or {}).get("description"),
        }
    except SerpApiError:
        return {}


def organic_check(name, api_key):
    """Quick organic-search check: does the business have a findable website?"""
    try:
        data = serpapi_get(
            {"engine": "google", "q": f'"{name}" official website', "num": 3}, api_key
        )
        organic = data.get("organic_results") or []
        return [r.get("link") for r in organic[:3] if r.get("link")]
    except SerpApiError:
        return []


def score_lead(biz):
    """Heuristic lead score 0-100. Higher = better outreach target.

    Signals: has phone (+25), has website (+20), rating >= 4.0 (+15),
    review count in sweet spot 10-200 (+15), no website found organically
    but has phone (+15 => needs a website pitch), has hours listed (+10).
    """
    score, reasons = 0, []
    if biz.get("phone"):
        score += 25
        reasons.append("has phone")
    if biz.get("website"):
        score += 20
        reasons.append("has website")
    try:
        rating = float(biz.get("rating") or 0)
    except (TypeError, ValueError):
        rating = 0
    if rating >= 4.0:
        score += 15
        reasons.append(f"rating {rating}")
    try:
        reviews = int(str(biz.get("reviews") or "0").replace(",", ""))
    except (TypeError, ValueError):
        reviews = 0
    if 10 <= reviews <= 200:
        score += 15
        reasons.append(f"{reviews} reviews (sweet spot)")
    if biz.get("hours"):
        score += 10
        reasons.append("hours listed")
    if biz.get("phone") and not biz.get("website") and not biz.get("organic_links"):
        score += 15
        reasons.append("no website found -> needs a website pitch")
    return min(score, 100), reasons


def write_json(leads, path):
    with open(path, "w") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


def write_csv(leads, path):
    fields = ["name", "score", "phone", "website", "rating", "reviews",
              "address", "hours", "organic_links", "reasons", "query", "location"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for lead in leads:
            row = dict(lead)
            row["reasons"] = "; ".join(lead.get("reasons", []))
            row["organic_links"] = "; ".join(lead.get("organic_links", []))
            w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description="LiveLead — live-search lead research (SerpApi India Hackathon 2026)")
    ap.add_argument("query", help='business category, e.g. "dental clinic"')
    ap.add_argument("location", help='city/region, e.g. "Birmingham, UK"')
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--format", choices=["json", "csv"], default="json")
    ap.add_argument("--out", default="leads.json")
    ap.add_argument("--no-enrich", action="store_true", help="skip place-details enrichment (saves API calls)")
    args = ap.parse_args()

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("error: set SERPAPI_KEY env var (free plan at serpapi.com — 100 searches/month)",
              file=sys.stderr)
        return 1

    print(f"maps search: {args.query} in {args.location} ...", file=sys.stderr)
    places = maps_search(args.query, args.location, api_key, args.limit)
    print(f"found {len(places)} places", file=sys.stderr)

    leads = []
    for i, p in enumerate(places, 1):
        biz = {
            "name": p.get("title"),
            "phone": p.get("phone"),
            "website": p.get("website"),
            "rating": p.get("rating"),
            "reviews": p.get("reviews"),
            "address": p.get("address"),
            "query": args.query,
            "location": args.location,
        }
        if not args.no_enrich:
            extra = enrich_place(p, api_key)
            biz["hours"] = extra.get("hours")
            biz["reviews_link"] = extra.get("reviews_link")
        biz["organic_links"] = organic_check(biz["name"] or "", api_key)
        biz["score"], biz["reasons"] = score_lead(biz)
        leads.append(biz)
        print(f"  [{i}/{len(places)}] {biz['name']} -> {biz['score']}", file=sys.stderr)
        time.sleep(0.4)

    leads.sort(key=lambda b: b["score"], reverse=True)
    if args.format == "csv":
        write_csv(leads, args.out)
    else:
        write_json(leads, args.out)
    print(f"wrote {len(leads)} leads -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())