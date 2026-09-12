---
name: git-cloud-sync-guardian
description: מנטר, מאמת ומבטיח סנכרון מלא ודו-כיווני בין תיקיית העבודה המקומית למאגר ה-Git בענן (GitHub/Cloud), ומונע כשלי ביצוע משימות, דחיית פושים (non-fast-forward), קונפליקטים ודליפות קבצים. כולל את כללי הברזל ל-GitOps ב-CI/CD.
---

# Git Cloud Sync Guardian & GitOps Authority 🛡️

סקיל זה נועד להבטיח **התאמה מוחלטת (1:1)** בין סביבת העבודה המקומית למאגר ה-Git בענן (GitHub / Remote), למנוע קונפליקטים, לחסום דחיות (Pushes Rejected), ולהבטיח שרידות מלאה של תהליכי GitOps אוטומטיים בריצות CI/CD (GitHub Actions) ובריצות מקומיות כאחד.

---

## 🧭 עקרון הליבה: Zero Divergence, Zero Broken Pipelines

סביבת עבודה מקומית שאינה מסונכרנת עם ה-Remote גורמת ל:
1. **דחיות Push** (`[rejected - non-fast-forward]`) עקב שינויים שבוצעו ב-GitHub Actions או במחשב אחר במקביל.
2. **דריסת קבצים וקונפליקטים שקטים** בקבצי נתונים או קוד.
3. **עבודה על קוד ישן**, מה שמוביל להפעלת לוגיקה לא מעודכנת באוטומציות.

---

## 📋 שלב 1: אימות טרום-ביצוע משימה (Pre-Execution Alignment)

לפני כל שינוי בקוד, הרצת סקריפט או ביצוע משימה, חובה לוודא שהסביבה המקומית מעודכנת מול ה-Remote:

### 1.1 פקודת סריקה ובדיקת מצב (Sync Health Check)
```bash
# 1. זיהוי הענף הנוכחי
BRANCH=$(git branch --show-current)

# 2. משיכת מטא-דאטה מהענן ללא השפעה על הקבצים
git fetch origin --prune

# 3. בדיקת פערים (Lag & Lead)
BEHIND=$(git rev-list --count HEAD..origin/$BRANCH)
AHEAD=$(git rev-list --count origin/$BRANCH..HEAD)
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')

echo "=== GIT SYNC STATUS ==="
echo "Branch: $BRANCH"
echo "Behind remote: $BEHIND commit(s)"
echo "Ahead of remote: $AHEAD commit(s)"
echo "Dirty files locally: $DIRTY"
```

### 1.2 כללי פעולה לפי מצב:
* **אם `BEHIND > 0` וסביבת העבודה נקייה (`DIRTY == 0`):**
  בצע משיכה ישירה ב-Rebase:
  ```bash
  git pull --rebase origin $BRANCH
  ```
* **אם `BEHIND > 0` ויש שינויים מקומיים לא שמורים (`DIRTY > 0`):**
  בצע שמירה זמנית, עדכון, והחזרה:
  ```bash
  git stash push -u -m "autostash-before-sync"
  git pull --rebase origin $BRANCH
  git stash pop
  ```
* **אם יש התפצלות (Divergence: גם Ahead וגם Behind):**
  אל תבצע Push כוחני (`--force`) לעולם! בצע `git pull --rebase origin $BRANCH`.

---

## 🔒 שלב 2: הגנות בזמן ביצוע המשימה (In-Execution Guardrails)

בזמן הרצת תהליכים (איסוף דאטה, ריצות טסטים או עדכון סקריפטים):

1. **הגנת נעילת אינדקס (`.git/index.lock`):**
   אם תהליך קודם קרס, קובץ הנעילה עלול למנוע פקודות Git עתידיות. 
   אם קיים קובץ נעילה ישן, יש להסירו בבטחה:
   ```bash
   if [ -f .git/index.lock ]; then
     echo "Removing stale git index.lock..."
     rm -f .git/index.lock
   fi
   ```

2. **בקרת `.gitignore` נוקשה:**
   ודא שלעולם לא נדחפים קבצים זמניים, סביבות ריצה או קבצי סודות:
   * תיקיות `venv/`, `__pycache__/`, `.pytest_cache/`
   * קובצי סביבה: `.env`, `*.key`, `*.pem`, `token.json`
   * קובצי ריצה זמניים: `*.log`, `tmp/`, `.system_generated/`

---

## 🤖 שלב 3: חוקי ברזל ל-GitOps באוטומציות CI/CD (GitHub Actions)

בעת כתיבה, עריכה או בדיקה של קובצי Workflow ב-`.github/workflows/`:

