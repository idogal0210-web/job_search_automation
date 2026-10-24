---
name: save-and-sync
description: Protocol executed whenever the user says "שמור ועדכן", "שמור וסנכרן", or "Save and update". Validates project integrity, enforces zero-waste lean directory hygiene by purging obsolete legacy files and wrappers, runs test suite, checks secret leaks, verifies zero emojis, persists files, commits and pushes to Git/GitHub, and provides a structured executive summary in RTL.
---

# Save & Sync Protocol ("שמור ועדכן")

Execute this comprehensive 5-step procedure whenever the user issues the trigger phrase **"שמור ועדכן"**, **"שמור וסנכרן"**, or **"Save and update"**:

## שלב 1 - בדיקת תקינות ושלמות (Code & Integrity Validation)
1. **הידור ובדיקת תחביר מלאה:** הרץ בדיקת קומפילציה ותחביר לכל קובצי הקוד הפעילים בפרויקט (`python3 -m py_compile ...`).
2. **אימות קובצי נתונים ותצורה:** אמת תקינות של כל קובצי ה-JSON, הסכמות והקונפיגורציות בפרויקט (`json.load`).
3. **בדיקות יחידה אוטומטיות:** הרץ את מערך הטסטים המלא (`python3 -m unittest discover -s tests -p "test_*.py"`).
4. **בדיקת שלמות:** ודא אפס שגיאות תחביר, אפס כשלים בבדיקות, אפס ייבואים שבורים ואפס תלויות חסרות לפני המעבר לשלבים הבאים.

## שלב 2 - טיהור מוחלט של קבצים מיותרים (Zero-Waste & Lean Directory Hygiene)
אכוף את חוק הברזל: **"לא יישאר בפרויקט אפילו קובץ אחד שאין בו שימוש פעיל או צורך ממשי"**.
בצע סריקה אקטיבית ומחיקה אוטומטית של:
- **סקריפטים ותיקיות עבר ישנות:** תיקיות כגון `legacy/` או סקריפטים שהוחלפו ואינם חלק מתהליך הייצור.
- **קובצי מעטפת כפולים (Root Forwarders / Wrappers):** קבצים כפולים בשורש הפרויקט כאשר המימוש כבר יושב בצורה מודולרית בתוך `src/`.
- **קבצים של אוטומציות או תכונות שבוטלו:** כל קובץ, סקריפט או תצורה של פיצ'ר שאינו פעיל עוד.
- **קובצי טיוטה, תצוגות זמניות ודאמפים:** קבצים כגון `sample_*.html`, `temp_*`, `test_*.html`, דאמפים של טסטים ותצוגות מקדימות חד-פעמיות.
- **סקריפטים חד-פעמיים:** סקריפטים זמניים שנוצרו לניפוי שגיאות או בדיקות (`tmp_*.py`, `scratch_*.py`, `test_*.py`).
- **קובצי מטמון וזבל מערכת:** מחיקה רקורסיבית של `__pycache__/`, `*.pyc`, `*.pyo`, `.DS_Store`, `Thumbs.db`, וקובצי לוג מקומיים (`*.log`).

> **סייג בטיחות (Safety Guard):**
> לעולם אין למחוק קובצי ליבה פעילים (כגון `main.py`), מודולים פעילים בתוך `src/`, מסדי נתונים וארכיונים פעילים בתוך `data/`, קובצי תצורה חיוניים (`.env`, `requirements.txt`, `.gitignore`), קובצי תיעוד רשמיים (`README.md`, `docs/`) או תהליכי CI/CD פעילים ב-`.github/workflows/`.

## שלב 3 - שמירה ובנייה מקומית (Local Persistence & Build)
1. **שמירה בדיסק:** ודא שכל הקבצים שנערכו או נוצרו נשמרו מקומית בדיסק.
2. **סריקת סודות ואפס אימוג'ים:** בצע סריקת pre-commit למניעת דליפת מפתחות ואמת אפס אימוג'ים בקבצים החדשים.
3. **עדכון מסמכי הליבה:** בעת שינוי ארכיטקטוני או שינוי תלויות, ודא סנכרון של `PROJECT_CONTEXT.md`, `README.md`, `requirements.txt` ו-`skills-lock.json`.
4. **אימות .gitignore:** ודא שקובץ `.gitignore` קיים ומתעלם כראוי מ-`.env`, ספריות וירטואליות (`venv/`), ומטמונים.

## שלב 4 - סנכרון ודחיפה ל-GitHub (GitHub Synchronization)
> **כלל מנחה:** כאשר המשתמש אומר "גיט", הכוונה היא תמיד ל-**GitHub**, ויש להתייחס לפלטפורמה ולכתוב תמיד **GitHub**.
- בדיקת סטטוס: `git status --porcelain`.
- צירוף כל השינויים והמחיקות: `git add -A`.
- יצירת הודעת Commit סמנטית (ללא אימוג'ים): `feat: ...`, `fix: ...`, `chore: ...`.
- דחיפה ל-GitHub: `git push origin <branch>`.
- אימות עץ עבודה נקי (`working tree clean`) ותאימות 1:1 מול ה-Remote.

## שלב 5 - דוח סיכום תמציתי בעברית (RTL Executive Summary)
הפק דוח סיכום מובנה ומקצועי ביישור מלא לימין (RTL) ללא אימוג'ים כלל:
- בדיקת תקינות: תקין (הידור קוד, אימות נתונים, כל בדיקות היחידה עברו)
- טיהור קבצים מיותרים (Zero Waste): פירוט קבצי עבר/כפילויות/זבל שנמחקו
- קבצים שנשמרו מקומית: פירוט הקבצים שעודכנו
- סנכרון GitHub: סטטוס דחיפה, Hash והודעת ה-Commit
- שורה תחתונה: הפרויקט רזה, נקי, מאובטח, שמור ומסונכרן במלואו
