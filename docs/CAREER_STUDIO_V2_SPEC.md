# מפרט ארכיטקטורה ו-UX מאוחד — Career Studio v2 (`job_search_automation`)

מפרט זה מאחד את שדרוג הפריסה וה-UX (`Master Split-Screen`, מילון במגירה, אקורדיון שערי סף ופיצול מצבי ראיון) עם התשתית הקיימת של המערכת ([`scripts/studio_bridge.py`](scripts/studio_bridge.py), [`tools/cv_tailor/`](tools/cv_tailor/tailor.py), והמחסנית הוונילית [`frontend/`](frontend/templates/index.html) -> [`docs/`](docs/index.html)), תוך פתרון 5 התאמות קריטיות למניעת רגרסיות.

---

## 1. מטרה, היקף ו-Non-Goals

- **מטרה:** צמצום גלילה ועומס קוגניטיבי בתוך `careerStudioWorkspace` על ידי הצגת תצוגת קורות חיים חיה וקבועה (`Sticky Live CV Preview`) לצד כלי הפעולה בדסקטופ, פינוי מילון המונחים ופרטי ייצוא עמוקים למגירות/חלונות `<dialog>` נגישים, ומיקוד כל טאב במשימה אחת ברורה.
- **מגבלות ברזל (Constraints & Non-Goals):**
  1. **ללא פריימוורקים וללא Build Steps:** Vanilla HTML5, CSS3, ES6+ בלבד, בסנכרון 1:1 בין `frontend/` ל-`docs/` (`tests/test_template_docs_sync.py`).
  2. **תאימות הרצת JavaScriptCore / Node:** `frontend/js/dashboard.js` נטען ישירות בבדיקות ללא DOM מלא; שמירה על `typeof document !== 'undefined'` ופונקציות ליבה סינכרוניות (`runAtsJobMatching`, `transformBulletTone`, `validateBulletGrammar`).
  3. **גבול פרטיות ו-GitHub Pages:** `tools/cv_tailor/base_profile.md` נותר מוחרג ב-`.gitignore`. קריאות AI חיות וגריפת קישורים מתבצעות רק מקומית מול `127.0.0.1:8765`, עם Fallback מילולי שקוף במצב אופליין.
  4. **שימור חוזה ה-DOM של הבדיקות הקיימות:** שמירת `4` טאבים (`studioTab*`), `4` פאנלים (`studioModule*`), מניין הצעדים (`.studio-step-num` `3, 5, 3, 2` ו-`.studio-step-outline`), ומזהי היעד ב-`test_m2_ats_spec.py`, `test_m3_writer_spec.py` ו-`test_m456_studio_spec.py`.
  5. **אפס אימוג'ים ו-RTL לוגי:** קו לוגי (`start` / `end`) ל-`dir="rtl"`, וללא אימוג'ים בכל קובץ או תוצר.

---

## 2. ארכיטקטורת הפריסה (`Master Split-Screen`)

### 2.1 דסקטופ (`min-width: 1120px`)
- שורת סרגל עליונה קומפקטית: כרטיסית קליטת קו"ח (`#studioCvUploadBar`) + סרגל `4` הטאבים האופקי (`#studioTabAts`, `#studioTabWriter`, `#studioTabInterview`, `#studioTabSkills`).
- **מתחת לסרגל — פריסת `Master Split-Screen` (`grid-template-columns: minmax(0, 60fr) minmax(0, 40fr)`):**
  - **אזור הפעולה (`inline-start`, 60% רוחב):** `.studio-modules-container` המציג את הטאב הפעיל.
  - **תצוגת הקו"ח החיה הדביקה (`inline-end`, 40% רוחב, `position: sticky; top: 16px`):** `#studioStickyPreviewCol` המציג:
    - כותרת + תג מקור (`פרופיל בסיס / חבילת Gemini / עריכה מקומית`), מד התאמת ATS נוכחי (`#stickyPreviewScoreBadge`), ומונה נקודות מאושרות.
    - `#studioLiveDocViewer` (מופעל מ-`StudioState`, רינדור DOM בטוח דרך `createSafeMarkdownNodes` ללא `innerHTML`), שבו שורות הניסיון ניתנות לבחירה (`click` / מקלדת) לצורך עריכה דו-כיוונית בטאב 2.
    - כפתורי פעולה מהירים בראש הפאנל: פתיחת חלון ייצוא `A4 PDF` / שמירה ל-`output` (`#studioExportDialog`) והדגשת שינויים אחרונים.

### 2.2 מובייל וטאבלט (`max-width: 1119px`)
- אזור הפעולה מקבל **100% רוחב** (`minmax(0, 1fr)`).
- עמודת התצוגה הקבועה מוסתרת מהזרימה הראשית ונפתחת דרך כפתור ייעודי בשורת הכותרת של הסטודיו (`#btnMobileOpenPreview`, מינימום גובה `48px` — **ללא FAB צף** כדי למנוע חפיפה עם `#btnBackToTop`), המזרים את אותו רינדור בטוח לתוך חלון `<dialog id="studioMobilePreviewDialog">` (`showModal()`, סגירה בלחיצת `Esc` / רקע / כפתור סגור).

---

## 3. מפרט השדרוג לפי טאבים (P0)

