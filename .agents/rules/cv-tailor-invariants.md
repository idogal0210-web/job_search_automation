---
trigger: glob
description: "Invariants for tailored CV and cover letter generation: candidate realism, locked role titles, zero inflation, Hebrew default, opt-in cover letter, and clean naming."
globs: ".agents/skills/cv-tailor/**, tools/cv_tailor/**, docs/career/cv/**, frontend/data/cv/**, output/**"
---

# כללי ברזל להתאמת קורות חיים ומסמכי מועמדות (CV Tailoring Invariants)

## 1. נעילת שמות תפקידים מקוריים (Locked Role Titles)
- חובה לשמר במדויק את שמות התפקידים המקוריים מ-`base_profile.md`:
  * `בקר גז — תפעול ומוצר | Energean Israel Ltd.` / `ENERGEAN ISRAEL LTD. – Gas Controller – Operations and Product`
  * `אחראי משמרת אבטחה במתקן אנרגיה אסטרטגי | וולקן עוצמה בע״מ / Energean Israel Ltd.` / `ENERGEAN ISRAEL LTD. / VOLCAN OTZMA LTD. – Security Shift Supervisor – Strategic Energy Facility`
  * `ראש צוות ומדריך מכירות | חברות מכירות בפעילות בינלאומית` / `INTERNATIONAL BUSINESS OPERATIONS – Team Leader & Sales Instructor`
  * `מתקין מערכות סולאריות | MER Group` / `MER GROUP – Solar Systems Installer`
- אסור בתכלית האיסור לשנות שם תפקיד מן העבר כדי לחקות את דרישות משרת היעד.

## 2. אפס ניפוח נתונים והצמדות לאמת (Zero-Inflation & Realism)
- התאמת קורות חיים מתבצעת אך ורק באמצעות תיעדוף מחדש של הישגים אמיתיים והבלטת נקודות חוזק רלוונטיות (פרויקט גמר סולארי, תפעול 24/7, AVEVA System Platform, אנגלית שוטפת, SAP/Excel).
- אסור להציג ניסיון במכירות כמהנדס ביצוע / EPC.
- אסור להציג התקנת מערכות PV כניהול פרויקטים הנדסיים רחבי היקף.
- אם משרה דורשת מיומנות שאינה מופיעה ב-`base_profile.md`, אסור להמציא או לשער אותה. יש לגשר אך ורק באמצעות כישורים מוכחים קיימים או לשאול ישירות את המשתמש.

## 3. שפת יעד: עברית כברירת מחדל (Language Policy)
- ברירת המחדל להפקת מסמכים מותאמים היא עברית בלבד (`CV_<Company>_HE.html`, `CV_<Company>_HE.md`).
- אין לייצר גרסת אנגלית באופן אוטומטי. גרסה באנגלית (`CV_<Company>_EN.*`) תיווצר אך ורק כאשר המשתמש מבקש זאת במפורש.

## 4. מכתב מקדים לפי דרישה בלבד (Cover Letter Policy)
- אסור לייצר מכתב מקדים (Cover Letter) באופן אוטומטי.
- יש לשאול את המשתמש מראש: "האם ברצונך לייצר גם מכתב מקדים מותאם (בעברית / באנגלית)?".
- מכתב מקדים יופק אך ורק לאחר אישור מפורש מהמשתמש.

## 5. מתן שמות ואישור שמירה (File Naming & Save Policy)
- שמות קבצים נקיים וקריאים ללא חותמות זמן מסורבלות:
  * `CV_<Company>.html` / `CV_<Company>.md`
  * `CoverLetter_<Company>.html` / `CoverLetter_<Company>.md`
  * `Summary_<Company>.md`
- יש לבקש את אישור המשתמש בסיום התהליך לפני כתיבת או שמירת קבצים בתיקיית `output/`.
