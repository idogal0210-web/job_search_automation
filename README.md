# מערכת אוטומציה וסינון משרות | עידו גל
**Job Search Automation & Multi-Tier AI Evaluation**

מערכת אוטונומית לאיסוף יומי, סינון דטרמיניסטי, הערכת AI מבוססת מודלים מתקדמים, אומדן שכר ענפי והצגת דשבורד אינטראקטיבי עבור משרות בתחומי האנרגיה, הגז הטבעי, מערכות סולאריות (PV), אגירת אנרגיה (BESS), בקרה ו-SCADA, ורחפנים/כטב"ם (UAV/C-UAS).

---

## ארכיטקטורת המערכת והמודולים

המערכת בנויה בארכיטקטורה מודולרית נקייה ומאובטחת:

```
job_search_automation/
├── main.py                  # תהליך הריצה המרכזי והתזמור היומי (Orchestration)
├── src/
│   ├── fetchers.py          # סריקת משרות מפלטפורמות (LinkedIn, Comeet) עם מנגנון Backoff ו-Jitter
│   ├── evaluators.py        # סינון מקדים דטרמיניסטי והערכת התאמה ב-Gemini AI עם Fallback
│   ├── salary_engine.py     # מנוע שכר רב-שכבתי: חילוץ ממודעה + מטריצת סקרי שכר 2026
│   ├── publishers.py        # הפקת דוח דוא"ל מעוצב (RTL) ושליחה אוטומטית
│   ├── ui_builder.py        # מחולל דשבורד אינטראקטיבי ומאובטח (GitHub Pages Web App)
│   └── state_manager.py     # שמירת מצב אטומית עם גיבוי למניעת שחיתות נתונים
├── tests/
│   ├── test_salary_intelligence.py    # בדיקות יחידה למנוע השכר
│   ├── test_reliability_phase_a.py    # בדיקות אמינות סינון, פסילות ומנגנון Fallback
│   └── test_phase_b_precision.py      # בדיקות דיוק נתונים, שלילת משמרות וגבולות חברות יעד
├── data/                    # קובצי מצב והיסטוריית משרות (jobs_state, archive, catalog)
├── docs/                    # אפליקציית Web אינטראקטיבית ב-GitHub Pages (index.html)
└── .github/workflows/       # ריצה יומית מתוזמנת ב-GitHub Actions עם שער בדיקות
```

---

## דרישות מערכת והתקנה

### סביבת ריצה
- **גרסת Python נתמכת**: Python 3.11 ומעלה (מאומתת ומסונכרנת מול סביבת הענן ב-GitHub Actions).

### התקנת תלויות
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### הגדרת משתני סביבה (`.env`)
להרצה מקומית, צור קובץ `.env` בשורש הפרויקט:
```env
GEMINI_API_KEY="your-google-gemini-api-key"
SENDER_EMAIL="your-email@gmail.com"
SENDER_APP_PASSWORD="your-google-app-password"
```

---

## הרצה ובדיקות

### 1. הרצת חבילת בדיקות היחידה המלאה (Quality Gate)
כל שינוי קוד נבדק אוטומטית לפני ביצוע:
```bash
python3 -m unittest discover tests/
```

### 2. הפקת דשבורד מקומי (`docs/index.html`)
לבנייה ורענון של הדשבורד מתוך הארכיון הקיים:
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
2. **אי-שריפת משרות בתקלות רשת**: רק משרות שהוערכו בהצלחה נשמרות ב-`jobs_state.json`. תקלות רשת או קטיעת תהליך מותירות את המשרה פתוחה להערכה חוזרת בריצה הבאה.
3. **שמירת כל המשרות המתאימות**: כל המשרות שעוברות את סף ההתאמה נשמרות בדשבורד ובארכיון השבועי, בעוד שרק 5 המובילות נשלחות לתקציר הדוא"ל.
4. **אבטחת XSS ו-Script Injection**: כל השדות המוצגים בממשק עוברים ניקוי (`escapeHtml`), כתובות מאומתות (`sanitizeUrl`), וכל מבני ה-JSON המוטמעים מוגנים מפני שבירת תגיות `<script>`.
5. **מדיניות שמירה אטומית וניהול היסטוריה**: עדכוני נתונים נכתבים לקובץ זמני ומוחלפים אטומית (`os.replace`) עם גיבוי (`.bak`), לצד ארכוב מוגדר לניהול צמיחת הקטלוג ההיסטורי.