### טאב 1 — התאמת ATS ושערי סף (`#studioModuleAts`)
- **קלט והתראות (`step-ats-1`):** שמירת קליטת URL (`/api/studio/ingest`), בחירת משרה שמורה/כוכב (`#atsJobSelector`), קלט שם חברה/כותרת, התראת רשימת החרגות (`#atsBlacklistAlert`), וכפתור ניתוח עמוק (`Gemini`) כולל שאלות הבהרה (`Clarifications`).
- **תצוגת תוצאות ושערי סף (`step-ats-2`, `step-ats-3`):**
  - בשערי הסף הסטטוטוריים (`#atsHardGatesList`): הצגת **שערים עם פער או בתהליך או רלוונטיים למשרה** באופן פתוח בראש הרשימה, וקיבוץ השערים התקינים/שלא נדרשו בתוך `<details class="studio-passed-gates-accordion">` סגור כברירת מחדל (שומר על כל המידע ב-DOM עם `find-in-page` תקין ובלי כותרות בתוך `<summary>`).
  - שמירת 4 קטגוריות מילות המפתח + תאימות מבנה ATS מתחת במבנה קומפקטי ונקי.

### טאב 2 — עורך תוכן, סנכרון דו-כיווני ומגירת מילון (`#studioModuleWriter`)
- **סנכרון דו-כיווני מול ה-Live Preview:**
  - לחיצה על שורת הישג ב-`#studioLiveDocViewer` מעבירה אותה אל `#writerRawInput`, מעבירה לטאב 2 במקרה הצורך וגוללת ל-`#step-writer-3` (`selection-to-editor`).
  - לחיצה על `"החל על קו״ח"` (`applyBulletToCv()`) מוסיפה/מעדכנת את הבולט בתוך `StudioState.appliedBullets` וב-`#studioLiveDocViewer` ומציגה סימון הדגשה זמני (`selection highlight`) בחלון החי (`editor-to-preview`).
- **מגירת מילון מונחים (`step-writer-4` -> `<dialog id="studioGlossaryDialog">`):**
  - באזור `step-writer-4` מוצג סרגל קומפקטי (`"פתח מילון מונחים (20 מונחים)"`) במקום פריסת 20 כרטיסים ארוכה בדף.
  - `#dictSearchInput`, `#btnDictClearSearch`, `#dictTermsCount` ו-`#dictCardsGrid` נשמרים במלואם בתוך `<dialog id="studioGlossaryDialog">` (תאימות מלאה ל-`test_m3_23_index_template_has_writer_components` ופונקציות החיפוש!). לחיצה על מונח מזריקה לעורך וסוגרת את המגירה בנגישות.
- **ממשק ייצוא `A4` ממוקד (`step-writer-5` -> `<dialog id="studioExportDialog">` + `#studioPackageWorkbench`):**
  - יצירת חבילת `Gemini` (`HE`/`EN`), התראת דרישות חסרות, בחירה/השלמת הבהרות, צפייה בטוחה ופתיחת `<dialog id="studioExportDialog">` לייצוא `A4 PDF` (`printTailoredPackageA4`) או שמירה ישירה ל-`tools/cv_tailor/output/` (`POST /api/studio/export`). שני כרטיסי הבסיס (`cv_he.html`, `cv_en.html`) נותרים זמינים ב-`#writerCvHubGrid`.

### טאב 3 — סימולטור ראיונות ולינקדאין (`#studioModuleInterview`)
- הוספת **Segmented Control** בראש הפאנל (`role="tablist"`: `#interviewSegSimBtn` עבור סימולטור `STAR` + השאלות מול `#interviewSegLiBtn` עבור הלימה מול `LinkedIn`), תוך הצגת משימה אחת ממוקדת בכל מצב ושמירה של שניהם נגישים דרך מתג המצב וב-DOM עבור `test_m6_02` ו-`test_m6_03` (`hidden` מבוקר בלבד על העמודה הלא-פעילה, עם חיווי `aria-selected`).

### טאב 4 — פערי מיומנויות ואנונימיזציה (`#studioModuleSkills`)
- שמירה על 4 המלצות הסמכה בממשק תמציתי וקומפקטי (`step-skills-1`).
- באנונימיזציה (`step-skills-2`): הוספת **סינון מזהים דינמי (`redactSensitiveText`)** הפועל גם על טקסט חי מ-`Live Preview` / בולטים שהוזנו ידנית (הסתרת שם, טלפון, מייל, קישור LinkedIn ומעסיק רגיש), + כפתור הדפסה/ייצוא מסמך אנונימי ל-`PDF A4` (`printAnonymizedCvA4`).

---

## 4. ניהול מצב אחיד ב-Vanilla JS (`StudioState`)

- `window.StudioState` מרכז במקום אחד: `bridgeConnected`, `profile`, `activeJob`, `atsLocalReport`, `atsAiAnalysis`, `clarifications`, `appliedBullets`, `selectedPreviewLineIndex`, `tailoredPackage`, `previewSourceMode`, `interviewSubMode` (`'simulator' | 'linkedin'`).
- כל פונקציות ה-UI מפרסמות דרך `updateStudioState(patch)` המרענן את `#studioLiveDocViewer` ואת מדי הציון באופן דטרמיניסטי, עם שומרים לריצת `Node`/`JSC`.

---

## 5. קריטריוני קבלה ואימות (`Definition of Done`)

1. כל בדיקות היחידה הקיימות והחדשות (`326+` בדיקות פייתון ו-`2,489` בדיקות `stress_m2_harness.js`) עוברות ללא שינויי הקלה.
2. `tests/test_template_docs_sync.py` ו-`scripts/validate_zero_emoji.py` עוברים (`0` אמוג'ים, 1:1 parity בין `frontend/` ל-`docs/`).
3. אימות בדפדפן דרך `Chrome DevTools` ברוחב `1440x900` (דסקטופ Split-Screen + Sticky Preview, סנכרון דו-כיווני, Drawer מילון, אקורדיון שערי סף, Segmented Control בטאב 3) וברוחב `390x844` (אפס גלישה אופקית, `<dialog>` מקדים במובייל ללא חפיפת כפתורים, שדות `>= 16px` ויעדי מגע `>= 48px`).
