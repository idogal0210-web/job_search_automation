---
name: git-cloud-sync-guardian
description: מנטר ומאמת סנכרון בין תיקיית העבודה המקומית למאגר GitHub, ומגדיר את כללי הברזל ל-GitOps בקובצי Workflow של GitHub Actions. משמש לבדיקת מצב סנכרון לפני עבודה ולכתיבה או בדיקה של קובצי `.github/workflows/`. לא מבצע commit, push, ניקוי או מחיקת קבצים - את אלה מבצע הסקיל save-and-sync בלבד.
---

# Git Cloud Sync Guardian

עקרון הליבה: **Zero Divergence, Zero Broken Pipelines**. סביבה מקומית שאינה מסונכרנת גורמת לדחיות push (`non-fast-forward`), לקונפליקטים שקטים ולעבודה על קוד ישן, במיוחד מול הריצה הלילית ב-GitHub Actions.

## גבול סמכות
- הסקיל הזה **קורא ומאמת בלבד** בצד המקומי. שמירה, commit, push וניקוי מתבצעים רק דרך `save-and-sync`, ורק בהוראה מפורשת.
- אסור: `git push --force`, `git reset --hard`, מחיקת `.git/index.lock`, `git stash` אוטומטי, `git add -A` מקומי, או `[skip ci]` ללא בקשה. נעילה שנתקעה מדווחים למשתמש ולא מוחקים.

## 1. בדיקת מצב סנכרון (לפני עבודה, קריאה בלבד)
```bash
BRANCH=$(git branch --show-current)
git fetch origin --prune
BEHIND=$(git rev-list --count HEAD..origin/$BRANCH)
AHEAD=$(git rev-list --count origin/$BRANCH..HEAD)
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
echo "Branch: $BRANCH | Behind: $BEHIND | Ahead: $AHEAD | Dirty: $DIRTY"
```

| מצב | פעולה |
| :--- | :--- |
| `BEHIND > 0` ו-`DIRTY == 0` | מותר `git pull --rebase origin $BRANCH` |
| `BEHIND > 0` ו-`DIRTY > 0` | לעצור ולדווח. אין `stash` אוטומטי ואין rebase על שינויים שלא נשמרו. לשאול את המשתמש איך לשמור אותם |
| `BEHIND > 0` ו-`AHEAD > 0` (התפצלות) | לדווח. לשלב רק לפי מדיניות הפרויקט ובאישור, לעולם לא `--force` |
| `HEAD` מנותק | להחזיר לענף הראשי לפני עבודה |

מצב של ריצת לילה ב-GitHub Actions שדחפה תוצאות הוא הסיבה העיקרית ל-`BEHIND > 0`. חובה למשוך אותו לפני עריכת קובצי נתונים ב-`data/` ובדשבורד.

## 2. הגנת `.gitignore`
לוודא שלעולם לא נדחפים: `venv/`, `__pycache__/`, `.pytest_cache/`, `.env`, `*.key`, `*.pem`, `token.json`, `*.log`, `tmp/`, `.recovery/`. הוספה ל-`.gitignore` אינה מסירה קבצים שכבר במעקב.

## 3. כללי ברזל ל-GitOps ב-GitHub Actions
חלים רק בעת כתיבה, עריכה או בדיקה של `.github/workflows/`:

1. **ב-Runner בלבד**, כשה-workflow מבצע commit של תוצרים, להשתמש במבנה:
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
   - `git add -A` ב-Runner מונע שגיאות `pathspec` על קבצים שנמחקו או שונו.
   - הבדיקה `git diff --staged --quiet` מונעת commit ריק.
   - ה-rebase מתבצע אחרי ה-commit המקומי, וה-pull שלפני ה-push מונע `non-fast-forward` בריצות מקבילות.
   - `[skip ci]` ו-`git add -A` מותרים כאן כי זה Runner אוטומטי ולא סביבת עבודה של המשתמש.
2. **ב-`run`** להימנע משרשראות כמו `cmd1 && cmd2 || cmd3`. להשתמש ב-`if / then / else / fi` מפורשים.
3. **ללא השגחה:** סקריפט לא קורס בשקט על שינוי מבנה זמני. לעטוף ב-`subprocess` שתופס `stderr` ומדווח (דפוסים נוספים ב-`resilient-automation-patterns`).

## 4. כשלים נפוצים

| שגיאה | פתרון |
| :--- | :--- |
| `Merge conflict in rebase` | לעצור, `git rebase --abort`, ליצור ענף גיבוי `git branch backup-$(date +%s)`, לפתור ממוקד |
| `Everything up-to-date` אך קבצים חסרים בענן | `git status --ignored` לבדיקה אם `.gitignore` חסם אותם |
| `Failed to connect to github.com` | Retry עם backoff: 2, 4 ו-8 שניות, לכל היותר 2 ניסיונות נוספים |
| `[rejected - non-fast-forward]` | זו התפצלות ולא תקלת רשת: fetch ובדיקה מחדש לפי סעיף 1 |
