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
    """Normalizes shouting text and preserves Roman Numerals/Acronyms."""
    if not text: return ""
    # Remove HTML tags and extra whitespace
    text = re.sub('<[^<]+?>', ' ', text)
    text = " ".join(text.split())
    
    words = text.lower().split()
    caps_list = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "dlnr", "rcuh", "dar", "scuba", "sop"]
    return " ".join(w.upper() if w in caps_list else w.capitalize() for w in words)

def parse_salary(desc):
    """Extracts salary and converts to annual numeric value for the UI toggle."""
    if not desc: return None
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
    """Pulls DLNR jobs and Duties from the NEOGOV RSS feed."""
    jobs = []
    ns = {'joblisting': 'http://www.neogov.com/namespaces/JobListing'}
    try:
        r = requests.get(NEOGOV_FEED, timeout=30)
        root = ElementTree.fromstring(r.content)
        for item in root.findall("./channel/item"):
            dept = item.findtext("joblisting:department", namespaces=ns) or ""
            if "Land & Natural Resources" in dept or "DLNR" in dept:
                raw_title = item.findtext("title") or ""
                title_part, loc_part = raw_title.split("-", 1) if "-" in raw_title else (raw_title, "Hawaii")
                
                # Pull the specific Duties field from the XML
                duties_raw = item.findtext("joblisting:examplesofduties", namespaces=ns) or ""
                
                jobs.append({
                    "title": clean_text(title_part),
                    "job_number": item.findtext("joblisting:jobNumberSingle", namespaces=ns) or "N/A",
                    "division": clean_text(item.findtext("joblisting:division", namespaces=ns) or "DLNR"),
                    "location": clean_text(loc_part),
                    "yearly_salary": parse_salary(item.findtext("description") or ""),
                    "posted": item.findtext("pubDate")[:16] if item.findtext("pubDate") else "",
                    "closing": item.findtext("joblisting:advertiseToDateTime", namespaces=ns) or "Continuous",
                    "link": item.findtext("link"),
                    "duties": clean_text(duties_raw)
                })
    except Exception as e:
        print(f"Civil Service Error: {e}")
    return jobs

def scrape_rcuh_compass():
    """Scrapes RCUH positions and follows links to grab 'Duties' section."""
    jobs = []
    try:
        r = requests.get(COMPASS_URL, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if cols and "RCUH" in cols[0].text:
                full_text = cols[0].text.strip()
                id_match = re.search(r'ID#\s*(\d+)', full_text)
                
                link_tag = row.find('a')
                detail_url = link_tag['href'] if link_tag else None
                
                # Fetch Duties from the detail page
                duties_text = "Click 'View Job' for full details."
                if detail_url:
                    try:
                        detail_res = requests.get(detail_url, timeout=15)
                        detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
                        # Look for the text after "DUTIES:"
                        content = detail_soup.get_text()
                        if "DUTIES:" in content:
                            # Grab everything between DUTIES and the next major header (usually PRIMARY QUALIFICATIONS)
                            parts = content.split("DUTIES:")
                            if len(parts) > 1:
                                duties_raw = parts[1].split("PRIMARY QUALIFICATIONS")[0].strip()
                                duties_text = clean_text(duties_raw)
                    except: pass

                loc_badge = row.find('span', class_='badge')
                location = loc_badge.text.strip() if loc_badge else "Hawaii"
                title_clean = full_text.split(':', 1)[-1].split('ID#')[0].strip(" –-")
                
                jobs.append({
                    "title": clean_text(title_clean),
                    "id": id_match.group(1) if id_match else "N/A",
                    "project": "Conservation / DAR",
                    "location": clean_text(location),
                    "posted": cols[1].text.strip() if len(cols) > 1 else "",
                    "closing": cols[2].text.strip() if len(cols) > 2 else "Continuous",
                    "link": detail_url or COMPASS_URL,
                    "duties": duties_text
                })
    except Exception as e:
        print(f"RCUH Error: {e}")
    return jobs

def main():
    print("Starting scrape...")
    civil = scrape_civil_service()
    print(f"Collected {len(civil)} Civil Service jobs.")
    
    rcuh = scrape_rcuh_compass()
    print(f"Collected {len(rcuh)} RCUH jobs.")

    data = {
        "civil_service": civil,
        "rcuh": rcuh,
        "generated_at_utc": datetime.now(timezone.utc).isoformat()
    }
    
    with open("jobs.json", "w") as f:
        json.dump(data, f, indent=2)
    print("jobs.json updated successfully.")

if __name__ == "__main__":
    main()
