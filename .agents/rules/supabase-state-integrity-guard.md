---
trigger: glob
globs: "supabase/**, frontend/js/**, docs/dashboard.js, scripts/*cloud*"
description: "Guarantees absolute non-destructive persistence and integrity for user triage state in Supabase Cloud Database (public.sync_state)."
---

# Supabase State Integrity Guard (`public.sync_state`)

## 1. Protected Data Boundary
The user's triage decisions (`starred`, `saved`, `rejected`, `purged`, applied dates, and personal notes) are the primary persistent assets of `job_search_automation`:
- **Remote Source of Truth:** Hosted Supabase Cloud Database (`eu-central-1`, project `dvmdbupifrltbvyyfrdk`), table `public.sync_state`.
- **Local Cache & Offline Adapters:** Browser `localStorage` and `data/sync_state.json`.

## 2. Invariant Rules (Iron Guards)
1. **Never Truncate, Drop, or Overwrite State:** Executing destructive SQL statements (`DROP TABLE`, `TRUNCATE`, `DELETE FROM sync_state` without a scoped target ID) or overwriting `sync_state` with blank/default templates is strictly forbidden.
2. **Additive Upsert Contract:** All synchronization operations between the local pipeline, scrapers, and Supabase must use non-destructive upserts (`ON CONFLICT DO UPDATE` or equivalent REST merge logic). An existing user triage label (`starred`, `saved`, `rejected`) must never be silently cleared or reverted to unreviewed by a new scrape run.
3. **Safe Schema Migrations:** Any table alteration, index addition, or RLS policy change must be executed carefully via `apply_migration` or Supabase CLI, and followed immediately by verifying health through:
   - Security and performance lints: `get_advisors` via `supabase_mcp`.
   - Table inspection: `list_tables` via `supabase_mcp`.
4. **Offline & Node.js Runtime Safety:** All client-side polling and network listeners targeting Supabase in `frontend/js/dashboard.js` and `docs/dashboard.js` must remain guarded by `typeof process === 'undefined'` to avoid hanging timers during headless test runs (e.g., `tests/stress_m1_harness.js`).
