---
name: save-and-sync
description: Protocol executed whenever the user says "שמור ועדכן", "שמור וסנכרן", "סנכרן ונקה", or "Save and update". Validates project integrity, enforces zero-waste lean directory hygiene via scripts/project_hygiene.py, runs test suite, checks secret leaks, verifies zero emojis, persists files, commits and pushes to GitHub, and provides a structured executive summary in RTL.
---

# Save & Sync Protocol ("שמור ועדכן")

Execute this comprehensive 5-step procedure whenever the user issues the trigger phrase **"שמור ועדכן"**, **"שמור וסנכרן"**, **"סנכרן ונקה"**, or **"Save and update"**:

## שלב 1 - בדיקת תקינות ושלמות (Code & Integrity Validation)
1. **הידור ובדיקת תחביר מלאה:** הרץ בדיקת קומפילציה ותחביר באמצעות `python3 scripts/project_hygiene.py --validate`.
2. **אימות קובצי נתונים ותצורה:** אימות תקינות של כל קובצי ה-JSON, הסכמות והקונפיגורציות בפרויקט.
3. **בדיקות יחידה אוטומטיות:** הרץ את מערך הטסטים המלא (`python3 -m unittest discover -s tests -p "test_*.py"`).
4. **בדיקת שלמות:** ודא אפס שגיאות תחביר, אפס כשלים בבדיקות, אפס ייבואים שבורים ואפס תלויות חסרות לפני המעבר לשלבים הבאים.

## שלב 2 - טיהור דטרמיניסטי של קבצים מיותרים (Project Hygiene & Zero-Waste)
אכוף את מדיניות הניקוי המוגדרת בקובץ `.save-and-sync.yml` באמצעות הסקריפט הייעודי:
1. **הפעלת ניקוי:** הרץ `python3 scripts/project_hygiene.py --clean`.
2. **פריטים המנוקים אוטומטית (שכבה 2 ושכבה 3):**
   - קובצי מטמון וזבל מערכת: `__pycache__/`, `*.pyc`, `*.pyo`, `.DS_Store`, `Thumbs.db`.
   - קובצי גיבוי וטיוטות זמניות: `*.bak`, `*.tmp`, `*.temp`.
   - קובצי לוג ישנים מ-7 ימים תחת `logs/`.
3. **סייג בטיחות מוחלט (שכבה 1 - מוגנים לתמיד):**
   - לעולם אין למחוק קובצי ליבה פעילים (`main.py`, `src/**`), קובצי נתונים וארכיון (`data/**`), דשבורד (`docs/**`), קובצי תצורה (`.env`, `requirements*.txt`, `.gitignore`), קובצי תיעוד (`README.md`, `PROJECT_CONTEXT.md`), סקריפטים (`scripts/**`) או תהליכי CI/CD (`.github/workflows/`).

## שלב 3 - שמירה ובדיקת אבטחה (Local Persistence & Security Check)
1. **שמירה בדיסק:** ודא שכל הקבצים שנערכו או נוצרו נשמרו מקומית בדיסק.
2. **סריקת סודות ואפס אימוג'ים:** הרץ `python3 scripts/project_hygiene.py --check-secrets` לוודא אפס דליפת מפתחות ואמת אפס אימוג'ים בקבצים החדשים ובסיכומי מנהלים.
3. **עדכון מסמכי הליבה:** בעת שינוי ארכיטקטוני או שינוי תלויות, ודא סנכרון של `PROJECT_CONTEXT.md`, `README.md`, `requirements.txt` ו-`requirements-lock.txt`.
4. **אימות .gitignore:** ודא שקובץ `.gitignore` קיים ומתעלם כראוי מ-`.env`, `.recovery/`, ספריות וירטואליות (`venv/`), ומטמונים.

## שלב 4 - סנכרון ודחיפה ל-GitHub (GitHub Synchronization)
> **כלל מנחה:** כאשר המשתמש אומר "גיט", הכוונה היא תמיד ל-**GitHub**, ויש להתייחס לפלטפורמה ולכתוב תמיד **GitHub**.
- בדיקת סטטוס: `git status --porcelain`.
- בדיקת סנכרון מול ה-Remote: `git fetch origin main`.
- צירוף השינויים המאושרים בלבד: `git add <paths>`.
- יצירת הודעת Commit סמנטית (ללא אימוג'ים): `feat(...)`, `fix(...)`, `chore(...)`, `refactor(...)`.
- דחיפה ל-GitHub: `git push origin main`.
- אימות עץ עבודה נקי (`working tree clean`) ותאימות מול ה-Remote.

## שלב 5 - דוח סיכום תמציתי בעברית (RTL Executive Summary)
הפק דוח סיכום מובנה ומקצועי ביישור מלא לימין (RTL) ללא אימוג'ים כלל:
- פעולה שבוצעה: [שמירה / סנכרון / סנכרון ונקה]
- בדיקת תקינות: תקין (הידור קוד, אימות נתונים, כל בדיקות היחידה עברו)
- טיהור קבצים מיותרים (Zero Waste): פירוט מדויק של כמות הפריטים שנוקו ושטח הדיסק שפונה
- סריקת אבטחה: אפס סודות, אפס אימוג'ים
- קבצים שנשמרו מקומית: פירוט הקבצים שעודכנו
- סנכרון GitHub: סטטוס דחיפה, Hash והודעת ה-Commit
- שורה תחתונה: הפרויקט רזה, נקי, מאובטח, שמור ומסונכרן במלואו מול GitHub
