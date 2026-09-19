# Data Dictionary — Denial Prevention Simulator

## claims_fact — one row per submitted claim

| Field | Type | Definition | Allowed values | Required | Example | Quality rule | Owner |
|---|---|---|---|---|---|---|---|
| Claim_ID | text | Unique claim identifier | `CLM-YYYY-######` | Yes | CLM-2026-000001 | DQ-01 | Billing Manager |
| Service_Date | date | Date of service | — | Yes | 2026-03-01 | DQ-05 | Billing Manager |
| Submission_Date | date | Date claim was submitted to the payer | ≥ Service_Date | Yes | 2026-03-04 | DQ-05 | Billing Manager |
| Payer_ID | text | Payer key | must exist in dim_payer | Yes | PAY-04 | DQ-08 | Data Steward |
| Service_Line | text | Clinical service line | reference list | Yes | Imaging | reference | Revenue Cycle Director |
| Procedure_Group | text | Procedure grouping within the service line | reference list | Yes | Advanced Imaging | reference | Coding Lead |
| Claim_Amount | decimal | Billed charge | > 0 | Yes | 1850.00 | DQ-04 | Billing Manager |
| Denied_Amount | decimal | Amount denied | 0 ≤ value ≤ Claim_Amount | Yes | 1850.00 | DQ-03 | Billing Manager |
| Claim_Status | text | Current claim state | Paid, Denied, In Process | Yes | Denied | DQ-06, DQ-07 | Billing Manager |
| Denial_Flag | text | Whether the claim was denied | Yes, No | Yes | Yes | DQ-07 | Billing Manager |
| Denial_Reason_Code | text | Primary denial reason | must exist in dim_denial_reason | If denied | AUTH-01 | DQ-02, DQ-09 | Payer Relations |
| Auth_Required | text | Authorization required for this procedure group | Yes, No | Yes | Yes | reference | Authorization Lead |
| Authorization_Present | text | Authorization on file at submission | Yes, No | Yes | No | — | Authorization Lead |
| Eligibility_Verified | text | Coverage verified for the date of service | Yes, No | Yes | Yes | — | Billing Intake |
| Documentation_Complete | text | Clinical documentation complete at submission | Yes, No | Yes | No | — | Clinical Documentation |
| Coding_Validation_Passed | text | Passed the code edit check | Yes, No | Yes | Yes | — | Coding Lead |
| Timely_Filing_Risk | text | Filing risk band derived from Days_To_Submit | Low ≤20, Medium 21-60, High >60 | Yes | High | derived | Billing Supervisor |
| Days_To_Submit | integer | Submission_Date minus Service_Date | ≥ 0 | Yes | 3 | DQ-05 | Billing Manager |
| Resubmission_Flag | text | Claim was corrected and resubmitted | Yes, No | Yes | Yes | — | Denial Analyst |
| Recovery_Amount | decimal | Amount recovered after resubmission or appeal | 0 ≤ value ≤ Denied_Amount | Yes | 1250.00 | DQ-10 | Denial Analyst |
| Days_Outstanding | integer | Days the balance has been open | ≥ 0 | Yes | 46 | — | Denial Analyst |
| Work_Queue | text | Queue the denial was routed to | derived from reason category | If denied | Authorization Review | — | Billing Manager |
| Preventable_Flag | text | Denial reason maps to a pre-submission control | Yes, No | Yes | Yes | DQ-09 | Revenue Cycle Director |

### Derived by `clean_and_score.py`

| Field | Definition |
|---|---|
| Preventable_Risk_Score | 30 auth + 20 eligibility + 20 documentation + 15 coding + 15 filing risk |
| Risk_Band | Low 0-14, Medium 15-29, High 30+ |
| Recovery_Priority_Score | 0.45 denied-dollar index + 0.30 recovery likelihood + 0.15 filing urgency + 0.10 age risk. Null for non-denied claims |
| Prevention_Opportunity | Denied_Amount x preventable probability (0.8 when preventable, else 0) |

## pre_submission_queue — one row per unsubmitted claim

Same control fields as `claims_fact`, plus:

| Field | Definition |
|---|---|
| Triggered_Rules | Semicolon-separated prevention rule IDs that fired |
| Primary_Owner | Owner of the first triggered rule |
| At_Risk_Amount | Claim_Amount when Risk_Band is High, else 0 |
| Days_To_Submit | Days the claim has been held since service |

## dim_denial_reason

| Field | Definition |
|---|---|
| Denial_Reason_Code | Primary key, e.g. AUTH-01 |
| Reason_Description | Plain-language reason |
| Reason_Category | Authorization, Eligibility, Documentation, Coding, Timely Filing, Coverage, Duplicate |
| Preventable | Yes when a pre-submission control could have caught it |

## prevention_rules

| Field | Definition |
|---|---|
| Rule_ID | Primary key, PR-## |
| Trigger | Condition that fires the rule |
| Prevention_Action | What the owner must do |
| Owner | Accountable team |
| Linked_Denial_Reason | Denial reason the rule is intended to prevent |

## dim_payer / dim_service_line / dim_date

| Table | Fields |
|---|---|
| dim_payer | Payer_ID, Payer_Name, Payer_Type |
| dim_service_line | Service_Line, Procedure_Group, Auth_Typically_Required |
| dim_date | Date_Key, Year, Month_Num, Month_Name, Quarter |

## dq_exceptions

Exception_ID, Rule_ID, Record_ID, Severity, Description, Owner, Status.
