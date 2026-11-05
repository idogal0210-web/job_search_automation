# 11. בדיקות

## 11.1 מסגרת הבדיקות ורשימת קובצי הבדיקה
- **מסגרת הבדיקות:** Python `unittest` (שימוש ב-`unittest.TestCase`).
- **סך הכל קובצי בדיקה:** 25 קבצים.

| קובץ בדיקה | מספר שורות |
| :--- | :--- |
| `tests/test_audit_regressions.py` | 232 |
| `tests/test_audit_state.py` | 22 |
| `tests/test_benchmark_metrics.py` | 34 |
| `tests/test_career_studio_spec.py` | 1180 |
| `tests/test_comeet_connector.py` | 87 |
| `tests/test_curated_tags.py` | 152 |
| `tests/test_cv_tailor.py` | 64 |
| `tests/test_evidence_assessments.py` | 57 |
| `tests/test_m1_challenger_stress.py` | 131 |
| `tests/test_m2_ats_spec.py` | 269 |
| `tests/test_m2_challenger_stress.py` | 307 |
| `tests/test_m3_challenger_stress.py` | 415 |
| `tests/test_m3_grammar_dict_challenger.py` | 518 |
| `tests/test_m3_writer_spec.py` | 438 |
| `tests/test_m456_studio_spec.py` | 190 |
| `tests/test_main_integration.py` | 75 |
| `tests/test_modular_es_spec.py` | 92 |
| `tests/test_phase_b_precision.py` | 96 |
| `tests/test_policy_expansion.py` | 101 |
| `tests/test_recovery.py` | 284 |
| `tests/test_reliability_phase_a.py` | 73 |
| `tests/test_requeue.py` | 24 |
| `tests/test_salary_intelligence.py` | 80 |
| `tests/test_state_and_counters_consistency.py` | 152 |
| `tests/test_template_docs_sync.py` | 34 |


## 11.2 ביצוע והרצת הבדיקות
- **פקודת ההרצה:** `python3 -m unittest discover tests/ -v`
- **בטיחות הריצה:** הבדיקות אינן מבצעות קריאות LLM חיות (כל קריאות המודלים ממוקקות או מבוססות על נתוני דמה), אינן מבצעות גישה לרשת החיצונית (תעבורת רשת מדומה באמצעות Mocks וקובצי fixtures), ואינן כותבות לסביבת הייצור (משתמשות בתיקיות זמניות או Mocks).
- **תוצאת הרצת הבדיקות בפועל:**
  - **מספר בדיקות שהורצו:** 305 בדיקות.
  - **משך זמן הריצה:** כ-10.6 שניות.
  - **תוצאה סופית:** `OK` (305 עברו בהצלחה, 0 נכשלו, 0 שגיאות).


# 12. אינדיקטורים טכניים, מבוססי סריקה

## 12.1 פונקציות ארוכות מ-50 שורות (סריקת AST)
אותרו 29 פונקציות בפרויקט באורך העולה על 50 שורות:

| שם פונקציה | נתיב קובץ ושורות | מספר שורות |
| :--- | :--- | :--- |
| `build_unified_html_email` | `src/publishers.py:52-277` | 226 |
| `main` | `main.py:20-216` | 197 |
| `create_html_wrapper` | `tools/cv_tailor/src/utils.py:89-281` | 193 |
| `main` | `tools/cv_tailor/tailor.py:129-284` | 156 |
| `extract_salary_from_ad` | `src/salary_engine.py:156-306` | 151 |
| `update_weekly_archive` | `src/ui_builder.py:203-343` | 141 |
| `extract_curated_tags` | `src/job_policy.py:215-343` | 129 |
| `generate_tailored_package` | `tools/cv_tailor/src/generator.py:94-216` | 123 |
| `build_and_save_docs_app` | `src/ui_builder.py:89-200` | 112 |
| `evaluate_job_salary` | `src/salary_engine.py:353-461` | 109 |
| `fetch_drushim_jobs` | `src/fetchers.py:200-306` | 107 |
| `evaluate_and_enrich_job_with_gemini` | `src/evaluators.py:172-269` | 98 |
| `fetch_linkedin_jobs` | `src/fetchers.py:76-166` | 91 |
| `fetch_comeet_jobs` | `src/fetchers.py:331-417` | 87 |
| `analyze_job_match` | `tools/cv_tailor/src/analyzer.py:71-149` | 79 |
| `scan_project` | `scripts/project_hygiene.py:92-159` | 68 |
| `test_stress_07_rapid_mode_switching_120_inputs` | `tests/test_m3_challenger_stress.py:253-319` | 67 |
| `simulate_auto_fit_a4` | `tests/test_career_studio_spec.py:41-107` | 67 |
| `run_jsc_script` | `tests/test_m2_challenger_stress.py:46-111` | 66 |
| `run_scanner` | `scripts/scan_inactive_jobs.py:147-212` | 66 |
| `run_clean` | `scripts/project_hygiene.py:161-224` | 64 |
| `check_job_url` | `scripts/scan_inactive_jobs.py:73-127` | 55 |
| `evaluate_candidates` | `src/pipeline.py:31-85` | 55 |
| `test_m2_challenger_01_extreme_inputs` | `tests/test_m2_challenger_stress.py:115-167` | 53 |
| `backfill_all` | `scripts/backfill_company_logos.py:197-249` | 53 |
| `main` | `scripts/validate_zero_emoji.py:224-276` | 53 |
| `test_challenge_perfect_bullets_score_above_90` | `tests/test_m3_grammar_dict_challenger.py:165-215` | 51 |
| `test_challenge_phosphor_icons_conformance_with_web_v2_1_1` | `tests/test_m3_grammar_dict_challenger.py:445-495` | 51 |
| `run_js` | `tests/js_runner.py:59-109` | 51 |


