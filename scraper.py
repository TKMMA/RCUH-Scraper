import json
import re
import requests
from datetime import datetime, timezone
from xml.etree import ElementTree
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
NEOGOV_FEED = "https://www.governmentjobs.com/SearchEngine/JobsFeed?agency=hawaii"
COMPASS_URL = "https://opportunities.conservationcompass.org/opportunity/filter/full-time-jobs"

def clean_text(text):
    """Normalizes shouting text and preserves Roman Numerals."""
    if not text: return ""
    text = re.sub('<[^<]+?>', '', text) # Strip HTML tags
    words = text.lower().split()
    roman = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
    return " ".join(w.upper() if w in roman or w in ["dlnr", "rcuh"] else w.capitalize() for w in words)

def parse_salary(desc):
    """Extracts salary and converts to annual numeric value for the UI toggle."""
    text = re.sub('<[^<]+?>', ' ', desc)
    pattern = r'\$\s*([\d,]+(?:\.\d+)?)(?:\s+to\s+\$\s*[\d,]+(?:\.\d+)?)?\s*per\s*(month|year|hr|hour)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            amount = float(match.group(1).replace(',', ''))
            unit = match.group(2).lower()
            if 'month' in unit: return amount * 12
            if 'yr' in unit or 'year' in unit: return amount
            if 'hr' in unit or 'hour' in unit: return amount * 2080
        except: return None
    return None

def scrape_civil_service():
    """Pulls DLNR jobs from the NEOGOV RSS feed."""
    jobs = []
    ns = {'joblisting': 'http://www.neogov.com/namespaces/JobListing'}
    try:
        r = requests.get(NEOGOV_FEED, timeout=30)
        root = ElementTree.fromstring(r.content)
        for item in root.findall("./channel/item"):
            dept = item.findtext("joblisting:department", namespaces=ns) or ""
            if "Land & Natural Resources" in dept or "DLNR" in dept:
                raw_title = item.findtext("title") or ""
                # Split Title/Location at "-"
                title_part, loc_part = raw_title.split("-", 1) if "-" in raw_title else (raw_title, "Hawaii")
                
                jobs.append({
                    "title": clean_text(title_part),
                    "job_number": item.findtext("joblisting:jobNumberSingle", namespaces=ns) or "N/A",
                    "division": clean_text(item.findtext("joblisting:division", namespaces=ns) or "DLNR"),
                    "location": clean_text(loc_part),
                    "yearly_salary": parse_salary(item.findtext("description") or ""),
                    "posted": item.findtext("pubDate")[:16] if item.findtext("pubDate") else "",
                    "closing": item.findtext("joblisting:advertiseToDateTime", namespaces=ns) or "Continuous",
                    "link": item.findtext("link")
                })
    except Exception as e: print(f"Civil Service Error: {e}")
    return jobs

def scrape_rcuh_compass():
    """Scrapes RCUH positions from Conservation Career Compass."""
    jobs = []
    try:
        r = requests.get(COMPASS_URL, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if cols and "RCUH" in cols[0].text:
                full_text = cols[0].text.strip()
                id_match = re.search(r'ID#\s*(\d+)', full_text)
                # Extract island from the orange badges or text
                loc = row.find('span', class_='badge')
                location = loc.text.strip() if loc else "Hawaii"
                
                jobs.append({
                    "title": clean_text(full_text.split(':', 1)[-1].split('–')[0].split('ID#')[0]),
                    "id": id_match.group(1) if id_match else "N/A",
                    "project": "Conservation/DAR",
                    "location": clean_text(location),
                    "posted": cols[1].text.strip() if len(cols) > 1 else "",
                    "closing": cols[2].text.strip() if len(cols) > 2 else "Continuous",
                    "link": row.find('a')['href'] if row.find('a') else COMPASS_URL
                })
    except Exception as e: print(f"RCUH Error: {e}")
    return jobs

def main():
    data = {
        "civil_service": scrape_civil_service(),
        "rcuh": scrape_rcuh_compass(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat()
    }
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
