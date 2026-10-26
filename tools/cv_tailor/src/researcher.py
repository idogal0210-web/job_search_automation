import os
import requests
from dataclasses import dataclass
from typing import Optional, List
try:
    from tools.cv_tailor.src.utils import print_info, print_warning, print_success
except ModuleNotFoundError:
    from src.utils import print_info, print_warning, print_success

@dataclass
class CompanyResearch:
    company_name: str
    summary: str
    recent_projects: List[str]
    culture_values: List[str]
    strategic_focus: str
    is_live_data: bool = False

def query_tavily(query: str, api_key: str, max_results: int = 4) -> Optional[List[dict]]:
    """Query Tavily Search API."""
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": max_results
        }
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            return data.get("results", [])
        return None
    except Exception as e:
        print_warning(f"Tavily search failed: {e}")
        return None

def research_company(company_name: str, job_context: str = "", tavily_key: str = None) -> CompanyResearch:
    """Perform targeted company research to enrich cover letter and interview readiness."""
    if not company_name or company_name.strip() in ["חברה לא צוינה", "Unknown", ""]:
        return CompanyResearch(
            company_name="חברה כללית בתעשייה",
            summary="לא צוין שם חברה ספציפי — ההתאמה תתבסס על ניתוח דרישות התפקיד והתעשייה.",
            recent_projects=[],
            culture_values=["מצוינות תפעולית", "בטיחות ורציפות אספקה", "עבודה בצוות"],
            strategic_focus="עמידה ביעדי תפעול ובטיחות קפדניים.",
            is_live_data=False
        )

    print_info(f"מבצע מחקר רקע עסקי ותפעולי על חברת: {company_name}...")
    
    if tavily_key:
        query = f"{company_name} Israel operations energy engineering projects"
        results = query_tavily(query, tavily_key)
        if results:
            print_success(f"נמצאו {len(results)} מקורות מידע עדכניים ב-Tavily עבור {company_name}.")
            snippets = [r.get("content", "") for r in results if r.get("content")]
            summary_text = " \n".join(snippets[:3])
            return CompanyResearch(
                company_name=company_name,
                summary=summary_text[:600],
                recent_projects=[r.get("title", "") for r in results[:3]],
                culture_values=["אמינות תפעולית", "חדשנות ובטיחות", "הובלת פרויקטים"],
                strategic_focus="הרחבת פעילות תפעולית ופרויקטים אסטרטגיים.",
                is_live_data=True
            )
        else:
            print_warning("לא התקבלו תוצאות מ-Tavily, משתמש בהקשר תעשייתי.")

    # Fallback contextual synthesis
    return CompanyResearch(
        company_name=company_name,
        summary=f"חברה מובילה בענף: {company_name}, הפועלת בסביבה עסקית ותפעולית מתקדמת.",
        recent_projects=["פרויקטי תפעול ותשתיות"],
        culture_values=["בטיחות ללא פשרות", "רציפות תפעולית", "איכות מקצועית"],
        strategic_focus="מצוינות בניהול מערכות ותשתיות קריטיות.",
        is_live_data=False
    )
