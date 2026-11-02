---
trigger: glob
description: "Enforce strict candidate realism, locked original job titles, and zero inflation across all tailored CV and cover letter outputs."
globs: ".agents/skills/cv-tailor/**, docs/career/cv/**, frontend/data/cv/**, output/**"
---

# Candidate Realism, Locked Titles & Anti-Fluff Policy

1. **Locked Original Role Titles:**
   - Always retain the candidate's exact, authentic job titles from `base_profile.md`:
     * `בקר גז — תפעול ומוצר | Energean Israel Ltd.` / `ENERGEAN ISRAEL LTD. – Gas Controller – Operations and Product`
     * `אחראי משמרת אבטחה במתקן אנרגיה אסטרטגי | וולקן עוצמה בע״מ / Energean Israel Ltd.` / `ENERGEAN ISRAEL LTD. / VOLCAN OTZMA LTD. – Security Shift Supervisor – Strategic Energy Facility`
     * `ראש צוות ומדריך מכירות | חברות מכירות בפעילות בינלאומית` / `INTERNATIONAL BUSINESS OPERATIONS – Team Leader & Sales Instructor`
     * `מתקין מערכות סולאריות | MER Group` / `MER GROUP – Solar Systems Installer`
   - NEVER alter a past role title to mimic the target job title.

2. **Grounded & Honest Phrasing (Zero-Inflation):**
   - Tailoring is achieved ONLY through re-prioritizing real bullets and emphasizing genuinely relevant aspects (e.g. solar thesis, 24/7 operations, AVEVA System Platform, Copilot AI agents, English fluency, Excel/SAP).
   - NEVER dress up sales leadership as construction/EPC engineering.
   - NEVER inflate hands-on PV installation into large-scale project management.
   - Keep language humble, direct, factual, and metric-driven.

3. **Bridge the Gap Honestly:**
   - Position the candidate as an authentic, high-potential Practical Mechanical Engineer with strong operational grounding and renewable energy education.

## Absolute Truthfulness & Asking Clarifications
- If a target role or domain requires skills/experience not documented in `base_profile.md`, NEVER assume or fabricate them.
- Always ask the user directly for clarification if in doubt.
- Bridge only through genuine, transferable skills already verified in `base_profile.md`.
