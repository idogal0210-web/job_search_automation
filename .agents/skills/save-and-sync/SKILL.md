---
name: save-and-sync
description: |
  פרוטוקול העל המאוחד לשמירה, ניקוי, אבטחה וסנכרון ("שמור ועדכן", "שמור וסנכרן", "Save and sync").
  מבצע: 1. סריקת התיקייה המקומית, זיהוי ומחיקת קבצים מיותרים/מיושנים (Zero-Waste Hygiene).
  2. בדיקות איכות, תקינות קוד, תחביר והרצת בדיקות יחידה (Code & Data Integrity).
  3. סריקת אבטחה, מניעת דליפת סודות ואימות אפס אימוג'ים (Anti-Leak Secret Scanning & Zero-Emoji Guard).
  4. סנכרון מלא ודו-כיווני מול ה-Remote (GitOps Cloud Guardian - מניעת דחיות, קונפליקטים ו-non-fast-forward).
  5. דחיפה אטומית לענן והפקת סיכום מנהלים מעוצב ב-RTL ללא אימוג'ים.
---

# Save & Sync Master Protocol ("שמור ועדכן")

> **מטרת העל:** פרוטוקול שלם, דטרמיניסטי ועמיד המבטיח תיקיית עבודה נקייה, מסודרת ומאובטחת ב-100%, אפס דליפות סודות, אפס אימוג'ים, וסנכרון מושלם ודו-כיווני (1:1) מול מאגר ה-GitHub ללא דחיות או קונפליקטים.

מופעל אוטומטית בכל פעם שהמשתמש כותב: **"שמור ועדכן"**, **"שמור וסנכרן"**, או **"Save and sync"**.

---

## הגדרות תצורה (Configuration Overrides)
* `DRY_RUN=false` — הפעל כמצב הדמיה (סימולציה) ללא מחיקות או פקודות push בפועל.
* `RETRY_PUSH=3` — מספר ניסיונות דחיפה חוזרים עם Exponential Backoff במקרה של כשל רשת זמני.
* `AUTO_CLEAN=true` — הפעלה אוטומטית של טיהור קבצים מיותרים או מיושנים.

---

## שלב 1: סריקת התיקייה המקומית וטיהור קבצים מיותרים ומיושנים (Zero-Waste Hygiene)

חוק הברזל: **שום קובץ שאינו נחוץ, מיושן, כפול או בלתי מקושר לקוד הפעיל לא יישאר בתיקיית העבודה.**

### 1.1 סריקה ואיתור קבצים מיושנים ומיותרים:
הסוכן סורק את עץ הפרויקט ומזהה:
1. **קבצים ישנים וזמניים:** קובצי טיוטה, גיבויים ידניים וקבצים זמניים (`tmp_*`, `temp_*`, `sample_*`, `*.bak`, `*.old`, `test_output.*`).
2. **סקריפטים מיושנים:** גרסאות קוד קודמות שהוחלפו על ידי קובץ מרכזי חדש ואינן נקראות עוד.
3. **פסולת מערכת וקאש:** `.DS_Store`, ספריות `__pycache__/`, קובצי `*.pyc`, `.pytest_cache/`, וקובצי לוג ישנים (`*.log`).
4. **נעילות Git שבורות:** אם קיים קובץ `.git/index.lock` ישן שנתקע מתהליך קודם — להסירו בבטחה:
   ```bash
   if [ -f .git/index.lock ]; then rm -f .git/index.lock; fi
   ```

### 1.2 רשימת קבצים ונתיבים מוגנים (Protected Paths - אין למחוק לעולם!):
* קובצי הליבה הפעילים (`daily_job_search_unified.py`, `main.py`, וכל קובץ תחת `src/`).
* מסדי נתונים ומידע פעיל (`data/job_state.db`, `data/jobs.json`, וכל קובץ תחת `data/`).
* קונפיגורציה קריטית: `.env`, `requirements.txt`, `.gitignore`.
* תיעוד וממשק: `README.md`, `PROJECT_CONTEXT.md`, קבצים תחת `docs/` (`docs/index.html`).
* אוטומציות ענן: `.github/workflows/`.

### 1.3 ביצוע הניקוי:
מחיקה פיזית של כל הקבצים המיותרים שאותרו, והשארת מבנה תיקייה שטוח, נקי, קריא ורזה.

---

## שלב 2: בדיקת איכות ותקינות קוד ונתונים (Code & Integrity Check)

לפני ששומרים ומסנכרנים, מוודאים שהקוד תקין ואינו שבור:
1. **בדיקת תחביר וקומפילציה:**
   * בפייתון: `python3 -m py_compile **/*.py` לוודא אפס שגיאות תחביר.
2. **אימות קובצי נתונים:** בדיקת שלמות קובצי הגדרות ונתונים (`json.load`, `yaml.safe_load`).
3. **בדיקות יחידה אוטומטיות:** הרצת כל בדיקות היחידה (`python3 -m unittest discover -s tests -p "test_*.py"`).
4. **אימות מסמכי הליבה:** בעת שינויי ארכיטקטורה, תלויות או UI, אימות שמסמכי הליבה מעודכנים (`PROJECT_CONTEXT.md`, `README.md`, `requirements.txt`, `requirements-lock.txt`).
5. **עצירת חירום במקרה של שגיאה קריטית:** אם נמצאה שגיאת קוד קריטית שלא ניתן לתקן בבטחה, יש לעצור, לא לבצע Push, ולדווח במדויק למשתמש.

---

## שלב 3: היגיינת אבטחה, סריקת סודות ואפס אימוג'ים (Anti-Leak & Zero-Emoji Scanner)

