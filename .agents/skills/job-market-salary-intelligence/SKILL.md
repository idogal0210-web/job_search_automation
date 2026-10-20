---
name: job-market-salary-intelligence
description: Project-specific skill for designing, implementing, validating, and improving evidence-based salary estimates in the job-search dashboard. Use for salary prediction, job compensation ranges, source ingestion, comparable jobs, salary confidence, salary cards, calibration, and salary feedback within this workspace only.
---

# Job Market Salary Intelligence — Project Skill

## Scope and operating contract

This skill applies **only** within the current job-search dashboard workspace. Store at `<workspace-root>/.agents/skills/job-market-salary-intelligence/SKILL.md`. Do not install, replicate, register, or move it into global skill directories. Do not apply it to unrelated repositories, even when discussing salary estimation.

Before any implementation, inspect existing repository instructions, architecture, job ingestion pipeline, schemas, UI components, tests, and existing salary logic. Reuse current conventions. Never presume a stack, database, country, currency, API credentials, or commercial data-access rights. Unless explicitly approved by the user, **do not modify source code, dependencies, config, data, schemas, secrets, deployment settings, or scheduled jobs; do not run migrations, external crawlers, or deployments**. Supply an implementation plan and request approval for scoped changes. Read-only inspection is permitted when tools/access are available; do not run destructive commands.

Do not assert accuracy based on model confidence or fabricated benchmarks. Prefer abstention to a misleading salary figure.

## Core mission

For each job, estimate an evidence-supported compensation distribution and surface both **market compensation** (peer jobs) and, only when calibrated employer-specific evidence exists, **likely employer offer**. These are separate prediction targets. Optionally estimate **candidate-specific negotiating position**, clearly flagged as more uncertain and requiring permission and appropriate user-provided data.

## Workflow

1. **Understand** — Extract role title, role family, occupation taxonomy (if present), seniority, relevant years of experience, location and remote arrangement, employment fraction, company industry/size, management scope, skill/technology requirements, employment type, and source date. Preserve missing values as `unknown`; never infer a numeric experience requirement or level from title alone without flagging uncertainty.
2. **Find evidence** — Prioritize salary directly advertised for the same vacancy; then verified employer/role/location observations; then recent comparable vacancies with disclosed compensation; then quality-assessed salary surveys. AI background knowledge is **not** a salary observation. Reference sources such as AllJobs, GotFriends, Ethosia, Glassdoor, and Levels.fyi as candidates for *licensed/authorized access*, not presumed APIs or unrestricted scraping.
3. **Check permission** — Verify access and terms, robots policy where relevant, privacy, retention and attribution obligations before fetching/storing third-party data. Prefer permitted APIs, exports, public disclosures and licensed datasets. If unavailable, report the blocker and use approved alternatives. No credential exposure.
4. **Normalize** — Store ISO currency, country/region, compensation period, gross/net basis, full-time equivalent, base vs bonus vs equity vs benefits, role level, as-of date, source ID, sample definition, and provenance. Never mix monthly base salary with annual total compensation. If conversion is needed, use dated FX data and explicit assumptions; do not convert undisclosed net to gross by guesswork. Israel default display **only if configured for Israel**: monthly gross NIS for 100% employment, base salary, with other compensation separate.
5. **Deduplicate & score quality** — Avoid counting reposts, syndicated salary tables, mirrored data or duplicate employer submissions multiple times. Flag self-reported, unverifiable, small-sample, selection-biased, historical, and incomparable observations. Track sample counts and effective independent evidence.
6. **Retrieve comparable jobs** — Use structured hard constraints first (region/country, role family, level, pay basis, employment type), then semantic embeddings to rank genuine responsibility/skill similarity. Explain all relaxations and prevent inappropriate job-family mixing. Apply transparent relevance/recency weighting (weights learned or validated, not invented as proven effects).
7. **Estimate** — If an employer-disclosed range exists, label and present it as `advertised`, not as a model prediction. If sufficient comparable observations exist, calculate weighted empirical P25/P50/P75 with an auditable method and document sample size, weighting, and assumptions. P25–P75 is the central 50% of the comparable distribution, **not** a confidence interval or employer offer prediction interval. For an actual predictive interval, fit and empirically calibrate on held-out *realized offers* (e.g., conformal methods), reporting target coverage and observed coverage. Avoid fake precision: round amounts appropriately. With inadequate evidence, abstain or provide a clearly labeled broad indicative survey range without exact point estimate.
8. **Assess evidence quality** — Display discrete levels `high / medium / low / insufficient`, determined by documented signals: independent observations, source reliability, source age, role/locale match, dispersion, and data completeness. Do not turn this into a numerical probability without out-of-sample calibration. A source being high quality does not alone guarantee a tight forecast.
9. **Render transparently** — In the job card, show display basis (currency, gross/base, period), `advertised` or `estimated`, P25–P75 market range, P50 if defensible, evidence quality, last refreshed date, and a drilldown of source links, dates, sample counts, normalization and exclusions. If employer estimate is uncalibrated, explicitly state `employer offer not reliably predictable`. Where data are insufficient, show `insufficient verified salary data`, not fabricated values.
10. **Learn & evaluate** — Where explicitly permitted, collect real-world offered base and total compensation for later comparison with predictions, respecting privacy and retention. Store predictions immutable with model version, evidence IDs and timestamp for prospective evaluation. Evaluate MAE/median AE by role, region and seniority; calibration and interval coverage (for predictive intervals); bias, drift, missingness, and freshness. Compare against simple baseline(s). Avoid leakage between training and held-out evaluations. Do not retrain automatically without approval.

