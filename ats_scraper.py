import os
import requests
from bs4 import BeautifulSoup

# Known Israeli defense, UAV, robotics, energy, and green tech companies with Comeet / Greenhouse career feeds
COMEET_COMPANIES = [
    {"company": "Airobotics", "uid": "airobotics", "sector": "רחפנים, כטב\"ם ורובוטיקה"},
    {"company": "SpearUAV", "uid": "spearuav", "sector": "רחפנים, כטב\"ם ורובוטיקה"},
    {"company": "SMARTSHOOTER", "uid": "smartshooter", "sector": "מערכות ביטחוניות ואלקטרו-אופטיקה"},
    {"company": "XTEND", "uid": "xtend", "sector": "רחפנים וביטחון"},
    {"company": "HighLander", "uid": "highlander", "sector": "ניהול תנועת רחפנים ורובוטיקה"},
    {"company": "D-Fend Solutions", "uid": "d-fend", "sector": "הגנת C-UAS וסייבר"},
    {"company": "NextVision", "uid": "nextvision", "sector": "אלקטרו-אופטיקה לרחפנים"},
    {"company": "SolarEdge", "uid": "solaredge", "sector": "אנרגיה סולארית וחשמל"},
    {"company": "Enlight Energy", "uid": "enlight", "sector": "אנרגיה מתחדשת"},
    {"company": "Augury", "uid": "augury", "sector": "ניטור מכונות ו-IIoT"},
]

ENERGY_KEYWORDS = [
    "gas", "energy", "mechanical", "control", "scada", "operator", "electrician", 
    "technician", "מכונות", "הנדסאי", "גז", "אנרגיה", "חשמל", "בקרה", "מפעיל", "טכנאי", "שירות שטח", "field", "operation"
]

DRONE_KEYWORDS = [
    "drone", "uav", "uas", "robotics", "flight", "test", "operator", "technician", 
    "integration", "mechanical", "electrical", "רחפן", "כטבמ", "כטב\"ם", "ניסויים", "חבלה", "מטיס", "מרכיב", "אינטגרציה"
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
    for comp in COMEET_COMPANIES:
        pos_list = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        for p in pos_list:
            text = f"{p['title']} {p['snippet']}".lower()
            if any(kw in text for kw in ENERGY_KEYWORDS):
                all_jobs.append(p)
    return all_jobs

def get_drone_ats_jobs():
    """Extract and filter drone/defense/UAV ATS jobs."""
    all_jobs = []
    for comp in COMEET_COMPANIES:
        pos_list = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        for p in pos_list:
            text = f"{p['title']} {p['snippet']}".lower()
            if any(kw in text for kw in DRONE_KEYWORDS):
                all_jobs.append(p)
    return all_jobs

if __name__ == "__main__":
    print("[+] Testing ATS Scraper...")
    energy_jobs = get_energy_ats_jobs()
    drone_jobs = get_drone_ats_jobs()
    print(f"[+] Found {len(energy_jobs)} Energy ATS jobs and {len(drone_jobs)} Drone ATS jobs.")