**חוק ברזל: שום מפתח API, סיסמה או טוקן לא ייחשפו או יידחפו לענן לעולם, ולעולם אין להשתמש באימוג'ים.**

### 3.1 אימות קובץ `.gitignore`:
ודא שקובץ ה-`.gitignore` קיים ומכיל באופן הרמטי:
```gitignore
# Credentials & Secrets
.env
.env.*
*.pem
*.key
*token*
*secret*

# System & Cache
__pycache__/
*.pyc
venv/
.DS_Store
*.log
```

### 3.2 סריקה אוטומטית מקדימה של השינויים (Pre-Commit Secret Scan):
לפני ה-Commit, יש לסרוק את כל הקבצים שנוספו ל-Staging:
```bash
git diff --cached --name-only | xargs grep -nEi \
  '(ghp_|AIza[A-Za-z0-9_-]{35}|sk-[A-Za-z0-9]{32,}|AQ\.Ab|password\s*=|secret\s*=|token\s*=)' \
  2>/dev/null
```
* **במידה ונמצא סוד כלשהו:** STOP מיידי. לא מבצעים Commit. מסירים את המפתח מהקוד, מעבירים אותו ל-`.env` (או GitHub Secrets), ורק לאחר מכן ממשיכים.

### 3.3 סריקת אימות אפס-אימוג'ים (Zero-Emoji Validation):
ודא שהשינויים ב-Staging אינם מכילים תווי אימוג'י יוניקוד:
```bash
git diff --cached | grep -E '[^\x00-\x7F\u0590-\u05FF\u2000-\u206F\u2070-\u209F\u20A0-\u20CF\u2100-\u214F\u2150-\u218F\u2190-\u21FF\u2200-\u22FF\u2300-\u23FF]' || true
```

---

## שלב 4: סנכרון מלא ודו-כיווני מול ה-Remote (GitOps Cloud Guardian)

מניעת שגיאות `[rejected - non-fast-forward]`, מניעת קונפליקטים, וסנכרון אטומי מול GitHub:

```bash
BRANCH=$(git branch --show-current)
if [ -z "$BRANCH" ]; then
  echo "Error: Detached HEAD detected. Switch to a branch."
  exit 1
fi

# 1. הוספת כל השינויים (כולל מחיקות הקבצים המיותרים משלב 1)
git add -A

# 2. בדיקה האם יש שינויים לקמט
if ! git diff --staged --quiet; then
  git commit -m "chore(sync): automated save, clean & sync [skip ci]"
else
  echo "No changes staged. Working tree clean."
fi

# 3. בדיקת פערים מול ה-Remote וסנכרון מקדים (Pull Rebase)
git fetch origin --prune
BEHIND=$(git rev-list --count HEAD..origin/$BRANCH)

if [ "$BEHIND" -gt 0 ]; then
  echo "Remote is ahead by $BEHIND commit(s). Applying safe rebase..."
  git pull --rebase origin $BRANCH
fi

# 4. דחיפה אטומית לענן עם מנגנון Retry
PUSH_SUCCESS=false
for i in $(seq 1 3); do
  if git push origin $BRANCH; then
    PUSH_SUCCESS=true
    break
  else
    echo "Push attempt $i failed. Retrying in $((i * 2))s..."
    sleep $((i * 2))
  fi
done

if [ "$PUSH_SUCCESS" = false ]; then
  echo "Error: Git push failed after 3 attempts."
  exit 1
fi

# 5. אימות התאמה מוחלטת (1:1) בין המחשב לענן
LOCAL_REV=$(git rev-parse HEAD)
REMOTE_REV=$(git rev-parse origin/$BRANCH)
STATUS_OUTPUT=$(git status --porcelain)

if [ "$LOCAL_REV" = "$REMOTE_REV" ] && [ -z "$STATUS_OUTPUT" ]; then
  echo "SYNC VERIFIED: 100% match between local and cloud."
else
  echo "Warning: Divergence detected between local ($LOCAL_REV) and remote ($REMOTE_REV)!"
  exit 1
fi
```

### 4.1 טיפול בכשלים (Disaster Recovery):
* **אם נוצר קונפליקט ב-rebase:** עצור מיד `git rebase --abort`, דווח למשתמש והצע פתרון ממוקד ללא דריסת שינויים.
* **לעולם אין לבצע `--force` push** שעלול לדרוס היסטוריה בענן.

---

## שלב 5: סיכום מנהלים מעוצב (RTL Executive Summary)

בסיום ביצוע כל השלבים, מוצג למשתמש סיכום מנהלים קצר וברור ללא אימוג'ים:

```html
<div dir="rtl" style="text-align: right; font-family: system-ui, sans-serif;">
  <h3>סיכום שמירה, ניקוי וסנכרון ("שמור ועדכן")</h3>
  <ul>
    <li><strong>טיהור קבצים:</strong> התיקייה נסרקה, קבצים מיושנים ומיותרים נמחקו, המבנה נקי ומעודכן.</li>
    <li><strong>בדיקת איכות:</strong> תחביר, נתונים ובדיקות יחידה אומתו בהצלחה (0 שגיאות).</li>
    <li><strong>בדיקת אבטחה:</strong> אפס דליפות סודות / מפתחות; קובץ .gitignore מאומת; אפס אימוג'ים.</li>
    <li><strong>סנכרון GitHub:</strong> שינויים נדחפו בהצלחה, תאימות 1:1 מלאה מול הענן ללא קונפליקטים.</li>
    <li><strong>Commit Hash:</strong> <code>[HASH]</code> | ענף: <code>[BRANCH]</code></li>
  </ul>
  <p><strong>הפרויקט רזה, מאובטח, מעודכן ומסונכרן במלואו.</strong></p>
</div>
```
