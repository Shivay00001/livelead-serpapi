# LiveLead — 3-minute demo video script
# SerpApi India Hackathon 2026 submission

## 0:00–0:20 — Hook (screen: terminal)
"Finding good outreach leads means hours of manual Google Maps digging.
LiveLead does it in one command — using live search data from SerpApi."

## 0:20–1:00 — Live run (screen: terminal, real run)
Run:
  export SERPAPI_KEY=$SERPAPI_KEY
  python3 livelead.py "dental clinic" "Birmingham, UK" --limit 5 --out leads.json
Show the per-business lines appearing with scores. Then:
  cat leads.json | head -40
Point at a lead with "no website found -> needs a website pitch".

## 1:00–1:50 — How SerpApi does the work (screen: code / README table)
"Three live SerpApi calls per business: Google Maps search for discovery,
Maps place-details for hours and reviews, organic Google search to check
web presence. The score is computed from live signals — nothing is cached."

## 1:50–2:30 — CSV output (screen: spreadsheet)
  python3 livelead.py "salon" "Mumbai" --limit 10 --format csv --out leads.csv
Open leads.csv — sorted by score, ready to import into any outreach tool.

## 2:30–3:00 — Close (screen: GitHub repo)
"LiveLead is open source — link in the description.
Built by Shivam Kumar, VisionQuantech, for the SerpApi India Hackathon 2026."

## Recording notes
- Keep under 3 minutes (hard requirement).
- Blur the API key if visible: export it before recording, never `echo` it.
- 1080p screen capture is fine; phone mic is fine.
