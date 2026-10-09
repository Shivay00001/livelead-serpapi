#!/usr/bin/env python3
"""Unit tests for livelead.py — all SerpApi calls mocked, no key needed."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livelead

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name}")


def test_score_lead():
    print("score_lead:")
    b = {"phone": "+1", "website": "https://x.com", "rating": "4.5",
         "reviews": 50, "hours": "Mon-Fri", "organic_links": []}
    s, reasons = livelead.score_lead(b)
    check("full signal scores high", s >= 85)
    check("reasons listed", len(reasons) >= 4)

    b2 = {"phone": "+1", "website": None, "rating": "4.2",
          "reviews": 30, "hours": None, "organic_links": []}
    s2, r2 = livelead.score_lead(b2)
    check("no-website phone lead flagged", any("needs a website" in r for r in r2))
    check("no-website scores lower than full", s2 < s)

    s3, _ = livelead.score_lead({})
    check("empty biz scores 0", s3 == 0)


def test_output_json_and_csv(tmpdir="/tmp"):
    print("output writers:")
    leads = [{"name": "A", "score": 90, "reasons": ["has phone"],
              "phone": "1", "website": None, "rating": "4.0",
              "reviews": 10, "address": "X", "hours": None,
              "organic_links": [], "query": "q", "location": "l"}]
    jp = os.path.join(tmpdir, "t.json")
    livelead.write_json(leads, jp)
    with open(jp) as f:
        back = json.load(f)
    check("json roundtrip", back[0]["name"] == "A" and back[0]["score"] == 90)

    cp = os.path.join(tmpdir, "t.csv")
    livelead.write_csv(leads, cp)
    with open(cp) as f:
        content = f.read()
    check("csv has header+row", "name,score" in content and ",90," in content)


def test_serpapi_get_injects_key():
    print("serpapi_get:")
    calls = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"local_results": []}'

    import urllib.request
    orig = urllib.request.urlopen

    def fake(req, timeout=30):
        calls["url"] = req.full_url if hasattr(req, "full_url") else req
        return FakeResp()

    urllib.request.urlopen = fake
    try:
        data = livelead.serpapi_get({"engine": "google_maps"}, "KEY123")
        check("returns parsed json", data == {"local_results": []})
        check("api_key injected in url", "api_key=KEY123" in calls["url"])
    finally:
        urllib.request.urlopen = orig


def test_serpapi_error_raised():
    print("serpapi error path:")
    import urllib.request
    orig = urllib.request.urlopen

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"error": "bad key"}'

    urllib.request.urlopen = lambda url, timeout=30: FakeResp()
    try:
        try:
            livelead.serpapi_get({}, "BAD")
            check("error raises", False)
        except livelead.SerpApiError as e:
            check("error raises", "bad key" in str(e))
    finally:
        urllib.request.urlopen = orig


if __name__ == "__main__":
    test_score_lead()
    test_output_json_and_csv()
    test_serpapi_get_injects_key()
    test_serpapi_error_raised()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