## 12.2 קוד כפול או דומה בין קבצים
1. **שכפול מלא (1:1) בין frontend ל-docs:**
   - `frontend/css/dashboard.css` ו-`docs/dashboard.css` (זהים לחלוטין, 6,245 שורות כל אחד).
   - `frontend/js/dashboard.js` ו-`docs/dashboard.js` (זהים לחלוטין, 6,828 שורות כל אחד).
   - מודולי ה-JS ב-`frontend/js/modules/` ו-`docs/js/modules/` (`atsEngine.js`, `geoMap.js`, `render.js`, `store.js`, `export.js`) זהים ב-100%.
2. **סימטריית תבנית ופלט HTML:**
   - `frontend/templates/index.html` (תבנית עם placeholders כגון `__TITLE__`, `__NOW_STR__`) ו-`docs/index.html` (דף ה-HTML המרונדר עם נתונים מוזרקים) חולקים כ-98% מהמבנה וה-DOM.
3. **לולאות ניסיון חוזר של קריאות LLM:**
   - `tools/cv_tailor/src/analyzer.py` (שורות 92–107) ו-`tools/cv_tailor/src/generator.py` (שורות 124–143) מיישמים לולאת fallback זהה על רשימת מודלים `["gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]`.
4. **לוגיקת חילוץ שכר ברגקס ב-`src/job_policy.py`:**
   - הפונקציות `advertised_high_salary` (שורות 89–110), `advertised_very_high_salary` (שורות 112–133) ו-`advertised_low_salary` (שורות 135–156) חולקות לוגיקת פירוק מחרוזות וביטויי רגקס כמעט זהים, פרט לספי המספרים (18k, 20k, 15k).

## 12.3 ערכים קשיחים בקוד (Hardcoded Values)
- **כתובות URL קשיחות:**
  - `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search` (`src/fetchers.py:92`)
  - `https://www.drushim.co.il/jobs/search/` (`src/fetchers.py:223`)
  - `https://www.comeet.com/jobs/enlightenergy/99.006` (`main.py:135`, `src/fetchers.py:350`)
  - `https://idogal0210-web.github.io/job_search_automation/` (`main.py:185`)
  - `https://www.google.com/s2/favicons?domain=` (`scripts/backfill_company_logos.py:64`)
- **ספים וקבועים מספריים:**
  - רצפת שכר מינימלית לפסילת משרה: `15,000` ש"ח לחודש (`src/job_policy.py:153`).
  - סף שכר גבוה לבקרת חדר בקרה: `18,000` ש"ח לחודש (`src/job_policy.py:107`).
  - סף שכר למשרות 24/7: `20,000` ש"ח לחודש (`src/job_policy.py:130`).
  - הגבלת כמות משרות יומיות בדוא"ל: `5` משרות מובילות (`main.py:182`).
  - זמני Timeout: 10 שניות לבקשות HTTP (`src/fetchers.py:98`), 20 שניות ל-Gemini API (`src/gemini_runtime.py:137`).
- **שמות מודלים קשיחים:**
  - ברירת מחדל ב-`src/gemini_runtime.py:108`: `"gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.5-flash"`.
  - רשימה קשיחה ב-`tools/cv_tailor/src/analyzer.py:89` ו-`tools/cv_tailor/src/generator.py:124`: `["gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]`.

## 12.4 תלויות מעגליות בין מודולים
- **תוצאת בדיקה מבוססת AST:** לא קיימות תלויות מעגליות בין המודולים בתיקיית `src/` (גרף הייבוא הפנימי הינו Directed Acyclic Graph נקי ותקין).

## 12.5 קבצים שאינם מיובאים או מופעלים משום מקום
1. `scripts/backfill_company_logos.py` - סקריפט תחזוקה עצמאי לשליפת סמלי חברות, אינו נקרא מ-`main.py` או מ-CI.
2. `scripts/scan_inactive_jobs.py` - סקריפט תחזוקה עצמאי לאיתור משרות שאינן פעילות יותר.
3. `scripts/update_job_gaps_and_reasoning.py` - סקריפט חד-פעמי לעדכון שדות פערי התאמה ונימוקים.
4. `tools/cloudflare-worker/job-check.js` - סקריפט JavaScript עצמאי המיועד לפריסה ב-Cloudflare Workers.

