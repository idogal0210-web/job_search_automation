---
name: cv-tailor
description: "Tailors Ido Gal's CV or requested cover letter to a specific vacancy in Hebrew or English, preserving factual qualifications and original role titles. Integrates with tools/cv_tailor/, prompts/cv_generation_v1.txt, and Career Studio ATS/Writer modules. Excludes job searching, invented achievements and automatic application submission."
---

# Factual CV Tailoring & ATS Optimization (`job_search_automation`)

## 1. Canonical Scope & Source Contract
- **Workspace Root:** `/Users/ido/.gemini/antigravity/scratch/job_search_automation` ([scope.json](references/scope.json)).
- **Canonical Candidate Profile:** Read [profile-source.json](references/profile-source.json) -> `/Users/ido/.gemini/antigravity/scratch/job_search_automation/tools/cv_tailor/base_profile.md` (`Ido Gal`).
- **Target & Exclusion Reference:** Read [target_companies.json](references/target_companies.json) and `/Users/ido/.gemini/antigravity/scratch/job_search_automation/.agents/skills/job-search-automation-state/references/search-preferences.json`. Never tailor CVs for blacklisted employers (`Energean`, `INGL`, `Chevron`).
- **Engine & Prompt Assets:**
  - Codebase module: `tools/cv_tailor/`
  - Structured Prompts: `prompts/cv_analysis_v1.txt` (ATS gap analysis) and `prompts/cv_generation_v1.txt` (factual tailoring)
  - Career Studio API Bridge: `scripts/studio_bridge.py` (`POST /api/ats/match`, `POST /api/writer/tailor`) validated via Pydantic schemas in `src/gemini_runtime.py`.

## 2. Iron Rules of Factual Integrity
Follow [realism-rules.md](references/realism-rules.md) and [realism-guidelines.md](references/realism-guidelines.md):
1. **Zero Fabricated Credentials:** Ido Gal is a certified **Practical Mechanical Engineer (הנדסאי מכונות מוסמך)**. Never claim or imply a `B.Sc` degree, completed electrician license, or unverified certification.
2. **Preserve Original Role Titles:** Keep the exact Hebrew title (`בקר גז - תפעול ומוצר`) or its approved English equivalent; never inflate into senior engineering or product-management titles.
3. **Separate Study from Field Experience:** Never present study topics or training familiarity (e.g., gas chromatography, PRMS commissioning) as hands-on employment history unless explicitly verified in `base_profile.md`.
4. **Evidence-Backed Metrics Only:** Use numeric achievements only when present in the canonical profile. Do not invent percentages, downtime reductions, or team sizes.

## 3. Tailoring & Career Studio Workflow
1. **Vacancy & ATS Gap Analysis (`prompts/cv_analysis_v1.txt`):**
   - Extract mandatory requirements, preferred keywords (SCADA, HMI, PLC, Solar PV, Natural Gas, UAV systems, pressure regulation), and statutory hard gates.
   - Map each requirement against `base_profile.md` into: `Matched Evidence`, `Transferable Experience`, or `True Gap`.
2. **Targeted Rewriting (`prompts/cv_generation_v1.txt`):**
   - Support the 3 Career Studio tone modes when requested:
     - **Engineering / Operational Precision (הנדסי-תפעולי):** Emphasize SCADA control, fault diagnosis, pressure/flow systems, and safety procedures.
     - **ATS Keyword Optimized (מותאם מילות מפתח):** Align terminology naturally with the job posting's exact phrasing without keyword stuffing.
     - **Executive / Impact Focused (ממוקד תוצאות):** Highlight operational reliability, cross-team coordination, and field-to-control-room interface.
3. **Formatting & Privacy ([israeli-cv-structure.md](references/israeli-cv-structure.md), [a4-single-page-specs.md](references/a4-single-page-specs.md), [eeo-compliance-checklist.md](references/eeo-compliance-checklist.md)):**
   - Maintain a clean **one-page A4** layout with proper RTL (`dir="rtl"`) for Hebrew or LTR for English.
   - Omit age, date of birth, marital status, ID number, photo, and exact street address.
   - Save authorized outputs using [folder-and-naming-conventions.md](references/folder-and-naming-conventions.md) (e.g., `CV_<Company>_HE.pdf`) without overwriting `base_profile.md`.

## 4. Verification & Delivery
- Cross-check every bullet against `base_profile.md` before output.
- Explicitly list any unmatched mandatory requirements (e.g., mandatory B.Sc or specific license) so Ido can make an informed submission decision.
- Strictly zero emojis across all generated CVs, cover letters, and UI outputs.
