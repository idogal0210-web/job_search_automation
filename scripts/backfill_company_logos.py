#!/usr/bin/env python3
"""
Backfill verified official company logos into historical catalog and weekly archive datasets.
Strict Zero Synthetic Logos Policy:
- Official LinkedIn CDN logos (media.licdn.com)
- Official Drushim ATS logos (webapi.drushim.co.il)
- Official high-res domain favicons via Google gstatic / DuckDuckGo
- Official verified local assets (assets/logos/*)
- If unverified, company_logo_url is set to None (null) and company name is clean text.
Zero emojis in all code and outputs.
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Verified company domain mappings
KNOWN_DOMAINS = {
    "solaredge": "solaredge.com",
    "enlight": "enlightenergy.co.il",
    "energean": "energean.com",
    "elbit": "elbitsystems.com",
    "iai": "iai.co.il",
    "mer group": "mer-group.com",
    "mer": "mer-group.com",
    "siemens energy": "siemens-energy.com",
    "siemens": "siemens.com",
    "ge vernova": "gevernova.com",
    "opc": "opc-energy.com",
    "opc-energy": "opc-energy.com",
    "edf": "edf-re.co.il",
    "percepto": "percepto.co",
    "airobotics": "airoboticsdrones.com",
    "xtend": "xtend.me",
    "spearuav": "spearuav.com",
    "d-fend": "d-fendsolutions.com",
    "regulus": "regulus.com",
    "adama": "adama.com",
    "bet shemesh": "bsengines.co.il",
    "hitachi": "hitachienergy.com",
    "longi": "longi.com",
    "clou ess": "clouglobal.com",
    "ersg": "ersg-global.com",
    "amarel": "amarel.net",
    "nextpower": "nextpower.com",
    "repair carbon": "repair-carbon.com",
    "sightec": "sightec.com",
    "wds": "wdstech.co.il",
    "utron": "utron-sys.com",
    "edwards vacuum": "edwardsvacuum.com",
    "bird aero": "birdaero.com",
    "allpha": "allpha-innovation.com",
    "pacaya": "pacaya.co.il",
    "team 3": "team3.co.il",
    "esp710": "esp710.com",
    "aitan": "aitan.com",
    "growings": "growings-robotx.com",
    "hct": "hct.co.il",
    "tehiru": "tehiru.com",
    "magnus": "magnusmetal.com",
    "ein-hashofet": "ehltg.com",
    "utila": "utila.io",
    "rhino": "rhinofc.com",
    "rina": "rina.org",
    "supercom": "supercom.com",
    "elmor": "elmor.co.il",
    "ageera": "ageera.co.il",
    "dty": "dty.co.il",
    "sle": "sle.co.il",
    "yael": "yaelgroup.com",
    "korentec": "yaelgroup.com",
    "sun pharma": "sunpharma.com",
    "intel": "intel.com",
    "apple": "apple.com",
    "amazon": "amazon.com",
    "nvidia": "nvidia.com",
    "tesla": "tesla.com",
    "mobileye": "mobileye.com",
    "checkpoint": "checkpoint.com",
    "palo alto": "paloaltonetworks.com",
    "cyberark": "cyberark.com",
    "wix": "wix.com",
    "monday": "monday.com",
    "fiverr": "fiverr.com",
    "microsoft": "microsoft.com",
    "nestle": "nestle.com",
    "strauss": "strauss-group.com",
    "tnuva": "tnuva.co.il",
    "loreal": "loreal.com",
    "hilti": "hilti.co.il",
    "knapp": "knapp.com",
    "ur tech": "urtechjobs.com",
    "segal": "segal.co.il",
    "arbex": "arbex.com",
    "carmit": "carmit-mrfix.com",
    "mr fix": "carmit-mrfix.com",
    "abra": "abra-it.com",
    "iff": "iff.com",
    "sungrow": "sungrowpower.com",
    "kyndryl": "kyndryl.com",
    "drivenets": "drivenets.com",
    "kela": "kela-tech.com",
    "exodigo": "exodigo.com",
    "forsight": "forsightrobotics.com",
    "mda space": "mda.space",
    "commit": "commit.tech",
    "comblack": "comblack.co.il",
    "nuvei": "nuvei.com",
    "mentee": "menteebot.com",
    "vishay": "vishay.com",
    "sofar": "sofarsolar.com",
    "fieldcore": "fieldcore.com",
    "cellcom": "cellcom.co.il",
    "cocacola": "cocacola.co.il",
    "ortal": "ortal-hr.co.il",
    "ducart": "ducart.co.il",
    "kimberly-clark": "kimberly-clark.com",
    "helios": "project-helios.space",
    "elmo": "elmomc.com",
    "dataway": "dataway.co.il",
    "octally": "octally.com",
    "acs": "acsmotioncontrol.com",
    "alum": "alumenergy.co.il"
}

LOCAL_LOGOS = {
    "opc": "assets/logos/opc.svg",
    "enlight": "assets/logos/enlight.png",
    "energean": "assets/logos/energean.svg",
    "solaredge": "assets/logos/solaredge.svg",
    "elbit": "assets/logos/elbit.svg",
    "iai": "assets/logos/iai.svg",
    "arbex": "assets/logos/arbex.svg",
    "segal": "assets/logos/segal.svg",
    "ur tech": "assets/logos/urtech.svg",
    "dty": "assets/logos/dty.png",
    "sle": "assets/logos/sle.png",
    "sun pharma": "assets/logos/sunpharma.svg",
    "yael": "assets/logos/yael.png",
    "korentec": "assets/logos/yael.png",
    "mr fix": "assets/logos/mrfix.png",
    "מיסטר פיקס": "assets/logos/mrfix.png"
}


def find_domain_for_company(company_name: str):
    if not company_name:
        return None
    c = company_name.casefold().strip()
    for key, dom in KNOWN_DOMAINS.items():
        if key in c:
            return dom
    return None


def find_local_logo_for_company(company_name: str):
    if not company_name:
        return None
    c = company_name.casefold().strip()
    for key, path in LOCAL_LOGOS.items():
        if key in c:
            return path
    return None


def resolve_logo(job: dict, sibling_logos: dict):
    # 1. Existing verified logo
    existing = job.get("company_logo_url") or job.get("logo")
    if existing and isinstance(existing, str):
        existing = existing.strip()
        if existing.startswith("assets/logos/") or "media.licdn.com" in existing or "drushim.co.il" in existing or "gstatic.com/faviconV2" in existing or "duckduckgo.com/ip3" in existing:
            return existing

    company = job.get("company", "") or ""

    # 2. Check local assets
    local_path = find_local_logo_for_company(company)
    if local_path:
        return local_path

    # 3. Check sibling logos
    comp_norm = re.sub(r"[^\w\s]", "", company.casefold()).strip()
    if comp_norm in sibling_logos:
        return sibling_logos[comp_norm]

    # 4. Check known domain
    domain = find_domain_for_company(company)
    if domain:
        return f"https://t2.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{domain}&size=128"

    return None


def backfill_all():
    catalog_path = ROOT / "data" / "historical_catalog.json"
    archive_path = ROOT / "data" / "weekly_archive.json"

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    with open(archive_path, "r", encoding="utf-8") as f:
        archive = json.load(f)

    # Build sibling logos map from high confidence logos
    sibling_logos = {}
    for j in catalog.values():
        comp = j.get("company", "") or ""
        norm = re.sub(r"[^\w\s]", "", comp.casefold()).strip()
        logo = j.get("company_logo_url") or j.get("logo")
        if norm and logo and ("media.licdn.com" in str(logo) or "drushim.co.il" in str(logo) or str(logo).startswith("assets/logos/")):
            sibling_logos[norm] = logo

    # Backfill catalog
    updated_catalog_count = 0
    for link, job in catalog.items():
        resolved = resolve_logo(job, sibling_logos)
        if resolved != job.get("company_logo_url"):
            job["company_logo_url"] = resolved
            job["logo"] = resolved
            updated_catalog_count += 1
        else:
            job["company_logo_url"] = resolved
            job["logo"] = resolved

    # Backfill archive
    updated_archive_count = 0
    for job in archive:
        resolved = resolve_logo(job, sibling_logos)
        if resolved != job.get("company_logo_url"):
            job["company_logo_url"] = resolved
            job["logo"] = resolved
            updated_archive_count += 1
        else:
            job["company_logo_url"] = resolved
            job["logo"] = resolved

    # Save data/
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

    print(f"[BACKFILL] Updated {updated_catalog_count} catalog jobs and {updated_archive_count} archive jobs.")
    total_with_logo = len([j for j in catalog.values() if j.get("company_logo_url")])
    print(f"[STATUS] Historical catalog: {total_with_logo}/{len(catalog)} jobs now have verified official logos.")


if __name__ == "__main__":
    backfill_all()
