import json
import re
import os

def clean_sentence(s):
    s = s.strip()
    s = re.sub(r"[,;:\-]\s*$", "", s).strip()
    if not s.endswith("."):
        s += "."
    return s

def condense_reasoning(text, title="", company=""):
    text = (text or "").strip()
    if not text:
        return "התאמה טכנית גבוהה כהנדסאי מכונות בעל ניסיון בבקרה, מערכות אנרגיה ותפעול שטח."

    s = text
    s = re.sub(r"^(המשרה הינה|המשרה דורשת|התפקיד כולל|התפקיד עוסק ב|מדובר ב)\s+", "", s)

    sentences = [part.strip() for part in re.split(r"[.!?]\s+", s) if part.strip()]
    if not sentences:
        return clean_sentence(text)

    res = sentences[0]
    if len(res) < 70 and len(sentences) > 1:
        res = f"{res}. {sentences[1]}"

    res = res.strip()
    return clean_sentence(res)

def analyze_fit_gaps(job):
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    reqs = (job.get("company_requirements") or "").lower()
    summary = (job.get("job_summary") or "").lower()
    snippet = (job.get("snippet") or "").lower()
    combined = f"{title} {reqs} {summary} {snippet}"

    gaps = []

    # 1. Electrician License Requirement
    if any(k in combined for k in ["חשמלאי מוסמך", "רישיון חשמלאי", "רישיון חשמל", "חשמלאי/ת מוסמך"]):
        gaps.append("נדרש רישיון חשמלאי מוסמך בתוקף (המועמד בלימודים לקראת סיום ההסמכה)")
    elif "מתח גבוה" in combined:
        gaps.append("נדרש רישיון מתח גבוה (למועמד אין רישיון מתח גבוה)")

    # 2. B.Sc. / Academic Degree requirement
    if any(k in combined for k in ["b.sc", "bsc", "תואר ראשון בהנדסת מכונות", "תואר ראשון בהנדסת חשמל", "תואר ראשון בהנדסה"]):
        if not any(k in combined for k in ["הנדסאי/ת", "הנדסאי", "practical engineer", "או הנדסאי"]):
            gaps.append("דרישת סף לתואר B.Sc בהנדסה (המועמד הינו הנדסאי מכונות מוסמך)")

    # 3. Civil / Railway / Infrastructure specific
    if any(k in combined for k in ["הנדסה אזרחית", "הנדסאי בניין", "מהנדס בניין", "עבודות מול נת\"ע", "רכבת קלה", "תשתיות מסילה", "lrt"]):
        gaps.append("דרישת רקע ייעודי בהנדסה אזרחית ותשתיות מסילתיות (למועמד התמחות במערכות אלקטרו-מכניות ואנרגיה)")

    # 4. Aviation / A&P License
    if any(k in combined for k in ["aircraft mechanic", "מבנאי.ת מטוסים", "רישיון רת\"א", "a&p", "רישיון תעופתי"]):
        gaps.append("דרישת רישיון טכנאי תעופה מוסמך / מבנאי מורשה (למועמד רקע מכני כללי ללא רישוי תעופתי ייעודי)")

    # 5. Deep Software / Embedded / Senior PLC programming
    if any(k in combined for k in ["c++", "c#", "embedded", "תכנות בקרים מתקדם", "פיתוח אלגוריתמים"]):
        gaps.append("דרישה לפיתוח תוכנה או תכנות בקרים מעמיק (למועמד רקע בתפעול ובקרה ואוטומציה בסיסית בפייתון)")

    # 6. Senior / Multi-year Management
    if any(k in title for k in ["site operations manager", "team lead", "opex leader", "מנהל/ת פרויקטים"]):
        gaps.append("דרישת שנות ניסיון רבות בניהול בכיר בתעשייה (למועמד ניסיון פיקודי קרבי וניהול תפעולי מוקדם)")

    if not gaps:
        return "אין פערי סף מהותיים; המועמד עונה על דרישות התפקיד."
    elif len(gaps) == 1:
        return gaps[0] + "."
    else:
        return "; ".join(gaps) + "."

def main():
    paths = [
        "docs/data/jobs.json",
        "data/weekly_archive.json"
    ]

    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        is_dict_envelope = isinstance(data, dict) and "jobs" in data
        jobs_list = data["jobs"] if is_dict_envelope else data

        print(f"Updating {len(jobs_list)} jobs in {p}...")
        for j in jobs_list:
            j["fit_gaps"] = analyze_fit_gaps(j)
            j["reasoning"] = condense_reasoning(j.get("reasoning", ""), j.get("title", ""), j.get("company", ""))

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    cat_paths = [
        "data/historical_catalog.json",
        "docs/data/historical_catalog.json"
    ]
    for cp in cat_paths:
        if not os.path.exists(cp):
            continue
        with open(cp, "r", encoding="utf-8") as f:
            cat = json.load(f)
        print(f"Updating {len(cat)} catalog jobs in {cp}...")
        for link, j in cat.items():
            j["fit_gaps"] = analyze_fit_gaps(j)
            j["reasoning"] = condense_reasoning(j.get("reasoning", ""), j.get("title", ""), j.get("company", ""))
        with open(cp, "w", encoding="utf-8") as f:
            json.dump(cat, f, ensure_ascii=False, indent=2)

    print("All jobs updated successfully!")

if __name__ == "__main__":
    main()
