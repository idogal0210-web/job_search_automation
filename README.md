# מערכת אוטומציה וסינון משרות | עידו גל
**Job Search Automation & Multi-Tier AI Evaluation**

מערכת אוטונומית לאיסוף יומי, סינון דטרמיניסטי, הערכת AI מבוססת Google Gemini, אומדן שכר ענפי והצגת דשבורד אינטראקטיבי עבור משרות בתחומי האנרגיה, הגז הטבעי, מערכות סולאריות (PV), אגירת אנרגיה (BESS), בקרה ו-SCADA, ורחפנים/כטב"ם (UAV/C-UAS).

---

## ארכיטקטורת המערכת והמודולים

המערכת בנויה בארכיטקטורה מודולרית נקייה ומאובטחת:

```
job_search_automation/
├── main.py                         # תהליך הריצה המרכזי ונקודת הכניסה (CLI Entrypoint)
├── PROJECT_CONTEXT.md              # עוגן ההקשר הרשמי ומקור האמת של הפרויקט עבור מפתחים וסוכני AI
├── requirements.txt                # תלויות פייתון
├── .python-version                 # הגדרת גרסת פייתון (Python 3.14 / 3.9+)
├── .agents/                        # חוקי הפעלה ומיומנויות ייעודיות לסוכני AI
│   ├── rules/                      # חוקי מערכת (mcp-policy.md, hebrew-rtl.md, critical-thinking-quality.md)
│   └── skills/                     # מיומנויות עבודה (salary-intelligence, cloud-sync, health-audit וכו')
├── .github/
│   └── workflows/
│       └── daily_job_search.yml    # ריצת Cron יומית מתוזמנת ב-GitHub Actions (07:17 שעון ישראל)
├── src/
│   ├── pipeline.py                 # תזמור תהליך הריצה, שלבים ומעקב מדדי בריאות
│   ├── fetchers.py                 # סריקת משרות מפלטפורמות (LinkedIn, Drushim) עם Backoff ו-Jitter
│   ├── job_policy.py               # סינון מקדים דטרמיניסטי: חסימת תפקידים לא-טכניים ורשימת מעסיקים חסומים
│   ├── gemini_runtime.py           # ניהול בריכת מודלי Gemini (Fallback Pool) עם סכמות Pydantic מובנות
│   ├── evaluators.py               # הערכת התאמה (ציון 0-100), בונוס חברות יעד וחלופת מילות מפתח
│   ├── salary_engine.py            # מנוע שכר מבוסס ראיות: חילוץ ממודעה + כיול שכר השוואתי
│   ├── state_manager.py            # ניהול מצב אטומי, מניעת כפילויות ומעקב סטטוסים
│   ├── ui_builder.py               # מקור האמת הבלעדי לבניית דשבורד ה-Web (docs/index.html)
│   └── publishers.py               # הפקת דוח דוא"ל מעוצב (RTL) ושליחה אוטומטית למשרות נבחרות
├── docs/
│   ├── index.html                  # אפליקציית Web אינטראקטיבית ב-GitHub Pages
│   ├── theme.css                   # משתני עיצוב CSS, סגנונות גלובליים ורספונסיביות
│   ├── fonts.css                   # הגדרות פונטים מקומיים
│   └── assets/                     # פונטים ונכסים גרפיים סטטיים
├── data/
│   ├── jobs_state.json             # מעקב משרות פעילות ומזהי URL
│   ├── weekly_archive.json         # ארכיון שבועי מלא עם ציוני AI, נתוני שכר ומטא-דאטה
│   ├── historical_catalog.json     # קטלוג היסטורי למניעת כפילויות בין סבבים
│   └── evaluation_state.json       # מטמון הערכות ותור משרות הממתינות לבדיקה חוזרת
├── tests/                          # חבילת בדיקות אוטומטית מלאה (49 בדיקות עוברות)
│   ├── test_recovery.py            # בדיקות שחזור והתאוששות מכשלים
│   ├── test_salary_intelligence.py # בדיקות יחידה למנוע הערכת השכר
│   ├── test_requeue.py             # בדיקות מנגנון החזרה לתור של משרות
│   ├── test_main_integration.py    # בדיקות אינטגרציה של התהליך המרכזי
│   ├── test_phase_b_precision.py   # בדיקות דיוק הערכת AI וסכמת Pydantic
│   └── test_reliability_phase_a.py # בדיקות אמינות סריקה, סינון מקדים וחלופות
└── scripts/
    └── requeue_jobs.py             # סקריפט שירות להערכה חוזרת סלקטיבית של משרות מהארכיון
```

