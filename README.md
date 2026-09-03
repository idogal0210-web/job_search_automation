# 🎯 Job Search Automation System – Ido Gal (עידו גל)

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-green.svg)
![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Live_Web_App-brightgreen.svg)
![Gemini AI](https://img.shields.io/badge/Gemini_AI-2.5--Flash-orange.svg)

מערכת אוטומציה מתקדמת ואוטונומית לסריקה, סינון, ניתוח אינטליגנטי (Gemini AI) והפצת דוחות משרות מותאמים אישית עבור **עידו גל** (הנדסאי מכונות – אנרגיה, גז טבעי ו-SCADA | בקר גז 24/7 | יוצא סיירת נח"ל).

---

## 🌐 ממשק אינטראקטיבי חי (Live Web App)

האפליקציה האינטראקטיבית פרוסה בלייב ב-GitHub Pages:  
👉 **[https://idogal0210-web.github.io/job_search_automation/](https://idogal0210-web.github.io/job_search_automation/)**

---

## 🚀 תכונות מרכזיות במערכת (Key Features)

### 1. ☀️ דוח יומי מאוחד (Unified Daily Email)
* **תזמון:** בכל יום בשעה **10:28 בבוקר** (שעון ישראל / 07:28 UTC).
* **הרכב 10 המשרות המותאמות:**
  * ⚡ **5 משרות אנרגיה, גז טבעי ו-SCADA**
  * 🚁 **5 משרות רחפנים, כטב"ם, C-UAS ומטע"דים**
* **עיצוב בערכת נושא כהה (Dark Mode List):**
  * 🏢 **חברה ומיקום:** `שם החברה – מאיזה תחום החברה ומה המוצר שלה | מיקום`
  * 📋 **תקציר המשרה:** תיאור תפקיד מפורט והקשר חברה.
  * 💪 **נקודות חוזק מהניסיון שלך:** התאמה ספציפית לקורות החיים (בקר גז/SCADA, הנדסאי מכונות, סיירת נח"ל).
  * 🔍 **דגשים / דרישות נוספות:** דרישות ספציפיות, מודל עבודה ומדד פתיחות ללא ניסיון בתחום.

### 2. 📅 דוח סיכום שבועי ביום שבת (Saturday Digest)
* **תזמון:** בכל יום שבת בשעה **10:13 בבוקר** (שעון ישראל / 07:13 UTC).
* **סינון מבוסס משרות שמורות (Saved Jobs Only):** מכיל **אך ורק משרות שסומנו ב-✔️ (Saved)**, תוך סינון מלא של משרות שהוסרו ב-✖️.

### 3. 🧠 תובנות AI עמוקות (Gemini AI Company Intelligence)
* 💡 **אודות החברה והרעיון:** ניתוח מוצר, טכנולוגיה ומעמד בשוק.
* 👥 **גודל חברה:** הערכת כמות עובדים.
* 🎓 **מדד פתיחות ללא ניסיון בתחום:** תגית ויזואלית (`🟢 גבוהה / 🟡 בינונית / 🔴 נמוכה`) + הסבר מפורט.
* 🏢 **מודל עבודה:** היברידי / שטח / משמרות 24/7.

### 4. 🚫 זיכרון החרמות וסינון cross-day (`Rejection Memory`)
* לחיצה על **✖️ (הסר משרה)** ב-Web App או במערכת שומרת את הקישור ב-`rejected_jobs.json`.
* משרה שהוסרה **לא תופיע שוב בשום יום עתידי ולא תיכלל בדוח השבועי של יום שבת**.

---

## 📁 ארכיטקטורת הקבצים והמבנה (File Architecture)

```text
job_search_automation/
├── .github/
│   └── workflows/
│       └── daily_job_search.yml      # הגדרת הליכי הריצה האוטומטיים ב-GitHub Actions
├── docs/
│   └── index.html                    # אפליקציית ה-Web App החיה ב-GitHub Pages
├── ats_scraper.py                    # סורק משרות ה-Comeet ATS לחברות אנרגיה ורחפנים
├── daily_job_search_unified.py       # מנוע הניתוח וההפצה היומי המאוחד
├── interactive_app_builder.py        # מחולל ה-HTML האינטראקטיבי ל-GitHub Pages
├── weekly_summary.py                 # מנוע הפקת הדוח השבועי של יום שבת
├── generate_weekly_pdf.py            # מחולל דוח PDF שבועי גיבוי
├── rejected_jobs.json                # זיכרון החרמות (משרות שסומנו ב-X)
├── seen_jobs.json                    # היסטוריית משרות אנרגיה שנראו
├── seen_drones.json                  # היסטוריית משרות רחפנים שנראו
├── weekly_archive.json               # ארכיון משרות שבועי
├── requirements.txt                  # תלויות פייתון
└── README.md                         # תיעוד הפרויקט
```

---

## ⚙️ הגדרת משתני סביבה (Environment Secrets)

להרצת האוטומציה ב-GitHub Actions נדרשים המפתחות הבאים ב-Repository Secrets:

| שם המפתח | תיאור |
| :--- | :--- |
| `SENDER_EMAIL` | כתובת הג'ימייל השולחת (`idogal0210@gmail.com`) |
| `SENDER_APP_PASSWORD` | סיסמת אפליקציה ייעודית מ-Google App Passwords |
| `GEMINI_API_KEY` | מפתח API של Google Gemini עבור AI Enrichment |
| `GITHUB_TOKEN` | מפתח הרשאות אוטומטי של GitHub Actions לסנכרון |

---

## 👤 פרופיל המועמד וסינון קשיח (Candidate Profile)

* **מועמד:** עידו גל (Ido Gal)
* **השכלה:** הנדסאי מכונות (התמחות בגז טבעי ואנרגיה ירוקה), המרכז האקדמי רופין. לימודי חשמלאי מוסמך.
* **תפקיד נוכחי:** בקר גז 24/7 (Gas Controller) – ניטור SCADA בזמן אמת, לחצים, ספיקות והקצאות נומינציה.
* **שירות צבאי:** לוחם ומשלח חבלה בסיירת נח"ל.
* **חברות מוחרגות (EXCLUDE):** אנרג'יאן (מעסיק נוכחי), נתג"ז (INGL), שברון ישראל (מודל 2-שבועות), Raycatch.
* **סינון B.Sc קשיח:** החרגת משרות המיועדות *אך ורק* למהנדסי B.Sc שבהן תואר הנדסאי *אינו* מתקבל.

---

© 2026 Job Search Automation System – Ido Gal.
