---
name: job-search-automation
description: Automates daily job searches tailored to Ido Gal's resume (Gas Controller, Mechanical Engineer, Energy Operations), scoring matches with Gemini AI and delivering email alerts.
---

# Job Search Automation Skill for Ido Gal

This skill manages and executes automated job searching, AI-based match scoring, and daily email summaries for Ido Gal.

## Candidate Profile Summary
- **Name:** Ido Gal (עידו גל)
- **Degree:** Practical Mechanical Engineer (הנדסאי מכונות - אנרגיה ירוקה וגז טבעי) + Certified Electrician (in progress). NOT B.Sc. Engineer.
- **Target Roles:** Gas Controller, Energy Operations Manager, Practical Mechanical Engineer, Solar & Renewable Energy Infrastructure (High Priority ⭐), Technical Team Leader, Field Operations.
- **Target Companies (High Priority ⭐):**
  - **Solar:** Enlight, Doral, Nofar, Energix, EDF Renewables, Shikun & Binui Energy, Afcon, Enerpoint.
  - **Energy Tech / AI:** SolarEdge, Augury, BrightSource, Driivz, REplace, Siemens Energy, Honeywell, ABB, Brightmerge.
  - **Gas & Storage:** NewMed, OPC Energy, Dorad, Edeltech, Nostromo, Brenmiller, StoreDot, Electreon, H2Pro, GenCell.
  - **Industry & Contractors:** ICL (כיל), חברת החשמל, מקורות, IDE, אלקטרה, מנרב.
- **Excluded Companies:** נתג"ז (INGL), Chevron Israel (שברון), Raycatch, Australia FIFO.
- **Location:** Israel (Center, Sharon, North, South) & Overseas Relocation.
- **Email:** idogal0210@gmail.com

## How to Execute Job Search
To trigger a manual job search and email dispatch:
```bash
python3 /Users/ido/.gemini/antigravity/scratch/job_search_automation/job_search.py
```

## Key Components
1. `job_search.py`: Core Python script that fetches job leads, evaluates matches using Gemini 2.0 / Flash API, and sends HTML formatted email reports.
2. `.github/workflows/daily_job_search.yml`: GitHub Actions schedule to execute daily in the cloud for zero cost even when the local machine is powered off.
3. `requirements.txt`: Python package dependencies.
