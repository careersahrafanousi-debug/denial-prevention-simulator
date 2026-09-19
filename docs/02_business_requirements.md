# Business Requirements — Denial Prevention Simulator

## User stories

**US-01** As a billing manager, I want unsubmitted claims ranked by preventable denial risk
with the triggered rule and owner shown, so that staff know exactly what to fix before the
claim goes out.
*Acceptance:* queue includes only `Claim_Status = 'Not Submitted'`; each row shows score,
band, triggered rule IDs, primary owner, and charge amount; sortable by score and amount.

**US-02** As a revenue cycle director, I want denied dollars split into preventable and
non-preventable, so that the prevention program is measured on what it can actually control.
*Acceptance:* split sourced from `dim_denial_reason.Preventable`; both dollars and claim
counts shown; totals reconcile to overall denied dollars.

**US-03** As a payer relations lead, I want a Pareto of denied dollars by reason with a
running share, so that I know how few reasons carry the balance.
*Acceptance:* descending by denied dollars; cumulative share column; preventable flag visible.

**US-04** As an authorization supervisor, I want all claims held for missing authorization in
one list, so that my team works from a single queue.
*Acceptance:* filtered to PR-01 triggers; shows payer, procedure group, charge, days since
service.

**US-05** As a denial analyst, I want open denied claims ranked by recovery priority rather
than by date, so that the highest recoverable value is worked first.
*Acceptance:* excludes claims with recovery already received; shows the four score
components on drill-through; sortable.

**US-06** As a revenue cycle director, I want modeled avoided exposure at 50, 70 and 90
percent intercept coverage, so that I can size the opportunity before committing staff.
*Acceptance:* three scenarios displayed together; the denial probability used is visible on
the visual; the word "modeled" appears on the page.

**US-07** As a coding lead, I want denial rate by procedure group for claims that failed code
validation, so that I can target education.
*Acceptance:* filterable to `Coding_Validation_Passed = 'No'`; minimum volume threshold
applied to avoid tiny denominators.

**US-08** As a billing supervisor, I want claims more than 20 days from date of service
flagged, so that timely filing denials stop happening.
*Acceptance:* threshold configurable in `prevention_rules.csv`; shows days to submit and
payer filing limit category.

**US-09** As an analyst, I want a data-quality page with exceptions by rule and severity and
a reconciliation of rows in versus rows reported, so that the finance numbers are defensible.
*Acceptance:* Data Quality Score card; blocked record count ties to rows in minus rows out.

**US-10** As a revenue cycle director, I want first-pass acceptance by submission month, so
that I can see whether prevention work is moving the trend.
*Acceptance:* monthly grain on submission date; denial rate on the same axis.

## Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Risk score calculated for submitted and unsubmitted claims using identical logic | Must |
| FR-02 | Rule thresholds and owners stored as data, not code | Must |
| FR-03 | Preventable classification driven by the reason dimension | Must |
| FR-04 | Critical data-quality failures excluded from reporting and logged | Must |
| FR-05 | Recovery priority excludes already-recovered claims | Must |
| FR-06 | Simulation displays the probability assumption it uses | Must |
| FR-07 | Score components exposed at claim level | Should |
| FR-08 | Work queue assignment derived from the first triggered rule | Should |
| FR-09 | Multiple denial reasons per claim supported | Could (future) |
| FR-10 | Score refitted from outcomes on a scheduled basis | Could (future) |

## Non-functional requirements

- Full pipeline runs in under 90 seconds on a laptop.
- No identifiers beyond synthetic claim IDs.
- SQLite-compatible SQL with Postgres notes.
- Fixed seed for reproducibility.

## Traceability

| Story | Requirements | SQL query | Dashboard page | UAT |
|---|---|---|---|---|
| US-01 | FR-01, FR-02, FR-08 | 11 | Pre-Submission Risk Queue | UAT-01, UAT-02 |
| US-02 | FR-03 | 4 | Denial Root Causes | UAT-03 |
| US-03 | FR-03 | 3 | Denial Root Causes | UAT-04 |
| US-04 | FR-02, FR-08 | 11, 12 | Pre-Submission Risk Queue | UAT-05 |
| US-05 | FR-05, FR-07 | 10 | Recovery Prioritization | UAT-06 |
| US-06 | FR-06 | 13 | Control Effectiveness Simulator | UAT-07 |
| US-07 | — | 2, 7 | Denial Root Causes | UAT-08 |
| US-08 | FR-02 | 8 | Pre-Submission Risk Queue | UAT-09 |
| US-09 | FR-04 | 14 | Data Quality | UAT-10, UAT-11 |
| US-10 | — | 5 | Revenue Cycle Overview | UAT-12 |