## 12.6 טיפול בשגיאות
- **קריאות רשת (`src/fetchers.py`):** מנגנון `_get_with_retries` עם 3 ניסיונות והשהיה מעריכית על שגיאות HTTP זמניות (429, 500, 502, 503, 504) וטיפול ב-`Retry-After`. שגיאות פר-מקור אינן מפילות את כל הריצה אלא נרשמות במוני `RunHealth` (`linkedin_failures`, `drushim_failures`, `comeet_failures`).
- **קריאות AI ומודלים (`src/gemini_runtime.py`):** פונקציית `classify_error` מסווגת שגיאות מול ה-API (`daily_quota`, `rate_limit`, `authentication`, `configuration`, `timeout`, `unavailable`, `invalid_response`). מנגנון Circuit Breaker (`ModelState.open_until`) מבודד מודל שנכשל ומעביר את הבקשה למודל הבא. במקרה שכל המודלים נכשלים, נזרקת `EvaluationUnavailable`.
- **נפילה למצב חירום (Fallback) ב-`src/pipeline.py`:** כאשר קריאת Gemini נכשלת או אינה זמינה, המערכת אינה קורסת אלא מפעילה את `apply_keyword_fallback`, המבצעת הערכה על בסיס מילות מפתח ומסמנת את המשרה בסטטוס `RETRY_PENDING` להרצה הבאה.
- **שמירת נתונים (`src/state_manager.py`):** שמירה אטומית באמצעות קובץ זמני, `fsync` ו-`os.replace`, בתוספת עותק גיבוי `.bak`.
- **רמת תהליך ה-CI (`.github/workflows/daily_job_search.yml`):** שלב הסריקה מוגדר עם `continue-on-error: true`, ואחריו שלב ייעודי השומר את קובצי המצב והבדיקות ב-Git גם במקרה של כישלון הריצה, ומשגר התראת דוא"ל דחופה.

## 12.7 הערות TODO, FIXME ו-HACK בקוד
נמצאו 2 מופעים בלבד בכל מאגר הפרויקט:
1. `scripts/evaluate_dataset.py:106`: `"expected_label": "TODO: relevant / irrelevant / borderline",`
2. `docs/archive/ANTIGRAVITY_UPGRADE_PLAN.md:38`: `5. צור docs/UPGRADE_STATUS.md עם שבע משימות ומצבים: TODO, IN_PROGRESS, DONE, BLOCKED...`


# 13. שאלות להשלמה על ידי הבעלים

סעיף זה מרכז פערים, דרישות עתידיות ושאלות אסטרטגיות שלא ניתן להסיק מקריאת הקוד בלבד. התשובות הושארו ריקות למילוי ע"י בעל הפרויקט:

1. **הבעיה המרכזית כיום:**
   - מהו הכשל, צוואר הבקבוק או האתגר המרכזי במערכת הקיימת שהוביל לצורך ב-Refactoring (למשל: עלויות/זמני קריאות LLM, יציבות הגריפה מול חסימות, מורכבות התחזוקה של ה-Frontend, או איכות תוצאות הסינון)?
   - תשובת הבעלים: 

2. **תוכניות הרחבה למקורות גיוס נוספים:**
   - האם מתוכננת הרחבה למקורות נוספים בישראל או בעולם (כגון AllJobs, Glassdoor, משרד העבודה, דפי Greenhouse/Workday של מעסיקים ספציפיים)?
   - תשובת הבעלים: 

3. **ארכיטקטורת ממשק המשתמש (Frontend):**
   - קובצי ה-Frontend הנוכחיים הינם קובצי ענק מונוליתיים (`dashboard.js` בן 6,828 שורות ו-`dashboard.css` בן 6,245 שורות). האם יש כוונה לפצלם לרכיבים מודולריים, או להגר למסגרת מודרנית (כגון React, Vue, Svelte, Vite)?
   - תשובת הבעלים: 

4. **שכבת מסד הנתונים והאחסון:**
   - כיום כל המצב והנתונים נשמרים בקובצי JSON בתוך מאגר ה-Git. האם קיימת כוונה להגר למסד נתונים עצמאי (כגון SQLite מקומי, PostgreSQL, Supabase או Cloudflare D1)?
   - תשובת הבעלים: 

5. **תשתית ההרצה והתזמון:**
   - כיום הריצה מבוססת על GitHub Actions cron פעם ביום. האם יש צורך בסריקות תכופות יותר, הרצה כשרת Web API עצמאי (FastAPI / Flask) או מעבר לשירות ענן (GCP Cloud Run / AWS Lambda)?
   - תשובת הבעלים: 

6. **שילוב כלי ה-CV Tailor:**
   - האם כלי התאמת קורות החיים (`tools/cv_tailor`) מיועד להשתלב באופן אוטומטי מלא בתוך זרימת העבודה היומית (כך שלכל משרה מובחרת יופקו קו"ח מותאמים מראש), או להישאר כלי CLI אינטראקטיבי לפי דרישה?
   - תשובת הבעלים: 

7. **מדיניות ומכסות תקציב עבור LLM:**
   - האם הפרויקט מחויב להישאר במסגרת ה-Free Tier של Google AI Studio (עם מגבלות RPM/RPD), או שניתן להסתמך על חשבון ענן בתשלום (Pay-as-you-go)?
   - תשובת הבעלים: 
