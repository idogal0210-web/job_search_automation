---
name: save-and-sync
description: Protocol executed whenever the user says "שמור ועדכן", "שמור וסנכרן", or "Save and update". Validates project integrity, enforces zero-waste lean directory hygiene by purging obsolete legacy files and wrappers, persists files, commits and pushes to Git/GitHub, and provides a structured executive summary in RTL.
---

# Save & Sync Protocol ("שמור ועדכן")

Execute this comprehensive 5-step procedure whenever the user issues the trigger phrase **"שמור ועדכן"**, **"שמור וסנכרן"**, or **"Save and update"**:

## שלב 1 - בדיקת תקינות ושלמות (Code & Integrity Validation)
1. **הידור ובדיקת תחביר מלאה:** הרץ בדיקת קומפילציה ותחביר לכל קובצי הקוד הפעילים בפרויקט (למשל `python3 -m py_compile ...`).
2. **אימות קובצי נתונים ותצורה:** אמת תקינות של כל קובצי ה-JSON, הסכמות והקונפיגורציות בפרויקט (`json.load`).
3. **בדיקת שלמות:** ודא אפס שגיאות תחביר, אפס ייבואים שבורים (Broken Imports) ואפס תלויות חסרות לפני המעבר לשלבים הבאים.

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
2. **הרצת סקריפטי בנייה:** הרץ סקריפטי בנייה מקומיים במידה וקיימים בפרויקט (כגון יצירה מחדש של תוצרי HTML/Docs).
3. **אימות .gitignore:** ודא שקובץ `.gitignore` קיים ומתעלם כראוי מ-`.env`, ספריות וירטואליות (`venv/`), ומטמונים.

## 4. GitHub Synchronization (סנכרון ודחיפה ל-GitHub)
> **כלל מנחה:** כאשר המשתמש אומר "גיט", הכוונה היא תמיד ל-**GitHub**, ויש להתייחס לפלטפורמה ולכתוב תמיד **GitHub**.
- Check `git status --porcelain`.
- Stage all intended changes and removals: `git add -A`.
- Create a descriptive, semantic commit message (e.g., `feat: ...`, `fix: ...`, `chore: ...`).
- Push changes to GitHub: `git push origin <branch>` (use BypassSandbox if network required).
- Verify clean working tree (`working tree clean`).

## שלב 5 - דוח סיכום תמציתי בעברית (RTL Executive Summary)
הפק דוח סיכום מובנה ומקצועי ביישור מלא לימין (RTL) הכולל:
- 🧪 **בדיקת תקינות:** תקין (הידור ואימות נתונים)
- 🧹 **טיהור קבצים מיותרים (Zero Waste):** פירוט קבצי עבר/כפילויות/זבל שנמחקו
- 📁 **קבצים שנשמרו מקומית:** פירוט הקבצים שעודכנו
- 🚀 **סנכרון GitHub:** סטטוס דחיפה, Hash והודעת ה-Commit
- 🎯 **שורה תחתונה:** הפרויקט רזה, נקי, שמור ומסונכרן במלואו.
