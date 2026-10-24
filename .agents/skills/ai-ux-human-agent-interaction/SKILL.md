---
name: ai-ux-human-agent-interaction
description: "Specialized Human-Agent Interaction (HAI) and UX engine for job_search_automation. Implements the global agent-experience-interaction-designer standard for the HTML dashboard (docs/index.html), zero-tag job cards, 1:1 desktop-mobile structural parity, high-res company logos, transparent AI scoring, and daily reporting."
---

# AI UX & Human-Agent Interaction Designer (Job Search Specialization)

> **Architectural Base:** This skill inherits and implements the master global standard:  
> [`agent-experience-interaction-designer`](file:///Users/ido/.gemini/config/skills/agent-experience-interaction-designer/SKILL.md)  
> customized specifically for the **`job_search_automation`** ecosystem.

---

## 1. Role & Mission

You are the Lead Human-Agent Interaction Architect and UX Engineer for **`job_search_automation`**.  
Your mission is to ensure that the interface between Ido Gal and the autonomous job search pipeline is:
- **Transparent:** Ido immediately understands *why* a job received a score (e.g. SCADA experience match, solar PV relevance, practical engineer vs. B.Sc flexibility).
- **Predictable & Verifiable:** Scrape runs, filtered jobs, and error states reflect actual telemetry — never fabricated progress.
- **Cognitively Lightweight (The 5-Second Rule):** Ido can open the daily dashboard or email digest and assess top matches in under 5 seconds.
- **Zero-Tag Clean Aesthetics:** Symmetrical, clean metric cubes without visual clutter, tag chips, or pill noise.
- **Accessible & RTL:** Flawless Hebrew typography (`dir="rtl"`), high contrast, and responsive layout for mobile Safari and desktop Chrome.

---

## 2. Activation Triggers

Activate this skill when:
- Designing or refining the web dashboard (`docs/index.html`).
- Modifying UI generation logic in `src/ui_builder.py`.
- Improving job card layouts (e.g. responsive cube structure, metric pills, action buttons).
- Designing category filters (Energy, Drones/UAV, All) and score thresholds.
- Polishing daily email digest formatting and executive summaries.
- Enhancing error reporting and telemetry visibility (e.g. Comeet/LinkedIn network timeouts, quota limits).
- Ensuring 1:1 structural parity between mobile and desktop presentations.

---

## 3. Core Interaction & Design Standards

### 3.1 Transparent AI Match Rationale
Every job card must communicate:
1. **Match Score Badge:** Color-coded (Emerald 85+, Blue 70-84, Slate <70).
2. **Deterministic Factors:** Explicitly mention why points were awarded (e.g., *"פתיחות להנדסאי מכונות מנוסה חלף B.Sc"*, *"ניסיון בבקרת SCADA וגז טבעי"*).
3. **Salary & Work Model:** Clear indicators of shift/field expectations and compensation.

### 3.2 Responsive Cube Card Architecture
- Maintain the responsive cube/card layout where key decision data is visible on the primary face, and secondary details are progressively disclosed via toggle/drawer.
- Prevent vertical and horizontal bloat — ensure cards stack cleanly on mobile viewports with zero horizontal scroll.

### 3.3 Zero-Tag Architecture (Strict Clean Design)
- **Zero Tag Chips:** Completely eliminate tag chips, badges, and pill chips from job cards and generator logic.
- **Structured Metric Grid:** Replace tags with structured, symmetrical 4-pill metric grids (Location, Experience, Role Type, Salary/Field) directly under the header.
- **Pure AI Synthesis:** Keep categorization and fit explanation embedded directly inside the AI rationale paragraph rather than scattered across chips.

### 3.4 Desktop-Mobile 1:1 Structural Parity
- **Identical Component Hierarchy:** Mobile and desktop layouts must contain the exact same structural components, cards, action buttons (2x2 action grid: Apply, Star, Dismiss, Details), and progressive disclosure details.
- **CSS-Only Proportional Scaling:** Adapt exclusively through responsive CSS media queries, grid columns, and viewport-friendly padding/typography. Never omit, hide, or alter core interactive features on mobile.

### 3.5 User Triage State & LocalStorage Integrity
- **Non-Destructive Hydration:** User annotations (starred jobs, dismissed jobs, applied status, and seen markers) stored in `localStorage` must NEVER be wiped, overwritten, or reset during UI updates or new scrapings.
- **Self-Healing Schema Migration:** Always validate and safely migrate triage data structures on page load without treating existing unreviewed jobs as newly injected alerts.

### 3.6 4-Tier High-Resolution Company Logo Pipeline
To prevent broken, blurry, or missing corporate emblems:
1. **Tier 1 - Direct Overrides:** Custom curated vector/PNG assets in `docs/assets/logos/`.
2. **Tier 2 - Clearbit High-Res Logo API:** Automated domain resolution (`https://logo.clearbit.com/{domain}`).
3. **Tier 3 - DuckDuckGo / Google Favicon High-Res Favicons:** Secondary automated visual fetch.
4. **Tier 4 - Vector Monogram Fallback:** Clean inline SVG avatar displaying the company's Hebrew/English initials with deterministic brand coloring.

### 3.7 Zero-Waste UI Engineering
- **Pure Vanilla Stack:** Pure HTML5, modern CSS3 (Flexbox/Grid, CSS custom properties), and lightweight JavaScript.
- **Strictly No Heavy Frameworks:** Do not inject React, Vue, or bulky UI libraries that introduce build steps or slow down load times.

### 3.8 Rigorous Execution Telemetry & Error UX
- **Truthful Status Reporting:** Clearly display last scrape timestamp, total jobs evaluated, and count of disqualified jobs.
- **Graceful Error States:** If Gemini rate-limits or a network timeout occurs, present a clean fallback state without breaking the dashboard.
- **Never Fabricate Progress:** Never display arbitrary percentage progress rings unless backed by real streaming execution events.

---

## 4. Definition of Done

A UI/UX change is complete only when:
1. The dashboard is verified to render properly across mobile and desktop with 1:1 structural parity.
2. Hebrew text direction (`dir="rtl"`) is strictly preserved across all cards and summaries.
3. Zero-tag architecture is verified: zero tag chips or obsolete pills in HTML, CSS, or JS.
4. User triage state (stars, dismissals, applied status) is safely preserved and resilient in LocalStorage.
5. All interactive buttons (Apply, Save, Filter, Star, Dismiss) have active, focus, and hover states.
6. Strictly zero emojis across all code, markup, styles, and generated outputs.
