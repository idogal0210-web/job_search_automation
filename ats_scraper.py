import os
import requests
from bs4 import BeautifulSoup

# Energy & Infrastructure ATS Companies
ENERGY_COMEET_COMPANIES = [
    {"company": "SolarEdge", "uid": "solaredge", "sector": "אנרגיה סולארית וחשמל"},
    {"company": "Enlight Energy", "uid": "enlight", "sector": "אנרגיה מתחדשת"},
    {"company": "Augury", "uid": "augury", "sector": "ניטור מכונות ו-IIoT"},
]

# Dedicated Pure Drone, UAV, Robotics & Counter-UAS Companies
DRONE_COMEET_COMPANIES = [
    {"company": "XTEND", "uid": "xtend", "sector": "רחפנים אוטונומיים וביטחון"},
    {"company": "SpearUAV", "uid": "spearuav", "sector": "רחפנים משוטטים ורובוטיקה"},
    {"company": "Airobotics", "uid": "airobotics", "sector": "רחפנים אוטונומיים"},
    {"company": "HighLander", "uid": "highlander", "sector": "ניהול תנועת רחפנים ו-UAS"},
    {"company": "D-Fend Solutions", "uid": "d-fend", "sector": "הגנת C-UAS מפני רחפנים"},
    {"company": "NextVision", "uid": "nextvision", "sector": "אלקטרו-אופטיקה ומטע\"דים לרחפנים"},
]

ENERGY_KEYWORDS = [
    "gas", "energy", "mechanical", "control", "scada", "operator", "electrician", 
    "technician", "מכונות", "הנדסאי", "גז", "אנרגיה", "חשמל", "בקרה", "מפעיל", "טכנאי", "שירות שטח", "field", "operation"
]

# Strict Drone / UAV Anchor Keywords
DRONE_ANCHOR_KEYWORDS = [
    "drone", "uav", "uas", "flight", "pilot", "operator", "avionics", "fpv", "evtol", 
    "multirotor", "payload", "gcs", "integration", "field test", "technician", "assembly",
    "רחפן", "רחפנים", "כטבמ", "כטב\"ם", "מטיס", "מפעיל", "אינטגרציה", "הרכבה", "ניסויי טיסה", "מטע\"ד", "חיווט"
]

# Negative Keywords to reject non-drone/unrelated jobs
DRONE_NEGATIVE_KEYWORDS = [
    "naval", "submarine", "tank", "artillery", "weapon sight", "accounting", "hr manager", "legal"
]

def fetch_comeet_positions(company_uid, company_name, default_sector):
    """Fetch open positions from Comeet API."""
    url = f"https://www.comeet.com/jobs-api/v1/companies/{company_uid}/positions?token=undefined"
    jobs = []
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=6)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                for pos in data:
                    title = pos.get("name", "")
                    location_obj = pos.get("location", {})
                    city = location_obj.get("city", "ישראל") if isinstance(location_obj, dict) else "ישראל"
                    link = pos.get("url_active_page", "") or pos.get("url_comeet_hosted_page", "")
                    details = pos.get("details", "") or pos.get("experience_level", "") or ""
                    
                    if link and title:
                        jobs.append({
                            "title": title,
                            "company": company_name,
                            "location": city,
                            "link": link,
                            "snippet": f"{company_name} - {title}. {details}"[:400],
                            "sector": default_sector
                        })
    except Exception:
        # Graceful fallback - never crash
        pass
    return jobs

def get_energy_ats_jobs():
    """Extract and filter energy/infrastructure/mechanical ATS jobs."""
    all_jobs = []
    for comp in ENERGY_COMEET_COMPANIES:
        pos_list = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        for p in pos_list:
            text = f"{p['title']} {p['snippet']}".lower()
            if any(kw in text for kw in ENERGY_KEYWORDS):
                all_jobs.append(p)
    return all_jobs

def get_drone_ats_jobs():
    """Extract and filter dedicated drone/UAV/C-UAS ATS jobs."""
    all_jobs = []
    for comp in DRONE_COMEET_COMPANIES:
        pos_list = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        for p in pos_list:
            text = f"{p['title']} {p['snippet']}".lower()
            # Must match at least one drone keyword and no negative keywords
            if any(kw in text for kw in DRONE_ANCHOR_KEYWORDS):
                if not any(neg in text for neg in DRONE_NEGATIVE_KEYWORDS):
                    all_jobs.append(p)
    return all_jobs

if __name__ == "__main__":
    print("[+] Testing ATS Scraper...")
    energy_jobs = get_energy_ats_jobs()
    drone_jobs = get_drone_ats_jobs()
    print(f"[+] Found {len(energy_jobs)} Energy ATS jobs and {len(drone_jobs)} Pure Drone ATS jobs.")
