# UAT Test Cases — Denial Prevention Simulator

Environment: local build, synthetic dataset, seed 411.

| ID | Story | Test | Expected result | Result |
|---|---|---|---|---|
| UAT-01 | US-01 | Pre-submission queue contains only unsubmitted claims | 900 rows, all `Not Submitted` | Pass |
| UAT-02 | US-01 | Triggered rules match the field values on the row | Every PR-01 row has Auth_Required Yes and Authorization_Present No | Pass |
| UAT-03 | US-02 | Preventable split reconciles | Preventable $4.48M plus non-preventable $0.94M equals $5.42M total denied | Pass |
| UAT-04 | US-03 | Pareto cumulative share reaches 100% | Final row shows 100.0% | Pass |
| UAT-05 | US-04 | Authorization hold queue is complete | 85 pending claims, $457,540 held, owner Authorization team | Pass |
| UAT-06 | US-05 | Recovery queue excludes recovered claims | No row has Recovery_Amount greater than zero | Pass |
| UAT-07 | US-06 | Simulator scales linearly with coverage | $95,275 / $133,386 / $171,496 at 50 / 70 / 90 percent | Pass |
| UAT-08 | US-07 | Coding failure denial rate is filterable | Rate rises against the all-claims baseline of 14.0% | Pass |
| UAT-09 | US-08 | Filing threshold is configurable | Changing PR-05 from 20 to 15 days in the CSV changes queue size with no code edit | Pass |
| UAT-10 | US-09 | Data Quality Score matches the pipeline | Card and script both show 99.51% | Pass |
| UAT-11 | US-09 | Blocked records reconcile | 12,014 in minus 11,967 out equals 47, of which 33 blocked and 14 deduplicated | Pass |
| UAT-12 | US-10 | First-pass acceptance by month matches query 5 | Values match; monthly grain is submission date | Pass |

## Negative tests

| ID | Test | Expected result | Result |
|---|---|---|---|
| UAT-N1 | Denied claim with no reason code | Excluded, DQ-02 logged | Pass |
| UAT-N2 | Negative claim amount | Excluded, DQ-04 logged | Pass |
| UAT-N3 | Submission date before service date | Excluded, DQ-05 logged | Pass |
| UAT-N4 | Payer code in lower case | Standardized, joins successfully | Pass |
| UAT-N5 | Status Paid with Denial_Flag Yes | DQ-07 logged, record retained and flagged | Pass |
| UAT-N6 | Recovery amount above denied amount | Excluded, DQ-10 logged | Pass |

## Open defects

| ID | Description | Severity | Status |
|---|---|---|---|
| D-01 | Score treats each failure independently; combined failures may be worse than additive. Needs interaction testing on production data. | Medium | Open |
| D-02 | Recovery likelihood is a flat assumption rather than fitted from appeal outcomes. | Medium | Open |
| D-03 | One denial reason per claim; multi-reason remittances unsupported (FR-09). | Low | Deferred |