---

## דרישות מערכת והתקנה

### סביבת ריצה
- **גרסת Python נתמכת**: Python 3.9 ומעלה / Python 3.14 (מאומתת ומסונכרנת מול סביבת הענן ב-GitHub Actions).

### התקנת תלויות
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### הגדרת משתני סביבה (`.env`)
להרצה מקומית, צור קובץ `.env` בשורש הפרויקט והגדר את המשתנים הבאים:
- `GEMINI_API_KEY` - מפתח API פעיל עבור Google Gemini (חובה להערכת משרות).
- `GEMINI_MODELS` - רשימת מודלים מועדפת (ברירת מחדל: `gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.5-flash`).
- `SENDER_EMAIL` - כתובת חשבון Gmail ממנו נשלח דוח המשרות היומי.
- `SENDER_APP_PASSWORD` - סיסמת אפליקציה מחשבון Google עבור שרת ה-SMTP (או `SENDER_PASSWORD`).

---

## הרצה ובדיקות

### 1. הרצת חבילת בדיקות היחידה המלאה (Quality Gate)
כל שינוי קוד נבדק אוטומטית לפני ביצוע (49 בדיקות יחידה ואינטגרציה):
```bash
python3 -m unittest discover tests/
```

### 2. הפקת דשבורד מקומי (`docs/index.html`)
מקור האמת הבלעדי של הדשבורד הוא `src/ui_builder.py`. אין לערוך ישירות את `docs/index.html`. לבנייה ורענון של הדשבורד מתוך הארכיון הקיים:
```bash
python3 -c "
import json
from src.ui_builder import build_and_save_docs_app
with open('data/weekly_archive.json', 'r', encoding='utf-8') as f:
    archive = json.load(f)
build_and_save_docs_app(archive, set(), '.')
"
```

### 3. הרצה מלאה של תהליך האוטומציה
```bash
python3 main.py
```

---

## עקרונות אמינות והגנה על הנתונים (Production Standards)

1. **הפרדה בין פסילה עסקית לכשל טכני**: משרות שאינן רלוונטיות נפסלות באופן סופי (`DISQUALIFIED`) ואינן חוזרות דרך מנגנון ה-Keyword Fallback.
2. **אי-שריפת משרות בתקלות רשת**: רק משרות שהוערכו בהצלחה נשמרות ב-`jobs_state.json`. תקלות רשת או קטיעת תהליך מותירות את המשרה פתוחה להערכה חוזרת בריצה הבאה (`RETRY_PENDING`).
3. **שמירת כל המשרות המתאימות**: כל המשרות שעוברות את סף ההתאמה נשמרות בדשבורד ובארכיון השבועי, בעוד שרק 5 המובילות נשלחות לתקציר הדוא"ל היומי.
4. **דשבורד אינטראקטיבי מתקדם**:
   - 3 מצבי תצוגה: רשת כרטיסיות (Cubes), רשימה קומפקטית ומפת Leaflet עם אשכולות גאוגרפיים (Spiderfy MarkerCluster).
   - מערכת ניהול משרות צד-לקוח (Triage): סימון בכוכב, שמירה ופסילה עם שמירה ב-LocalStorage של הדפדפן.
   - רספונסיביות מלאה למובייל (נבדק על גבי iPhone 14 ו-iPhone SE) עם יעדי מגע של 44x44 פיקסלים לפי תקן WCAG AA.
5. **אבטחת XSS ו-Script Injection**: כל השדות המוצגים בממשק עוברים ניקוי (`escapeHtml`), כתובות מאומתות (`sanitizeUrl`), וכל מבני ה-JSON המוטמעים מוגנים מפני שבירת תגיות `<script>`.
6. **מדיניות שמירה אטומית**: עדכוני נתונים נכתבים לקובץ זמני ומוחלפים אטומית (`os.replace`) עם גיבוי (`.bak`), לצד ארכוב מוגדר לניהול צמיחת הקטלוג ההיסטורי.
7. **מדיניות אפס אימוג'ים (Zero Emojis Policy)**: שימוש בלעדי באייקונים וקטוריים (Phosphor Icons) ללא שימוש באימוג'ים בקוד, בדוחות, בדשבורד או בתיעוד.
8. **פרוטוקול שמירה וסנכרון (Save & Sync Master Protocol)**: תהליך סנכרון מאובטח דו-כיווני מול GitHub הכולל ניקוי קבצים זמניים (Zero-Waste), סריקת אבטחה לפני קומיט למניעת דליפת מפתחות, ואימות התאמה של 100% (1:1) מול הענן.
