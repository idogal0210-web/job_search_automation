---
trigger: always_on
description: "Trigger the save-and-sync skill whenever the user writes שמור ועדכן, שמור וסנכרן, סנכרן ונקה, or Save and update."
---

# Save & Sync Trigger ("שמור ועדכן")

Whenever the user issues the trigger phrase **"שמור ועדכן"**, **"שמור וסנכרן"**, **"סנכרן ונקה"**, or **"Save and update"**, immediately load and follow the workspace skill [`.agents/skills/save-and-sync/SKILL.md`](file:///Users/ido/.gemini/antigravity/scratch/job_search_automation/.agents/skills/save-and-sync/SKILL.md).

Core invariants:
- Never infer `CLEAN` from `SAVE` or `SYNC` unless explicitly requested.
- Always refer to the remote platform as **GitHub** (never generic git).
- Strictly enforce zero emojis in all commit messages, logs, and RTL executive summaries.