### 3.1 הפרוטוקול המוזהב של סנכרון ב-CI/CD Runner
לעולם אל תריץ `git pull --rebase` לפני Commit ב-Runner אם ייתכן שנוצרו קבצים חדשים (זה ייכשל). 
יש להשתמש תמיד במבנה המגננתי הבא:
```bash
git add -A
if ! git diff --staged --quiet; then
  git commit -m "chore: automated update [skip ci]"
  git pull --rebase origin main
  git push origin main
else
  echo "No changes to commit or push."
fi
```
**יתרונות:**
* `git add -A` מונע שגיאות `pathspec` פטליות אם קבצים נמחקו או שונו שמותיהם.
* הבדיקה `if ! git diff --staged --quiet` מונעת שגיאת Exit 1 על Commit ריק.
* ביצוע ה-Rebase *לאחר* ה-Commit המקומי מונע קונפליקטים מול קבצים מקומיים, וה-Pull שלפני ה-Push מונע שגיאות `non-fast-forward` אם רץ תהליך במקביל.

### 3.2 לוגיקת Bash מפורשת ב-YAML
הימנע משרשראות שבירות של שורה אחת כמו `cmd1 && cmd2 || cmd3` בבלוקי `run`. כישלון בבדיקה שקטה עלול להפעיל בטעות את ה-fallback. השתמש תמיד במבני `if / then / else / fi` מפורשים.

### 3.3 תבנית המרפא האוטונומי (AI Auto-Healer Pattern)
באוטומציות סריקת דאטה ללא השגחה, אין לתת לסקריפט לקרוס בשקט על שינוי מבנה זמני. יש להשתמש בעטיפת `subprocess` שתופסת חריגות `stderr` ומאפשרת תיקון והרצה חוזרת באותה ריצה.

---

## 🚀 שלב 4: הפרוטוקול המקומי לשמירה וסנכרון לענן (Post-Execution Atomic Push)

בסיום ביצוע משימה מקומית, יש לדחוף את השינויים לענן בצורה אטומית:

```bash
BRANCH=$(git branch --show-current)

# 1. הוספת כל השינויים (כולל מחיקות)
git add -A

# 2. בדיקה האם יש מה לקמט
if ! git diff --staged --quiet; then
  COMMIT_MSG="chore(sync): automated sync - update project assets [skip ci]"
  git commit -m "$COMMIT_MSG"
else
  echo "No changes staged. Working tree clean."
fi

# 3. סנכרון סופי מול שינויים שהתרחשו בענן
git fetch origin $BRANCH
if [ $(git rev-list --count HEAD..origin/$BRANCH) -gt 0 ]; then
  echo "Remote has new commits. Applying rebase..."
  git pull --rebase origin $BRANCH
fi

# 4. דחיפה לענן עם אימות הצלחה
git push origin $BRANCH

# 5. אימות התאמה מלאה (1:1)
LOCAL_REV=$(git rev-parse HEAD)
REMOTE_REV=$(git rev-parse origin/$BRANCH)

if [ "$LOCAL_REV" = "$REMOTE_REV" ] && [ -z "$(git status --porcelain)" ]; then
  echo "✅ SYNC SUCCESS: Local workspace and cloud are 100% matched!"
else
  echo "❌ SYNC WARNING: Mismatch detected between local ($LOCAL_REV) and cloud ($REMOTE_REV)!"
  exit 1
fi
```

---

## 🛠️ שלב 5: טיפול בכשלים והתאוששות (Disaster Recovery & Fallbacks)

| סוג שגיאה | גורם | פתרון מומלץ |
| :--- | :--- | :--- |
| `Merge conflict in rebase` | שינויים חופפים בענן ובמקומי באותו קובץ | עצור את ה-Rebase מיד: `git rebase --abort`. בדוק את הדיף, צור ענף גיבוי מקומי `git branch backup-$(date +%s)`, ולאחר מכן פתור את הקונפליקט ממוקד. |
| `Everything up-to-date but remote lacks files` | קבצים לא נכנסו עקב `.gitignore` או שלא בוצע `git add` | הרץ `git status --ignored` לבדיקה האם הקבצים הרצויים נחסמו ע"י ה-gitignore. |
| `Failed to connect to github.com` / Network Timeout | ניתוק רשת זמני של ה-Runner / סביבה | בצע מנגנון Retry עם Exponential Backoff (נסה שוב לאחר 2 שניות, 4 שניות, ו-8 שניות). |
| `Detached HEAD` | עבודה שלא על ענף ראשי | חזור לענף הראשי: `git checkout main` ואחד שינויים לפי הצורך. |
