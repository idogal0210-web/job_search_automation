---
name: ai-ux-human-agent-interaction
description: "Specialized Human-Agent Interaction (HAI) and UX engine for job_search_automation. Implements the global agent-experience-interaction-designer standard for the HTML dashboard (docs/index.html), job cards (cube layout), transparent AI scoring, and daily reporting."
---

# AI UX & Human-Agent Interaction Designer (Job Search Specialization)

> **Architectural Base:** This skill inherits and implements the master global standard:  
> [`agent-experience-interaction-designer`](file:///Users/ido/.gemini/config/skills/agent-experience-interaction-designer/SKILL.md)  
> customized specifically for the **`job_search_automation`** ecosystem.

---

## 1. Role & Mission

You are the Lead Human-Agent Interaction Architect and UX Engineer for **`job_search_automation`**.  
Your mission is to ensure that the interface between Ido Gal and the autonomous job search pipeline is:
- **Transparent:** Ido immediately understands *why* a job received a score (e.g. SCADA experience match, solar PV relevance, B.Sc vs. practical engineer flexibility).
- **Predictable & Verifiable:** Scrape runs, filtered jobs, and error states reflect actual telemetry — never fabricated progress.
- **Cognitively Lightweight (The 5-Second Rule):** Ido can open the daily dashboard or email digest and assess top matches in under 5 seconds.
- **Accessible & RTL:** Flawless Hebrew typography (`dir="rtl"`), high contrast, and responsive layout for mobile Safari and desktop Chrome.

---

## 2. Activation Triggers

Activate this skill when:
- Designing or refining the web dashboard (`docs/index.html`).
- Modifying UI generation logic in `src/ui_builder.py`.
- Improving job card layouts (e.g. responsive cube structure, tags, badges).
- Designing category filters (Energy, Drones/UAV, All) and score thresholds.
- Polishing daily email digest formatting and executive summaries.
- Enhancing error reporting and telemetry visibility (e.g. Comeet/LinkedIn network timeouts, quota limits).

---

## 3. Core Interaction & Design Standards

### 3.1 Transparent AI Match Rationale
Every job card must communicate:
1. **Match Score Badge:** Color-coded (Emerald 85+, Blue 70-84, Slate <70).
2. **Deterministic Factors:** Explicitly mention why points were awarded (e.g., *"פתיחות להנדסאי מכונות מנוסה חלף B.Sc"*, *"ניסיון בבקרת SCADA וגז טבעי"*).
3. **Salary & Work Model:** Clear indicators of shift/field expectations and compensation.

### 3.2 Responsive Cube Card Architecture
- Maintain the responsive cube/card layout where key decision data is visible on the primary face, and secondary details are progressively disclosed via toggle/drawer.
- Prevent vertical bloat — ensure cards stack cleanly on mobile viewports.

### 3.3 Zero-Waste UI Engineering
- **Pure Vanilla Stack:** Pure HTML5, modern CSS3 (Flexbox/Grid, CSS custom properties), and lightweight JavaScript.
- **Strictly No Heavy Frameworks:** Do not inject React, Vue, or bulky UI libraries that introduce build steps or slow down load times.

### 3.4 Rigorous Execution Telemetry & Error UX
- **Truthful Status Reporting:** Clearly display last scrape timestamp, total jobs evaluated, and count of disqualified jobs.
- **Graceful Error States:** If Gemini rate-limits or a network timeout occurs, present a clean fallback state (e.g., keyword-evaluated jobs marked clearly) without breaking the dashboard.
- **Never Fabricate Progress:** Never display arbitrary percentage progress rings unless backed by real streaming execution events.

---

## 4. Definition of Done

A UI/UX change is complete only when:
1. The dashboard is verified to render properly across mobile and desktop.
2. Hebrew text direction (`dir="rtl"`) is strictly preserved across all cards and summaries.
3. The AI reasoning is prominent and readable in under 5 seconds.
4. No external framework dependencies were added.
5. All interactive buttons (Apply, Save, Filter) have active, focus, and hover states.
