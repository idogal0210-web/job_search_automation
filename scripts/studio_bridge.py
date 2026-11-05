#!/usr/bin/env python3
"""Local HTTP Bridge Server for Career Studio AI (Gemini + Pydantic validation + Local Fallback).

Exposes endpoints:
  - GET  /api/health
  - POST /api/interview/evaluate  ( also aliased to /api/evaluate-interview )
  - POST /api/ats/match           ( also aliased to /api/ats-match )
  - POST /api/writer/tailor
"""
import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

from google import genai
from src.gemini_runtime import (
    AtsSemanticMatch,
    CvTailoredBullet,
    EvaluationUnavailable,
    GeminiPool,
    StarInterviewEvaluation,
)

DEFAULT_PORT = int(os.getenv("STUDIO_BRIDGE_PORT", "8765"))
_POOL = GeminiPool(min_interval=0.5, max_attempts=2)


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def fallback_interview_evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    answer = str(payload.get("answer") or "").strip()
    question = str(payload.get("question") or "").strip()

    s_score, t_score, a_score, r_score = 22, 22, 23, 22
    s_desc = "הגדרת זירה ורקע תפעולי ברורים (משמרת/מתקן)."
    t_desc = "הצבת יעד ברור לבלימת הכשל והגנה על הצוות."
    a_desc = "שימוש נכון בסמכות מקצועית, מגופים ונוהל חירום."
    r_desc = "תוצאה חיובית עם שמירה על רציפות תפקודית ואפס נפגעים."
    strengths = ["שימוש במינוח מקצועי מעולם הגז והאנרגיה", "מיקוד בבטיחות ותגובה מהירה"]
    improvements = []

    if not any(k in answer for k in ("PRMS", "שטח", "משמרת", "מתקן", "לילה", "אסדה")):
        s_score = 16
        s_desc = "מומלץ לציין במפורש את זירת הפעולה (למשל: משמרת לילה במתקן PRMS או חדר בקרה)."
        improvements.append("הוסף פירוט ספציפי של זירת האירוע בתחילת התשובה (Situation).")
    if not any(k in answer for k in ("פינוי", "משימה", "יעד", "בלימת", "אבטחת", "מניעת")):
        t_score = 17
        t_desc = "כדאי להדגיש את המשימה הדחופה ביותר: הצלת חיי אדם ובלימת הדליפה."
        improvements.append("חדד את המטרה הקריטית שעמדה בפניך באותו רגע (Task).")
    if not any(k in answer for k in ("ESD", "SCADA", "סגרתי", "נוהל", "הפעלתי", "בידוד")):
        a_score = 16
        a_desc = "מומלץ לתאר פעולות הנדסיות קונקרטיות בגוף ראשון: הפעלת ESD, בידוד קווים ותקשורת SCADA."
        improvements.append("פרט את הפעולות ההנדסיות שביצעת בעצמך (Action).")
    if not any(k in answer for k in ("Zero LTI", "דקות", "0 תאונות", "ללא נפגעים", "100%", "רציפות")):
        r_score = 16
        r_desc = "מומלץ לחזק את התוצאה במדד כמותי: זמן תגובה בדקות ומדד בטיחות Zero LTI."
        improvements.append("סיים במדד כמותי ברור של הצלחה ובטיחות (Result).")

    if not improvements:
        improvements.append("התשובה בנויה היטב לפי מודל STAR וכוללת מדדים הנדסיים ברורים.")

    total = s_score + t_score + a_score + r_score
    model_obj = StarInterviewEvaluation(
        situation_score=s_score,
        task_score=t_score,
        action_score=a_score,
        result_score=r_score,
        total_score=total,
        situation_feedback=s_desc,
        task_feedback=t_desc,
        action_feedback=a_desc,
        result_feedback=r_desc,
        strengths=strengths,
        improvements=improvements,
        improved_answer=(
            "במהלך משמרת לילה כבקר גז עצמאי ב-Energean זיהיתי במערכת ה-SCADA נפילת לחץ חריגה בתחנת PRMS "
            "(Situation). המשימה המיידית הייתה בלימת הסיכון הבטיחותי לצוותי השטח ושמירה על רציפות אספקה (Task). "
            "הפעלתי נוהל חירום, ביצעתי סגירת מגוף ESD מרחוק, הוריתי על פינוי רדיוס בטיחות ותיאמתי מול נתג״ז ואסדת ההפקה (Action). "
            "האירוע נבלם תוך פחות מ-7 דקות עם 0 נפגעים (Zero LTI) וחזרה מבוקרת לתפקוד מלא (Result)."
        ),
        verdict_badge="הערכה מקומית (Fallback Mode)",
    )
    res = model_obj.model_dump()
    res["source"] = "fallback_local"
    return res


