---
trigger: glob
description: "UI invariants, unified desktop architecture, mathematical symmetry, zero synthetic logos, and schematic pipeline guidelines for job_search_automation."
globs: "*.html, *.css, *.js, frontend/**, docs/**, src/ui_builder.py"
---

# כללי ברזל לעיצוב וסנכרון ממשק (UI Invariants & Symmetry Guard)

## 1. ארכיטקטורת דשבורד אחודה לדסקטופ (Unified Desktop Architecture)
- המערכת מבוססת על דשבורד אחד אחוד בתצורת דסקטופ (Desktop-First). במידה והדשבורד נפתח במכשיר נייד, הוא מוצג במבנה הדסקטופ האחוד ללא רכיבי ניווט נפרדים או מצבי מובייל ייעודיים.
- אסור ששינוי בסרגלי הניווט, בכותרות או בפריסות יגרור עיוות, שינוי עימוד או פגיעה בקוביות המשרות (Category Cubes: `cube_all`, `cube_starred`, `cube_saved`, `cube_rejected`).
- מבנה קוביות המשרות הוא קומפקטי ואנכי (`flex-direction: column`).

## 2. סימטריה ומרכוז סרגלי עבודה (Symmetrical Header Architecture)
- כפתורי ניווט מצב ראשיים (כגון ממתג המערכת: "לוח משרות" ו"סטודיו קריירה") חייבים להיות ממוקמים במרכז הגיאומטרי המדויק (50% מרוחב המסך) של סרגל הבקרה העליון בדסקטופ.
- יש להשתמש ב-CSS Grid בתצורת `1fr auto 1fr` (עמודה ימנית: מיתוג וכלי מערכת; עמודה מרכזית: כפתורי מצב ממורכזים; עמודה שמאלית: קוביות משרות).
- יש לשמור על שולי מרווח (Buffer) המונעים גלישה או חפיפה בין אזורי הצד לכפתורי המרכז.

## 3. סטודיו קריירה סכמתי (Schematic Step-by-Step Pipeline)
- בעמוד סטודיו קריירה, סרגל האפשרויות יוצג מימין (RTL) כסרגל צד אנכי (`studio-pipeline-sidebar`) דביק (`position: sticky`).
- שלבי העבודה המודולריים (שלבים 1 עד 4) יוצגו במבנה סכמתי עוקב (Pipeline), ללא עומס מידע וטקסט, עם גדלי גופן אחידים, אייקונים מובחנים ותגי מספור מעגליים (1 עד 4).
- בתוך כל שלב, הפעולות מסודרות בעמודה אנכית אחת של צעדים ממוספרים (`studio-step-head`) עם סרגל קפיצה מהירה בראש השלב (`studio-step-outline`).
- שמירה מלאה על נגישות ותאימות בדיקות: `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-controls`.

## 4. עצמאות וגמישות ניהול קו״ח (Decoupled CV Upload)
- הממשק יכלול אפשרות עצמאית להעלאת קובץ קו״ח (PDF, DOCX, TXT) ישירות מהדפדפן, עם חיווי סטטוס ברור ואפשרות איפוס מהיר לקורות החיים המובנים של עידו גל ("איפוס לקו״ח בסיס").
- נתוני הקובץ יישמרו מקומית (`localStorage`) וישולבו באופן מיידי במנוע התאמת ה-ATS ללא תלות בסקריפטים חיצוניים.

## 5. סנכרון הרמטי של מוני הלשוניות (Hermetic Tab Counters Symmetry)
- מוני המשרות בלשוניות (Tab Badges: חדשות, בכוכב, שמורות להגשה, הוסרו מהסבב) חייבים להסתמך על מקור אמת יחיד (Single Source of Truth).
- כל מוני הסיכום והקוביות (`summaryNewCount`, `summaryStarredCount`, `summarySavedCount`, `summaryRejectedCount`, `statNewCount`, `statStarredCount`, `statSavedCount`, `statRejectedCount`) חייבים להיות זהים לחלוטין ומסונכרנים בזמן אמת בכל פעולת משתמש (סימון בכוכב, שמירה, מחיקה, שחזור) ובכל סינון או חיפוש, דרך `updateUI` ו-`updateCubeCountsImmediately`.

## 6. מדיניות אפס לוגואים גנריים או מלאכותיים (Zero Synthetic Logos Policy)
- חל איסור מוחלט להמציא לוגו, לייצר גרפיקה מלאכותית, או להשתמש במונוגרמות אותיות גנריות (אווטאר אותיות).
- קישור לוגו (`company_logo_url`) חייב להיות אך ורק קישור ישיר מאומת מתוך עמוד החברה ב-LinkedIn, או Favicon רשמי ברזולוציה גבוהה מדומיין הבית של החברה, או נכס וקטורי רשמי מקומי (`docs/assets/logos/`).
- במידה ולא קיים לוגו רשמי מאומת, השדה `company_logo_url` יישאר ריק (`null`), ושם החברה יוצג בטיפוגרפיה נקייה.
- כל תגית תמונת לוגו בממשק תכלול מנגנון `onerror` תקני המסתיר את תגית התמונה בצורה חלקה במידה והלוגו נחסם או נכשל בטעינה (404/CORS), ללא עיוות מבנה הכרטיס.
