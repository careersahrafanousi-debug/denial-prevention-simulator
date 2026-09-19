# Project Charter — Denial Prevention Simulator

**Project name:** Denial Prevention Simulator
**Organization:** Northbridge Medical Group (fictional)
**Prepared by:** Business analyst / revenue cycle analyst
**Date:** 2026-02-02
**Status:** Prototype, portfolio build

## Problem statement

Northbridge Medical Group denies-and-reacts. Roughly 14% of claims are denied, and the
revenue cycle team learns about each one when the remittance arrives. Denial reporting lists
top reasons after the fact, which tells staff what to appeal but never changes what gets
submitted. No one can quantify how much of the denied balance was preventable before
submission, and no one can see which unsubmitted claims are about to fail.

## Goal

Shift the decision point earlier. Produce a transparent pre-submission risk score, a rule
set that maps every failure to a named owner and action, and a recovery priority score so
the existing denial inventory is worked in value order.

## Objectives

1. Quantify the preventable share of denied dollars, by reason and by payer.
2. Score unsubmitted claims and route them by risk band.
3. Tie each risk factor to a prevention rule with an accountable owner.
4. Rank open denied claims by recoverable value rather than age.
5. Model avoided exposure at several intercept coverage levels without asserting savings.

## Users

| User | Primary use |
|---|---|
| Revenue cycle director | Denial rate, denied dollars, preventable share, monthly trend |
| Billing manager | Pre-submission risk queue and daily workload |
| Coding lead | Claims failing code validation |
| Authorization staff | Claims held for authorization |
| Payer relations | Payer and reason concentration |
| Analyst | Score logic, rule thresholds, data-quality exceptions |

## Success measures

| Measure | Baseline (modeled) | Target direction |
|---|---|---|
| Denial rate | 14.0% | Decrease |
| Preventable denial rate | 76.6% of denials by count | Decrease |
| Denied dollars | $5.42M over 8 months | Decrease |
| First-pass acceptance | 80.0% | Increase |
| Priority-worked rate (denials worked in priority order) | Not currently measured | Establish, then increase |
| Data Quality Score | 99.51% | Maintain above 99% |

## Scope

**In scope:** professional and outpatient claims, service dates 2026-01-01 to 2026-08-31;
unsubmitted claim pipeline; pre-submission controls; denial reasons; resubmission and
recovery; reporting layer.

**Out of scope:** payer contract modeling, fee schedules, patient responsibility,
collections, clinical coding accuracy review, EHR configuration.

## Assumptions

- One primary denial reason per claim.
- Authorization requirement is determined by procedure group.
- Preventability is defined by whether a denial reason maps to a pre-submission control.
- Recovery likelihood is a stated assumption (75% preventable, 30% non-preventable), pending
  validation against historical appeal outcomes.
- No production or patient data is used.

## Constraints

- Scores must remain additive and explainable to non-technical staff.
- Rule thresholds must be configurable without code changes.
- Pipeline must run without a server database.

## Risks

| Risk | Mitigation |
|---|---|
| Modeled avoided exposure quoted as realized savings | Every figure labelled modeled; assumptions stated alongside |
| Prevention program judged on total denial rate, including coverage denials it cannot affect | Preventable and non-preventable reported separately |
| Hard holds create submission backlogs | Exception queues have named owners and are monitored for aging |
| Score weights mistaken for a fitted model | Documented as stated weights; logistic regression named as the next step |

## Deliverables

Charter, business requirements with user stories, data dictionary, synthetic dataset,
cleaning and scoring pipeline with exception log, SQL analysis library covering 14 questions,
prevention rule table, data-quality rule set, as-is and to-be process maps, dashboard
specification, UAT test cases, executive summary.
