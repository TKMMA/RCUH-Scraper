# 🌊 RCUH Contract Positions Scraper

An automated, interactive job dashboard focused specifically on **RCUH contract opportunities** relevant to Hawaii Division of Aquatic Resources programs.

View here:
[https://tkmma.github.io/Double-Scraper/](https://tkmma.github.io/RCUH-Scraper/)

## 🚀 Key Features
- **RCUH-Only Aggregation:** Collects active RCUH postings via `conservationcompass.org`.
- **Throttled Deep-Scraping:** Visits each listing detail page with a delay to reduce session and rate-limit issues.
- **Interactive UI:** Built with DataTables.js, featuring:
  - **Keyword Filtering:** Toggle visibility for roles tied to keywords like **DAR**, **HCRI**, **Coral**, and **Fish**.
  - **Salary Toggle:** Switch between Annual ($/yr) and Monthly ($/mo) salary views.
  - **Accordion Summaries:** Click a row to view extracted duties without leaving the page.
- **Readable Visual Theme:** Inter font with a high-visibility palette for fast scanning.

## 🛠️ Scraper Strategy
Directly scraping the RCUH portal can trigger session issues. This project uses a **throttled hybrid scraper** that:
1. Scans `conservationcompass.org` for active RCUH jobs.
2. Applies a **2-second delay** between detail-page requests.
3. Parses salary and duties content into a normalized JSON file.

## 🤖 Automation & Deployment
- **Scraper:** `scraper.py` runs daily at **8:00 AM HST** via GitHub Actions.
- **Storage:** Output is saved to `jobs.json`.
- **Hosting:** Frontend is served via GitHub Pages.

## 📁 Repository Structure
- `.github/workflows/scrape.yml`: Daily automation workflow.
- `scraper.py`: RCUH scraping logic.
- `index.html`: Bootstrap/DataTables frontend.
- `jobs.json`: Latest synchronized dataset.

---
*Built to streamline discovery of RCUH conservation-related positions in Hawaiʻi.*
