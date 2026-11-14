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

## 3. סטודיו קריירה 3.0 — ארכיטקטורת 3 כלים במסך מפוצל (`55/45` Split-Screen)
- בעמוד סטודיו קריירה (`#careerStudioWorkspace`), הניווט מתבצע דרך סרגל הקשר עליון אחוד (`.studio-context-bar`) הכולל בורר משרת יעד (`#atsJobSelector`), קליטת URL (`#atsJobUrlInput`), חיווי קו״ח פעיל (`#studioCurrentCvStatus`) וסרגל אופקי של **3 כלי ליבה בלבד** (`#studioTabAts`, `#studioTabWriter`, `#studioTabInterview`) עם `focusgroup="tablist nomemory" role="tablist"` וללא סרגל צד ימני או ניווט צעדים ממוספר כפול.
- מתחת לסרגל העליון, פריסת העבודה בדסקטופ היא **2 עמודות בלבד (`55fr / 45fr`)**: עמודת כלי הפעולה (`55%`) לצד עמודת תצוגת המסמך החיה והדביקה (`45%`, `#studioStickyPreviewCol` / `#studioLiveDocViewer`).
- שמירה מלאה על נגישות ותאימות בדיקות: `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-controls`, `hidden="until-found"`, ואירוע `beforematch`.

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
