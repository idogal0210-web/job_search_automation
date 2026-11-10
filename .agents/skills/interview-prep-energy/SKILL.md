---
name: interview-prep-energy
description: "Conducts evidence-based interview practice for Ido Gal in energy, gas operations, solar PV, SCADA/control-room, mechanical systems and UAV roles. Powers both conversational mock interviews and Career Studio's structured STAR simulator (scripts/studio_bridge.py)."
---

# Energy, Gas, SCADA & UAV Interview Practice (`job_search_automation`)

## 1. Canonical Scope & Profile Grounding
- **Workspace Root:** `/Users/ido/.gemini/antigravity/scratch/job_search_automation` ([scope.json](references/scope.json)).
- **Canonical Candidate Profile:** Read [profile-source.json](references/profile-source.json) -> `/Users/ido/.gemini/antigravity/scratch/job_search_automation/tools/cv_tailor/base_profile.md` (`Ido Gal`).
- **Architectural Integration:**
  - Powers conversational mock interviews in chat AND the Career Studio **STAR Interview Simulator** (`scripts/studio_bridge.py` -> `POST /api/interview/evaluate` backed by `src/gemini_runtime.py` Pydantic schemas).
  - Strictly separate verified hands-on experience in `base_profile.md` from study topics or theoretical concepts. Never frame study topics (e.g., gas chromatography, PRMS commissioning) as past employment experience.

## 2. Domain Focus Areas
Tailor technical, situational, and HR questions to the target vacancy across Ido's core domains:
1. **Natural Gas & Energy Infrastructure:** Pressure/flow regulation, control-room alarm triage, SCADA/HMI monitoring, safety interlocks, ESD procedures, and field-to-control-room coordination.
2. **Solar PV & BESS Storage:** Inverter monitoring, string fault isolation, preventive maintenance schedules, grid interconnection coordination, and telemetry diagnostics.
3. **Industrial Mechanical & Rotating Equipment:** Pumps, valves, compressors, preventive/corrective maintenance, P&ID reading, and root-cause failure analysis.
4. **UAV / Drone Operations:** Mechanical integration, ground control station (GCS) telemetry, pre-flight/post-flight checklists, payload integration, and field testing protocols.

## 3. STAR Evaluation & Coaching Protocol
Whether evaluating an answer in Career Studio or running an interactive session:
1. **Structured STAR Rubric (0–100):**
   - **Situation (20%):** Clear operational context without confidential employer leaks.
   - **Task (20%):** Specific responsibility and operational constraint (safety, uptime, SLA).
   - **Action (40%):** Concrete personal engineering/operational steps taken (distinguishing personal actions from team actions).
   - **Result (20%):** Verifiable, factual outcome without invented metrics or exaggerated claims.
2. **Practical Engineer Positioning:**
   - Frame Ido's **Practical Mechanical Engineer (הנדסאי מכונות מוסמך)** background and control-room/operations experience as a hands-on strength.
   - When a role asks about theoretical gaps or B.Sc requirements, prepare honest, structured bridging answers that highlight field diagnostics, SCADA mastery, and rapid technical ramp-up.
3. **Refinement Loop:**
   - Identify 1–2 concrete improvements per answer.
   - Provide an upgraded **Golden Reference Answer (תשובת מופת מומלצת)** grounded strictly in `base_profile.md` facts.
   - In Career Studio, persist session scores (`LocalStorage`) to track longitudinal improvement across practice runs.

## 4. Safety & Execution Guardrails
- Never invent emergencies, safety incidents, or unverified metrics. If no personal example exists for a hypothetical question, explicitly frame the response as a theoretical troubleshooting methodology ("במצב כזה, מתודולוגיית הפעולה הנכונה היא...").
- Strictly zero emojis across all questions, feedback rubrics, and generated text.
