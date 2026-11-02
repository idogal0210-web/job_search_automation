---
description: Enforce strict candidate realism, locked original job titles, and zero inflation across all tailored CV and cover letter outputs
globs: "tools/cv_tailor/**"
---

# Candidate Realism, Locked Titles & Anti-Fluff Policy

1. **Locked Original Role Titles:**
   - Always retain the candidate's exact, authentic job titles from `base_profile.md`:
     * `בקר גז │ Energean Israel Ltd.` / `Gas Controller │ Energean Israel Ltd.`
     * `קצין ביטחון, מתקן אנרגיה אסטרטגי │ Vulcan / Energean` / `Security Officer – Strategic Energy Facility │ Vulcan / Energean`
     * `ראש צוות ומדריך מכירות │ פעילות בינלאומית` / `Sales Team Leader & Trainer – International Operations`
     * `מתקין מערכות סולאריות PV │ Group MER` / `Solar PV Systems Installer │ Group MER`
   - NEVER alter a past role title to mimic the target job title.

2. **Grounded & Honest Phrasing (Zero-Inflation):**
   - Tailoring is achieved ONLY through re-prioritizing real bullets and emphasizing genuinely relevant aspects (e.g. solar thesis, 24/7 operations, English fluency, Excel/AI).
   - NEVER dress up sales leadership as construction/EPC engineering.
   - NEVER inflate hands-on PV installation into large-scale project management.
   - Keep language humble, direct, factual, and metric-driven.

3. **Bridge the Gap Honestly:**
   - Position the candidate as an authentic, high-potential Practical Mechanical Engineer with strong operational grounding and renewable energy education.

## 4. Zero Synthetic Logos Policy (איסור מוחלט על לוגואים גנריים או מלאכותיים)
- חל איסור מוחלט להמציא לוגו, לייצר גרפיקה מלאכותית, או להשתמש במונוגרמות אותיות גנריות (כגון אווטאר אותיות).
- קישור לוגו (`company_logo_url`) חייב להיות אך ורק קישור ישיר מאומת מתוך עמוד החברה ב-LinkedIn, או Favicon רשמי ברזולוציה גבוהה מדומיין הבית של החברה, או נכס וקטורי רשמי מקומי.
- במידה ולא קיים לוגו רשמי מאומת, השדה `company_logo_url` יישאר ריק (`null`), ושם החברה יוצג בטיפוגרפיה נקייה.
- כל תגית תמונת לוגו בממשק תכלול מנגנון `onerror` תקני המסתיר את תגית התמונה בצורה חלקה במידה והלוגו נחסם או נכשל בטעינה (404/CORS), ללא עיוות מבנה הכרטיס.

## Absolute Truthfulness & Asking Clarifications
- If a target role or domain requires skills/experience not documented in `base_profile.md`, NEVER assume or fabricate them.
- Always ask the user directly for clarification if in doubt.
- Bridge only through genuine, transferable skills already verified in `base_profile.md`.
