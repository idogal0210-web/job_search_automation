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
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=10)
        res.raise_for_status()
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
        return {"status": "success", "jobs": jobs}
    except Exception as e:
        print(f"[ERROR] Comeet scraper failed for {company_name}: {e}")
        return {"status": "failed", "jobs": [], "error": str(e)}

def get_energy_ats_jobs():
    """Extract and filter energy/infrastructure/mechanical ATS jobs."""
    all_jobs = []
    failures = 0
    successes = 0
    for comp in ENERGY_COMEET_COMPANIES:
        res = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        if res["status"] == "success":
            successes += 1
            for p in res["jobs"]:
                text = f"{p['title']} {p['snippet']}".lower()
                if any(kw in text for kw in ENERGY_KEYWORDS):
                    all_jobs.append(p)
        else:
            failures += 1
    return {"jobs": all_jobs, "successes": successes, "failures": failures, "attempted": len(ENERGY_COMEET_COMPANIES)}

def get_drone_ats_jobs():
    """Extract and filter dedicated drone/UAV/C-UAS ATS jobs."""
    all_jobs = []
    failures = 0
    successes = 0
    for comp in DRONE_COMEET_COMPANIES:
        res = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        if res["status"] == "success":
            successes += 1
            for p in res["jobs"]:
                text = f"{p['title']} {p['snippet']}".lower()
                if any(kw in text for kw in DRONE_ANCHOR_KEYWORDS):
                    if not any(neg in text for neg in DRONE_NEGATIVE_KEYWORDS):
                        all_jobs.append(p)
        else:
            failures += 1
    return {"jobs": all_jobs, "successes": successes, "failures": failures, "attempted": len(DRONE_COMEET_COMPANIES)}

def scrape_all_comeet_jobs():
    """Combined helper for all ATS Comeet jobs."""
    e_res = get_energy_ats_jobs()
    d_res = get_drone_ats_jobs()
    return {
        "jobs": e_res["jobs"] + d_res["jobs"],
        "successes": e_res["successes"] + d_res["successes"],
        "failures": e_res["failures"] + d_res["failures"],
        "attempted": e_res["attempted"] + d_res["attempted"]
    }

if __name__ == "__main__":
    print("[+] Testing ATS Scraper...")
    res = scrape_all_comeet_jobs()
    print(f"[+] Found {len(res['jobs'])} total Comeet ATS jobs. Successes: {res['successes']}, Failures: {res['failures']}")
