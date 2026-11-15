---
name: job-market-salary-intelligence
description: "Project-specific skill for calibrating, validating, and displaying evidence-based Israeli salary estimates (monthly gross ILS) in job_search_automation via src/salary_engine.py."
---

# Job Market Salary Intelligence (`job_search_automation`)

## 1. Scope & Production Anchor
- **Workspace Scope:** Applies strictly to `/Users/ido/.gemini/antigravity/scratch/job_search_automation`.
- **Production Engine:** Anchored directly to `src/salary_engine.py`, `src/job_policy.py`, `search-preferences.json`, and `tests/test_salary_intelligence.py`.
- **Standard Display Basis:** All salary figures in this project are normalized to **Israeli Monthly Gross Base Salary in ILS (ש"ח ברוטו לחודש, 100% משרה)**, with shift supplements, company vehicle (`רכב צמוד`), and bonuses noted separately.

## 2. Mandatory Salary Floors & Domain Calibration (`search-preferences.json`)
Enforce the candidate's explicit compensation boundaries alongside market estimation:
1. **Absolute Floor:** **`14,000 ILS / month`**. Any role with an explicitly advertised salary `< 14,000 ILS` is automatically disqualified (`Score = 0`).
2. **Control Room & Shift Policy:** `24/7` rotating shift roles are strictly disqualified per `search-preferences.json`; daytime/operational control-room roles require explicit energy/utility SCADA (`>= 20,000 ILS` benchmark for senior/shift-adjacent control rooms).
3. **Target Compensation Range:** **`14,000 – 22,000+ ILS / month`** across Ido Gal's core role families:
   - **Gas & Pressure Systems / PRMS / Power Stations:** Typically `16,000 – 24,000 ILS`.
   - **Solar PV / BESS / Commissioning / Site Coordination & SCADA Operations:** Typically `14,500 – 22,000 ILS` (often includes field vehicle `רכב צמוד`).
   - **UAV / Drone Integration, Flight-Test & Avionics Operations:** Typically `16,000 – 24,000 ILS` depending on defence tier and experience level.
   - **Practical Mechanical Engineer (הנדסאי מכונות) Energy & Cleantech Operations:** Typically `14,000 – 21,000 ILS`.

## 3. Estimation & Provenance Rules (`src/salary_engine.py`)
1. **Strict Separation of Estimate Types:**
   - `advertised`: Explicitly stated in the job posting. Never overwrite an advertised salary with a model guess.
   - `market_estimate`: Calibrated P25–P75 range derived from comparable Israeli roles by domain family, seniority, shift model, and employer tier.
   - `insufficient_data`: When role scope is too vague to anchor reliably, abstain cleanly rather than inventing numbers.
2. **Adjustments & Signals:**
   - Account for explicit shift structures (`משמרות 24/7`), field vs. HQ location, Tier-1 energy/defence employer premiums, and years of practical experience required.
   - Assign transparent confidence levels (`high | medium | low | insufficient`) with explicit Hebrew rationale rendered in the dashboard job card.

## 4. Verification & Testing
- Run `python3 -m unittest tests/test_salary_intelligence.py` after any calibration or rule update in `src/salary_engine.py`.
- Ensure UI rendering in `frontend/js/dashboard.js` (`docs/dashboard.js`) clearly labels whether a range is advertised (`שכר מפורסם`) or estimated (`הערכת שוק`), with zero emojis.
