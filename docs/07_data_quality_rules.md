# Data Quality Rules — Denial Prevention Simulator

Severity: **Critical** blocks the record from reporting. **High** stays in reporting but is
flagged. **Medium** and **Low** are logged for correction.

| Rule | Check | Severity | Action | Owner |
|---|---|---|---|---|
| DQ-01 | `Claim_ID` unique in the reporting layer | High | Keep first, log duplicate | Data Steward |
| DQ-02 | Denied claims carry a denial reason code | Critical | Exclude, return to billing | Billing Manager |
| DQ-03 | `Denied_Amount` does not exceed `Claim_Amount` | Critical | Exclude | Billing Manager |
| DQ-04 | `Claim_Amount` is greater than zero | Critical | Exclude | Billing Manager |
| DQ-05 | `Submission_Date` is on or after `Service_Date` | Critical | Exclude | Billing Manager |
| DQ-06 | `Claim_Status` is Paid, Denied, or In Process | Medium | Standardize case, log unmappable | Billing Manager |
| DQ-07 | `Claim_Status` agrees with `Denial_Flag` | High | Flag for correction | Billing Manager |
| DQ-08 | `Payer_ID` exists in `dim_payer` | High | Trim and upper-case, then log | Data Steward |
| DQ-09 | `Denial_Reason_Code` exists in `dim_denial_reason` | High | Log; preventable classification cannot be derived without it | Payer Relations |
| DQ-10 | `Recovery_Amount` does not exceed `Denied_Amount` | Critical | Exclude | Denial Analyst |

Specified but not yet automated:

| Rule | Check | Severity |
|---|---|---|
| DQ-11 | Every denied claim has a work queue assigned | Medium |
| DQ-12 | Resubmitted claims have a resubmission date | Medium |
| DQ-13 | Reporting layer refresh is under 24 hours old | High |

## Data Quality Score

```
Data Quality Score = records with no rule failure / records in extract x 100
```

Last run: 99.51% (12,014 records in, 59 distinct records with at least one failure).
Displayed with the blocked-record count so the two always reconcile.
