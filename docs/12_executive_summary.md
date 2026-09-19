# Executive Summary — Denial Prevention Simulator

**Northbridge Medical Group (fictional) | Prepared by the revenue cycle analyst | 2026-08-31**

## Why this was done

Northbridge works denials after the money is already gone. Denial reporting names last
month's top reasons, which helps staff appeal but never changes what gets submitted. The
question this analysis set out to answer was narrower and more useful: how much of the denied
balance could a check before submission have prevented, and which claims sitting in the
pipeline right now are about to fail.

## What the data shows

**1. Most denied dollars were preventable at the front end.**
Of $5.42M denied across 11,967 claims, $4.48M carried a reason that maps to one of five
pre-submission controls. Authorization alone is $1.96M.

**2. There is a hard ceiling on what prevention can do.**
$935K of denied dollars came from plan coverage and policy determinations — the second
largest category and not preventable by any front-end check. Measuring a prevention program
on total denial rate will make it look like it is failing.

**3. Risk is visible before submission.**
The additive risk score produced denial rates of 7.8% (Low), 22.9% (Medium), and 37.8%
(High). No modeling sophistication was required; five yes/no checks separate the population.

**4. Late submission is close to a coin flip.**
Claims flagged high timely-filing risk denied at 45.7% against 13.0% for low risk. Only 197
claims, but this is entirely self-inflicted and the cheapest thing on the list to fix.

**5. Denied dollars concentrate where volume does not.**
Surgery is 13% of claims and 64% of denied dollars. Any denial report ranked by claim count
hides this completely.

**6. The next wave is already in the queue.**
104 of 900 unsubmitted claims score High risk, carrying $505K in charges — about $191K of
modeled denied exposure, most of it missing authorization on surgical and oncology claims.

## Recommendations

| Priority | Action | Why |
|---|---|---|
| 1 | Hard hold on claims requiring authorization without one (PR-01) | Largest preventable bucket, simplest check |
| 2 | 20-day submission alert to the billing supervisor (PR-05) | 379 pending claims, $908K, highest-volume rule |
| 3 | Route by risk band: Low auto-submits, Medium checklist, High to an owner | Puts staff time where denial probability is |
| 4 | Work denials by recovery priority instead of date received | High-value recoverable claims currently age behind $95 lab denials |
| 5 | Report preventable and non-preventable denials separately | Protects the program from being judged on coverage denials |
| 6 | Recalibrate rule thresholds monthly against outcomes | Static edit rules decay and get switched off |

## Modeled opportunity, not savings

| Intercept coverage | Modeled avoided exposure |
|---|---|
| 50% | $95,275 |
| 70% | $133,386 |
| 90% | $171,496 |

These figures assume the intercept resolves the underlying gap and that intercepted claims
would have denied at the historical High-risk rate of 37.8%. Neither assumption is validated.
No savings figure should be quoted externally until both are tested against production data
over a defined baseline period.

## Next steps

1. Validate the preventable classification of each denial reason with payer relations.
2. Refit the risk weights with a logistic regression on historical claims and compare
   separation against the current additive score.
3. Pilot PR-01 as a hard hold in one service line for 60 days, monitoring the exception queue
   for aging as well as the denial rate.
4. Build the recovery priority queue into daily work assignment and start measuring
   priority-worked rate, which is currently not measured at all.
