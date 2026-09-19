-- Denial Prevention Simulator - analysis queries
-- Northbridge Medical Group (fictional org, fully synthetic data)
-- SQLite dialect.

--------------------------------------------------------------------
-- 1. Denial rate and denied dollars by payer
--------------------------------------------------------------------
SELECT p.Payer_Name,
       p.Payer_Type,
       COUNT(*)                                                            AS claims,
       ROUND(100.0 * SUM(CASE WHEN c.Denial_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                                AS denial_rate_pct,
       ROUND(SUM(c.Claim_Amount), 0)                                       AS billed,
       ROUND(SUM(c.Denied_Amount), 0)                                      AS denied_dollars
FROM claims_fact c
JOIN dim_payer p ON p.Payer_ID = c.Payer_ID
GROUP BY p.Payer_Name, p.Payer_Type
ORDER BY denial_rate_pct DESC;


--------------------------------------------------------------------
-- 2. Denial rate by service line and procedure group
--------------------------------------------------------------------
SELECT Service_Line,
       Procedure_Group,
       COUNT(*)                                                          AS claims,
       ROUND(100.0 * SUM(CASE WHEN Denial_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                              AS denial_rate_pct,
       ROUND(SUM(Denied_Amount), 0)                                      AS denied_dollars
FROM claims_fact
GROUP BY Service_Line, Procedure_Group
HAVING COUNT(*) >= 100
ORDER BY denied_dollars DESC;


--------------------------------------------------------------------
-- 3. Pareto of denied dollars by reason
-- Running share tells you how few reasons carry the money.
--------------------------------------------------------------------
WITH by_reason AS (
    SELECT r.Denial_Reason_Code,
           r.Reason_Description,
           r.Reason_Category,
           r.Preventable,
           SUM(c.Denied_Amount) AS denied_dollars
    FROM claims_fact c
    JOIN dim_denial_reason r ON r.Denial_Reason_Code = c.Denial_Reason_Code
    GROUP BY 1, 2, 3, 4
)
SELECT Denial_Reason_Code,
       Reason_Description,
       Reason_Category,
       Preventable,
       ROUND(denied_dollars, 0) AS denied_dollars,
       ROUND(100.0 * SUM(denied_dollars) OVER (ORDER BY denied_dollars DESC)
             / SUM(denied_dollars) OVER (), 1) AS running_share_pct
FROM by_reason
ORDER BY denied_dollars DESC;


--------------------------------------------------------------------
-- 4. Preventable vs non-preventable split
--------------------------------------------------------------------
SELECT Preventable_Flag,
       COUNT(*)                            AS denied_claims,
       ROUND(SUM(Denied_Amount), 0)        AS denied_dollars,
       ROUND(AVG(Denied_Amount), 0)        AS avg_denied,
       ROUND(SUM(Recovery_Amount), 0)      AS recovered
FROM claims_fact
WHERE Denial_Flag = 'Yes'
GROUP BY Preventable_Flag;


--------------------------------------------------------------------
-- 5. First-pass acceptance trend by submission month
--------------------------------------------------------------------
SELECT strftime('%Y-%m', Submission_Date) AS submission_month,
       COUNT(*)                            AS claims,
       ROUND(100.0 * SUM(CASE WHEN Claim_Status = 'Paid' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                AS first_pass_acceptance_pct,
       ROUND(100.0 * SUM(CASE WHEN Denial_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                AS denial_rate_pct
FROM claims_fact
GROUP BY submission_month
ORDER BY submission_month;


--------------------------------------------------------------------
-- 6. Does the risk score predict denials? (score validation)
--------------------------------------------------------------------
SELECT Risk_Band,
       COUNT(*)                                                          AS claims,
       ROUND(100.0 * SUM(CASE WHEN Denial_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                              AS denial_rate_pct,
       ROUND(SUM(Denied_Amount), 0)                                      AS denied_dollars
FROM claims_fact
GROUP BY Risk_Band
ORDER BY denial_rate_pct DESC;


--------------------------------------------------------------------
-- 7. Which combinations of control failures hurt most
--------------------------------------------------------------------
SELECT CASE WHEN Auth_Required = 'Yes' AND Authorization_Present = 'No'
            THEN 'auth missing; ' ELSE '' END ||
       CASE WHEN Eligibility_Verified = 'No'   THEN 'eligibility; '   ELSE '' END ||
       CASE WHEN Documentation_Complete = 'No' THEN 'documentation; ' ELSE '' END ||
       CASE WHEN Coding_Validation_Passed = 'No' THEN 'coding; '      ELSE '' END ||
       CASE WHEN Timely_Filing_Risk = 'High'   THEN 'filing risk'     ELSE '' END
           AS failure_combination,
       COUNT(*)                                                          AS claims,
       ROUND(100.0 * SUM(CASE WHEN Denial_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                              AS denial_rate_pct,
       ROUND(SUM(Denied_Amount), 0)                                      AS denied_dollars
FROM claims_fact
GROUP BY failure_combination
HAVING COUNT(*) >= 25
ORDER BY denial_rate_pct DESC
LIMIT 20;


--------------------------------------------------------------------
-- 8. Timely filing risk vs actual denial rate
--------------------------------------------------------------------
SELECT Timely_Filing_Risk,
       COUNT(*)                                                          AS claims,
       ROUND(AVG(Days_To_Submit), 1)                                     AS avg_days_to_submit,
       ROUND(100.0 * SUM(CASE WHEN Denial_Flag = 'Yes' THEN 1 ELSE 0 END)
             / COUNT(*), 1)                                              AS denial_rate_pct
FROM claims_fact
GROUP BY Timely_Filing_Risk
ORDER BY denial_rate_pct DESC;


--------------------------------------------------------------------
-- 9. Recovery opportunity by claim age
--------------------------------------------------------------------
SELECT CASE
           WHEN Days_Outstanding <= 30 THEN '0-30 days'
           WHEN Days_Outstanding <= 60 THEN '31-60 days'
           WHEN Days_Outstanding <= 90 THEN '61-90 days'
           ELSE '90+ days'
       END                                  AS age_bucket,
       COUNT(*)                             AS denied_claims,
       ROUND(SUM(Denied_Amount), 0)         AS denied_dollars,
       ROUND(SUM(Recovery_Amount), 0)       AS recovered,
       ROUND(AVG(Recovery_Priority_Score), 1) AS avg_priority
FROM claims_fact
WHERE Denial_Flag = 'Yes'
GROUP BY age_bucket
ORDER BY age_bucket;


--------------------------------------------------------------------
-- 10. Top 50 denied claims by recovery priority - the work queue
--------------------------------------------------------------------
SELECT c.Claim_ID,
       p.Payer_Name,
       c.Service_Line,
       r.Reason_Description,
       c.Preventable_Flag,
       ROUND(c.Denied_Amount, 0)             AS denied_amount,
       c.Days_Outstanding,
       c.Recovery_Priority_Score,
       c.Work_Queue
FROM claims_fact c
JOIN dim_payer p ON p.Payer_ID = c.Payer_ID
LEFT JOIN dim_denial_reason r ON r.Denial_Reason_Code = c.Denial_Reason_Code
WHERE c.Denial_Flag = 'Yes' AND c.Recovery_Amount = 0
ORDER BY c.Recovery_Priority_Score DESC
LIMIT 50;


--------------------------------------------------------------------
-- 11. Pre-submission risk queue with triggered rules
--------------------------------------------------------------------
SELECT q.Claim_ID,
       p.Payer_Name,
       q.Service_Line,
       q.Procedure_Group,
       ROUND(q.Claim_Amount, 0)  AS claim_amount,
       q.Preventable_Risk_Score,
       q.Risk_Band,
       q.Triggered_Rules,
       q.Primary_Owner,
       q.Days_To_Submit
FROM pre_submission_queue q
JOIN dim_payer p ON p.Payer_ID = q.Payer_ID
WHERE q.Risk_Band IN ('High', 'Medium')
ORDER BY q.Preventable_Risk_Score DESC, q.Claim_Amount DESC
LIMIT 60;


--------------------------------------------------------------------
-- 12. Workload by prevention rule - who has to act
--------------------------------------------------------------------
SELECT r.Rule_ID,
       r.Trigger,
       r.Owner,
       SUM(CASE WHEN q.Triggered_Rules LIKE '%' || r.Rule_ID || '%' THEN 1 ELSE 0 END) AS pending_claims,
       ROUND(SUM(CASE WHEN q.Triggered_Rules LIKE '%' || r.Rule_ID || '%'
                      THEN q.Claim_Amount ELSE 0 END), 0)                              AS dollars_held
FROM prevention_rules r
CROSS JOIN pre_submission_queue q
GROUP BY r.Rule_ID, r.Trigger, r.Owner
ORDER BY dollars_held DESC;


--------------------------------------------------------------------
-- 13. Control effectiveness simulation
-- If we intercept X% of high-risk claims before submission, what
-- denied exposure is avoided? Coverage levels 50 / 70 / 90 percent.
--------------------------------------------------------------------
WITH high_risk AS (
    SELECT SUM(Claim_Amount) AS at_risk_dollars, COUNT(*) AS claims
    FROM pre_submission_queue
    WHERE Risk_Band = 'High'
),
observed AS (
    -- how often high-risk claims actually got denied in the historical file
    SELECT 1.0 * SUM(CASE WHEN Denial_Flag = 'Yes' THEN 1 ELSE 0 END) / COUNT(*) AS denial_p
    FROM claims_fact
    WHERE Risk_Band = 'High'
)
SELECT cov.level                                                      AS coverage_pct,
       h.claims                                                       AS high_risk_claims,
       ROUND(h.at_risk_dollars, 0)                                    AS at_risk_dollars,
       ROUND(h.at_risk_dollars * o.denial_p, 0)                       AS modeled_denied_exposure,
       ROUND(h.at_risk_dollars * o.denial_p * cov.level / 100.0, 0)   AS modeled_avoided_exposure
FROM high_risk h
CROSS JOIN observed o
CROSS JOIN (SELECT 50 AS level UNION ALL SELECT 70 UNION ALL SELECT 90) cov
ORDER BY cov.level;


--------------------------------------------------------------------
-- 14. Data quality exceptions
--------------------------------------------------------------------
SELECT Rule_ID, Severity, COUNT(*) AS exceptions
FROM dq_exceptions
GROUP BY Rule_ID, Severity
ORDER BY exceptions DESC;