## Decision tree

- **The exact posting states salary:** show employer-advertised value distinctly; validate pay period/currency and whether base or total.
- **Comparable, authorized, independently sourced observations are enough:** compute explainable percentiles, display sample quality and origin.
- **Only broad surveys exist:** show a labeled survey-based indicative range with reduced confidence; do not imply employer specificity.
- **Little or conflicting evidence exists:** abstain, show missing-data reason and suggest which evidence would improve coverage.
- **User requests an employer-offer prediction:** require past realized offers with comparable employers/roles; otherwise explain that only market salary can be estimated.
- **User requests personalized salary:** require informed consent and only relevant profile factors; do not use protected traits or infer them as pay determinants.

## Data contract (adapt names to existing schema)

Recommended additive fields, not instructions to migrate automatically:

```json
{
  "job_id": "string",
  "estimate_type": "advertised|market_estimate|employer_offer_prediction|indicative_survey|insufficient_data",
  "currency": "ISO-4217",
  "pay_period": "month|year|hour",
  "compensation_basis": "gross_base|gross_total|net|unknown",
  "employment_fraction": 1.0,
  "location_scope": "string|null",
  "p25": null,
  "p50": null,
  "p75": null,
  "advertised_min": null,
  "advertised_max": null,
  "quality_level": "high|medium|low|insufficient",
  "quality_reasons": [],
  "independent_observations": 0,
  "sources": [{"source_id":"string","url":"string|null","observed_at":"ISO-8601","license_status":"verified|unknown"}],
  "estimated_at": "ISO-8601",
  "model_version": "string",
  "assumptions": [],
  "limitations": []
}
```

Keep `null` for unmeasured quantiles; never insert example salaries into production. The example schema is not a demand to change existing types. Model employers' declared salary bands separately from market percentiles.

## Source policy and freshness

Maintain an approved-source registry with URL/provider, source type, license/terms verification, access method, source update date, retrieval timestamp, geographic and role coverage, compensation basis, and estimated independence from other sources. Set configurable staleness thresholds by market segment; mark stale observations, do not silently treat them as current. If upstream sources disagree substantially, expose dispersion instead of hiding it through averaging. Never claim a source has a public API without checking current documentation.

## Testing and acceptance criteria

Create tests **after approval** and align with the repository's test stack:

- Correct salary normalization across annual/monthly/hourly and full-time fraction; no accidental equity/bonus aggregation into base.
- Differentiates stated salary from model-estimated salary.
- No cross-country, cross-currency, cross-role or seniority blending without explicit defensible conversion/relaxation.
- Missing values, stale sources, duplicates, conflicting evidence, low sample sizes and API failures never produce made-up salary values.
- Quantile calculation, sample count, provenance and score explanation reproduce deterministically from fixed fixtures.
- Boundary cases: remote jobs, contractor roles, part-time, unusually broad job titles, salary bands without pay basis, and data with contradictory pay units.
- UI clearly labels ranges, currency, gross/base/total, period, source count, date and evidence quality.
- Privacy/security and licensing checks are enforced; errors and logs do not expose secrets or personal salary submissions.
- Backtesting uses chronological holdout with documented MAE and, when applicable, interval coverage; no promise of precision before validation.

## Suggested phased implementation

**Phase 0 — Audit:** Identify current prediction logic, data model, data acquisition and UI. Deliver gap analysis, source/legal availability matrix, baseline error measurement plan and low-risk rollout design.

**Phase 1 — Evidence MVP:** Approved data connectors; normalization, deduplication, source registry and immutable provenance; separate advertised range vs estimated range; explicit abstention.

**Phase 2 — Similarity & explainability:** Comparable-job retrieval, empirical P25/P50/P75, evidence-quality classification, explanations and user-facing drilldown.

**Phase 3 — Calibration:** Opt-in realized-offer feedback, longitudinal metrics, offline baseline comparison, calibrated predictive intervals where eligible, drift checks.

**Phase 4 — Controlled rollout:** Feature flag, shadow evaluation, monitored phased release and rollback. Approval required before changing production systems or turning on autonomous collection/retraining.

## Communication format when triggered

First return: (1) what exists in the repository versus what remains unknown, (2) a prioritized gap analysis, (3) which sources are legitimately accessible, (4) a proposed architecture compatible with the existing stack, (5) schema/API/UI impact, (6) test and validation plan, (7) explicit approval request for proposed edits. Clearly separate **verified findings**, **assumptions**, and **recommendations**. Do not claim the skill has been integrated simply because the file was drafted.

## Definition of done

For approved work: no fabricated salary values; explainable observation-level provenance; advertised and estimated ranges distinctly labeled; validated normalization and filtering; graceful abstention; reproducible tests; observed out-of-sample performance reported without inflated confidence; no global skill installation; no unapproved production changes.
