# מפרט ארכיטקטורה ו-UX מאוחד — Career Studio 3.0 (`job_search_automation`)

מפרט זה מגדיר את ארכיטקטורת **Career Studio 3.0** (`55/45` Master Split-Screen, סרגל הקשר עליון אחוד, ו-3 כלי ליבה ממוקדים בהשראת **Jobscan**, **Resume Worded** ו-**Teal HQ**) מול התשתית של [`scripts/studio_bridge.py`](../scripts/studio_bridge.py), [`tools/cv_tailor/`](../tools/cv_tailor/tailor.py), והמחסנית הוונילית [`frontend/`](../frontend/templates/index.html) -> [`docs/`](index.html).

---

## 1. מטרה, היקף וביטול רכיבי סרק
- **מטרה:** החלפת מבנה 4 הטאבים והניווט המשולש (13 תתי-צעדים ממוספרים) בארכיטקטורה שטוחה ופרקטית של **3 כלי ליבה בלבד** לצד תצוגת מסמך חיה ודביקה (`Sticky Live Document Viewer`).
- **רכיבים שהוסרו לצמיתות:**
  1. הטאב הרביעי (`studioModuleSkills` / `studioTabSkills`) שכלל 4 המלצות קורסים גנריות קשיחות (`PMP`, `Six Sigma`, `CEM`) וכלי אנונימיזציה לקבוצות פייסבוק/וואטסאפ.
  2. סרגל הצד הימני (`.studio-pipeline-sidebar`) וסרגלי קפיצת הצעדים הפנימיים (`.studio-step-outline`, `.studio-step-head` 1..5).
  3. מגירת המילון הסטטי בת 20 המונחים (`studioGlossaryDialog`) והחלונית הכפולה של תצוגת החבילה (`studioTailorPreviewPane` אוחד ישירות לתוך `#studioLiveDocViewer`).

---

## 2. ארכיטקטורת הפריסה (`55/45` Master Split-Screen)

### 2.1 סרגל הקשר עליון אחוד (`.studio-context-bar`)
- שורת כותרת וסטטוס גשר ה-AI (`#studioBridgeStatusPill`) + כפתור תצוגה מקדימה למובייל (`#btnMobileOpenPreview`).
- סרגל משרת היעד (`#atsStep1Panel.studio-target-bar`):
  - בורר משרות מסומנות בכוכב/שמורות (`#atsJobSelector`) + הזרקה בלחיצה אחת מכרטיסי לוח המשרות (`openJobInCareerStudio`).
  - שליפת משרה מכתובת URL (`#atsJobUrlInput` + `#btnFetchJobUrl`).
  - חיווי קו״ח פעיל והעלאת קובץ קומפקטית (`#studioCurrentCvStatus`).
  - אקורדיון `<details id="studioJobDetailsAccordion">` לעריכת חברה, תפקיד ותיאור המשרה המלא (`#atsCompanyInput`, `#atsTitleInput`, `#atsJobInput`).
- סרגל **3 כלי הליבה** (`nav.studio-subnav-pipeline` עם `focusgroup="tablist nomemory" role="tablist"`):
  1. `#studioTabAts` — סורק התאמת משרה ופערי ATS (`Jobscan Matcher`).
  2. `#studioTabWriter` — בונה קורות חיים מותאם ודירוג שורות (`Teal & Resume Worded`).
  3. `#studioTabInterview` — אופטימיזציית `LinkedIn SEO` והכנה לראיון (`Role Interview Prep`).

### 2.2 פריסת 2 עמודות בדסקטופ (`grid-template-columns: minmax(0, 55fr) minmax(0, 45fr)`)
- **עמודת כלי הפעולה (`55%`, `.studio-modules-container` עם `container: studio-main / inline-size`):** מציגה את הכלי הפעיל כאשר הפאנלים הלא-פעילים מוגדרים עם `hidden="until-found"` ומאזיני `beforematch` לתמיכה בחיפוש דפדפן (`Cmd+F`).
- **עמודת המסמך החי והדביק (`45%`, `#studioStickyPreviewCol`):**
  - בורר מסמך חי (`#pkgTabCv` קו״ח מותאם, `#pkgTabCover` מכתב פנייה, `#pkgTabTips` 3 דגשים לראיון).
  - כפתורי ייצוא מהירים (`#btnStickyOpenExport`, `#btnStickyQuickPrintA4`) ומונה שדרוגים שהוחלו.
  - `#studioLiveDocViewer` עם לחיצה דו-כיוונית על כל שורה לטעינה ישירה לעורך (`selectPreviewLineForEditing`).

---

## 3. מפרט 3 כלי הליבה

1. **כלי 1 — סורק התאמת משרה ופערי ATS (`#studioModuleAts`):**
   - מד התאמה משוקלל (`#atsScoreGaugeRing`), אבחון מילולי + ניתוח עומק `Gemini` ומחקר חברה חי (`#atsAiInsightsCard`).
   - שערי סף סטטוטוריים (`#atsHardGatesList`) עם קיפול שערים תקינים ב-`<details class="studio-passed-gates-accordion">`.
   - מטריצת מילות מפתח ב-4 קטגוריות שבה כל מילת מפתח חסרה היא **כפתור פעולה חי (`injectKeywordToWriter`)** המזריק תבנית הישג מבוססת-אמת ישירות לכלי 2.
2. **כלי 2 — בונה קו״ח מותאם (`A4`) ומבקר עוצמת שורות (`#studioModuleWriter`):**
   - **איחוד הפקת חבילת מועמדות (`#studioPackageWorkbench`):** בחירת שפה (`HE`/`EN`), טון כתיבה (`Technical`, `Operational`, `Strategic`), הפקת חבילת `Gemini` מלאה וייצוא `A4 PDF`.
   - **מבקר עוצמת שורות (`#writerBulletAuditList` — `renderBulletImpactAuditor`):** סורק אוטומטית את שורות הניסיון מקורות החיים הפעילים, מדרג כל שורה (`0-100`) לפי פועל פעיל, מערכת הנדסית ומדד כמותי, ומאפשר טעינה בלחיצה אחת לשכתוב.
3. **כלי 3 — אופטימיזציית `LinkedIn SEO` והכנה לראיון (`#studioModuleInterview`):**
   - **אופטימיזציית `LinkedIn SEO` דינמית (`#interviewColSide` — `renderLinkedInOptimizer`):** מייצרת בזמן אמת הצעת `Headline` (`#linkedinHeadlineOutput`), תקציר `About` (`#linkedinAboutOutput`) ותגיות `Skills` (`#linkedinSkillsChips`) המותאמים למשרת היעד הפעילה עם העתקה בלחיצה אחת.
   - **הכנה לראיון וסימולטור `STAR` (`#interviewColMain`):** כולל קטגוריית `role_fit` המייצרת שאלות ראיון מותאמות לחברה ולפערי המשרה הפעילה, זיהוי דיבור דפדפני אמיתי והערכת `STAR` ב-`Gemini`.