def fallback_writer_tailor(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_text = str(payload.get("raw_bullet") or "").strip()
    tone = str(payload.get("tone_mode") or "technical").strip()
    if tone not in ("technical", "operational", "strategic"):
        tone = "technical"

    templates = {
        "technical": (
            f"ניטרתי וניתחתי פרמטרים תפעוליים במערכות SCADA ומתקני PRMS ({raw_text or 'בקרת גז טבעי'}), "
            "תוך עמידה בתקני לחץ וספיקה ושיפור דיוק הבקרה ב-100% מהמשמרות."
        ),
        "operational": (
            f"הובלתי תפעול משמרות 24/7 עצמאיות במתקן אנרגיה אסטרטגי ({raw_text or 'בקרת גז וחירום'}), "
            "תוך אכיפת נהלי בטיחות קפדניים, מענה מיידי לתרחישי חירום ושמירה על 0 אירועי LTI."
        ),
        "strategic": (
            f"סנכרנתי תהליכי Nomination ורציפות אספקה מול אסדת הפקה ימית, נתג״ז ולקוחות קצה ({raw_text or 'ניהול אספקת גז'}), "
            "תוך ייעול העברת המשמרות באמצעות כלי אוטומציה ו-Copilot."
        ),
    }

    model_obj = CvTailoredBullet(
        transformed_bullet=templates[tone],
        tone_mode=tone,
        quality_score=92,
        has_active_verb=True,
        has_metric=True,
        has_scope=True,
        suggestions=[
            "שולב פועל הנדסי פעיל בזמן עבר בראש המשפט.",
            "הודגשה תשתית טכנולוגית ספציפית (SCADA / PRMS / Nomination).",
            "נוסף מדד כמותי של רציפות תפקודית ובטיחות (Zero LTI / 100%).",
        ],
    )
    res = model_obj.model_dump()
    res["source"] = "fallback_local"
    return res


def fallback_ats_match(payload: Dict[str, Any]) -> Dict[str, Any]:
    job_text = str(payload.get("job_text") or "").strip()
    lower = job_text.lower()

    matched = ["הנדסאי מכונות מוסמך (מכללת רופין)", "ניסיון בבקרת גז טבעי 24/7 ב-Energean Israel"]
    gaps = []
    tips = []
    score = 84

    if "b.sc" in lower or "תואר ראשון בהנדס" in job_text or "מהנדס מכונות" in job_text:
        if "הנדסאי" not in job_text:
            score = 52
            gaps.append("דרישת סף לתואר מהנדס B.Sc (עידו הוא הנדסאי מכונות מוסמך).")
            tips.append("הדגש ניסיון מעשי מוכח בחדר בקרה 24/7 ויכולת הובלה טכנית כתחליף מעשי.")

    if "scada" in lower or "סקאדה" in job_text or "aveva" in lower:
        matched.append("ניסיון ישיר במערכות SCADA ו-AVEVA System Platform")
    if "חשמלאי" in job_text:
        gaps.append("רישיון חשמלאי מוסמך נמצא כעת בלימודים (צפי סיום: דצמבר 2026).")
        tips.append("ציין בראש קורות החיים את לימודי החשמלאי המוסמך והרקע המעשי במערכות הספק.")

    if not tips:
        tips.append("התאם את תקציר קורות החיים כך שיכלול את מילות המפתח המרכזיות מדרישות המשרה.")

    model_obj = AtsSemanticMatch(
        semantic_score=score,
        summary="הערכה סמנטית מקומית מול פרופיל עידו גל (הנדסאי מכונות, בקר גז טבעי ותפעול מערכות אנרגיה).",
        matched_strengths=matched,
        critical_gaps=gaps,
        tailoring_tips=tips,
    )
    res = model_obj.model_dump()
    res["source"] = "fallback_local"
    return res


def handle_interview_evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_gemini_client()
    if client is None:
        return fallback_interview_evaluate(payload)

    question = str(payload.get("question") or "").strip()
    answer = str(payload.get("answer") or "").strip()
    job_context = str(payload.get("job_context") or "בקר גז טבעי / הנדסאי מכונות / תפעול מתקני אנרגיה").strip()

    prompt = f"""אתה מראיין טכני בכיר בתחומי האנרגיה, הגז הטבעי, SCADA והנדסת מכונות בישראל.
עליך להעריך את תשובת המועמד (עידו גל - הנדסאי מכונות מוסמך ובקר גז טבעי ב-Energean Israel) לפי מודל STAR.
שמור על אמינות מוחלטת (אפס המצאות של ניסיון שלא קיים) והחזר פלט בעברית נקייה ללא אימוג'ים כלל.

רקע תפקיד: {job_context}
שאלת הראיון: {question}
תשובת המועמד: {answer}

החזר JSON תואם לסכמה עם ציונים (0-25 לכל חלק ב-STAR, סה"כ 0-100), משוב קונקרטי לכל חלק, חוזקות, נקודות לשיפור והצעת ניסוח משופרת."""

    try:
        data = _POOL.generate_json(client, prompt, schema=StarInterviewEvaluation, temperature=0.2)
        data["source"] = "gemini_ai"
        return data
    except EvaluationUnavailable:
        return fallback_interview_evaluate(payload)
    except Exception:
        return fallback_interview_evaluate(payload)


def handle_writer_tailor(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_gemini_client()
    if client is None:
        return fallback_writer_tailor(payload)

    raw_bullet = str(payload.get("raw_bullet") or "").strip()
    tone_mode = str(payload.get("tone_mode") or "technical").strip()
    if tone_mode not in ("technical", "operational", "strategic"):
        tone_mode = "technical"

    prompt = f"""אתה מומחה כתיבת קורות חיים הנדסיים ותפעוליים עבור עידו גל (הנדסאי מכונות מוסמך, בקר גז טבעי 24/7 ב-Energean Israel, ניסיון ב-AVEVA System Platform, SCADA, Nomination, SAP, Excel, פיתוח סוכני Microsoft 365 Copilot, ובלימודי חשמלאי מוסמך).
שכתב את המשפט הבא לסגנון '{tone_mode}' לפי נוסחת ההישג התעשייתי: [פועל פעיל בזמן עבר] + [מערכת/תשתית ספציפית] + [מדד כמותי/בטיחות HSE/רציפות תפקודית].
חוק ברזל: אפס המצאות של עובדות שלא קיימות בפרופיל, ואפס אימוג'ים.

משפט מקורי: {raw_bullet}
סגנון מבוקש: {tone_mode}"""

    try:
        data = _POOL.generate_json(client, prompt, schema=CvTailoredBullet, temperature=0.2)
        data["source"] = "gemini_ai"
        return data
    except EvaluationUnavailable:
        return fallback_writer_tailor(payload)
    except Exception:
        return fallback_writer_tailor(payload)


def handle_ats_match(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_gemini_client()
    if client is None:
        return fallback_ats_match(payload)

    job_text = str(payload.get("job_text") or "").strip()
    cv_text = str(payload.get("cv_text") or "עידו גל - הנדסאי מכונות מוסמך, בקר גז טבעי 24/7 ב-Energean Israel, AVEVA System Platform, SCADA, Nomination, SAP, Copilot, לימודי חשמלאי מוסמך.").strip()

    prompt = f"""בצע ניתוח התאמה סמנטי (ATS Semantic Match) בין תיאור המשרה לבין קורות החיים של המועמד.
הקפד על עברית מקצועית ללא אימוג'ים כלל וללא המצאת עובדות.

תיאור המשרה:
{job_text}

פרופיל המועמד:
{cv_text}"""

    try:
        data = _POOL.generate_json(client, prompt, schema=AtsSemanticMatch, temperature=0.1)
        data["source"] = "gemini_ai"
        return data
    except EvaluationUnavailable:
        return fallback_ats_match(payload)
    except Exception:
        return fallback_ats_match(payload)


class StudioBridgeHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/health"):
            has_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
            self._send_json(200, {
                "status": "ok",
                "service": "career_studio_bridge",
                "gemini_configured": has_key,
                "models": list(_POOL.models),
            })
            return
        self._send_json(404, {"error": "Not found", "path": self.path})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            payload = json.loads(raw_body) if raw_body.strip() else {}
        except Exception as err:
            self._send_json(400, {"error": "Invalid JSON payload", "detail": str(err)})
            return

        path = self.path.split("?")[0].rstrip("/")
        if path in ("/api/interview/evaluate", "/api/evaluate-interview"):
            result = handle_interview_evaluate(payload)
            self._send_json(200, result)
        elif path in ("/api/writer/tailor", "/api/tailor-bullet"):
            result = handle_writer_tailor(payload)
            self._send_json(200, result)
        elif path in ("/api/ats/match", "/api/ats-match"):
            result = handle_ats_match(payload)
            self._send_json(200, result)
        else:
            self._send_json(404, {"error": "Unknown endpoint", "path": path})

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[STUDIO_BRIDGE] {fmt % args}\n")


def run_server(host: str = "127.0.0.1", port: int = DEFAULT_PORT):
    server = ThreadingHTTPServer((host, port), StudioBridgeHandler)
    print(f"[STUDIO_BRIDGE] Listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STUDIO_BRIDGE] Shutting down...", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Career Studio Local AI Bridge Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port (default: 8765)")
    args = parser.parse_args()
    run_server(args.host, args.port)
