# התאמת קו״ח & הכנה לראיון (CV Tailoring & Interview Prep Engine)

מערכת מודולרית ומדויקת להתאמת קורות החיים, המכתב המקדים וסימולציות הכנה לראיונות עבודה של **עידו גל** למשרות ספציפיות בענפי האנרגיה, הנדסת מכונות, בקרת תשתיות וגז טבעי.

המערכת פועלת תחת חוק ברזל של **אפס המצאות (Zero-Hallucination)** — כל התאמה מתבססת אך ורק על פרופיל האמת המוכח ב-[`base_profile.md`](base_profile.md) (או תבנית הבסיס).

---

## ארכיטקטורת המערכת

```text
tools/cv_tailor/
├── tailor.py                # כניסה ראשית — מנוע ההתאמה (CLI)
├── base_profile.md          # פרופיל בסיס — עידו גל (מקור אמת פרטי)
├── base_profile.template.md # תבנית בסיס ציבורית
├── README.md                # תיעוד מלא
└── src/
    ├── __init__.py
    ├── scraper.py            # גריפת משרות (Firecrawl API עם Fallback ל-BS4)
    ├── researcher.py         # מחקר חברה ותעשייה (Tavily API)
    ├── analyzer.py           # ניתוח דרישות + כרטיס ניקוד התאמה ATS (Gemini)
    ├── generator.py          # ייצור קו"ח מותאם, מכתב מקדים וטיפים לראיון
    ├── keywords.py           # מילון מונחי אנרגיה ומילות מפתח
    └── utils.py              # קונפיגורציה, קריאת פרופיל, עיצוב ופלט
```

---

## דרכי הרצה ושימוש (CLI)

### 1. לפי כתובת URL של מודעת דרושים (סורק, חוקר ומנתח):
```bash
python tools/cv_tailor/tailor.py --url "https://www.drushim.co.il/job/12345" --company "Energean" --title "מנהל תפעול"
```

### 2. לפי קובץ טקסט קיים עם תיאור המשרה (באנגלית או בעברית):
```bash
python tools/cv_tailor/tailor.py --file job_description.txt --lang en
```

### 3. הדבקה אינטראקטיבית ישירה של תיאור המשרה:
```bash
python tools/cv_tailor/tailor.py --paste
```

### 4. אשף שאלות אינטראקטיבי מלא:
```bash
python tools/cv_tailor/tailor.py
```

---

## פרמטרים ודגלים נתמכים

| דגל / פרמטר | תיאור | ברירת מחדל |
| :--- | :--- | :--- |
| `--url` | כתובת URL ישירה למודעת הדרושים ברשת | `None` |
| `--file` | נתיב לקובץ טקסט/מרקדאון המכיל את תיאור המשרה | `None` |
| `--paste` | מעבר למצב הדבקה מרובת שורות ישירות בטרמינל | `False` |
| `--text` | העברת טקסט המשרה כמחרוזת שורת פקודה | `None` |
| `--company` | שם החברה המגייסת (לדיוק המחקר והמכתב) | נגזר אוטומטית |
| `--title` | כותרת המשרה המבוקשת | נגזר אוטומטית |
| `--lang` | שפת היעד של קורות החיים (`he` לעברית, `en` לאנגלית) | `he` |
| `--no-research` | דילוג על שלב מחקר החברה (Tavily) | `False` |
| `--output-dir` | תיקיית היעד לשמירת תוצרי ה-Markdown וה-HTML | `tools/cv_tailor/output/` |

---

## שלבי הביצוע בכל ריצה

1. **קליטת המשרה (Scraping & Ingestion):** שליפת תוכן המודעה במלואו (דרך Firecrawl או BeautifulSoup).
2. **מחקר חברה (Deep Research):** שליפת מידע עסקי ותפעולי עדכני ב-Tavily אודות החברה והפרויקטים שלה.
3. **ניתוח ATS (Scorecard & Matching):** הפקת כרטיס ניקוד באחוזים, מיפוי מילות מפתח תואמות וזיהוי פערי מידע.
4. **ייצור מותאם אישית (Generation):** כתיבת נוסח קו"ח מלא, מכתב מקדים ממוקד ו-3 דגשים לשיחת סינון טלפונית.
5. **שמירה וייצוא (Export):** יצירת קבצי Markdown מעוצבים ודפי HTML תואמי הדפסה ויישור מלא (RTL/LTR) בתיקיית `output/`.

---

## הגדרת מפתחות סביבה (`.env`)

המערכת עושה שימוש בקובץ `.env` המשותף של המאגר הראשי:
```env
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_key_optional
FIRECRAWL_API_KEY=your_firecrawl_key_optional
```
