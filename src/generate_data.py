"""
Synthetic claims dataset for Northbridge Medical Group (fictional org).

The goal is a claims file where denials are *caused* by upstream control
failures rather than assigned at random, so a pre-submission risk score
has something real to detect.

Run:  python src/generate_data.py
"""

import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

SEED = 411
N_CLAIMS = 12000
START = date(2026, 1, 1)
END = date(2026, 8, 31)
RAW = os.path.join("data", "raw")

PAYERS = [
    # id, name, type, share, how strict they are about auth (multiplier)
    ("PAY-01", "Trinity Health Plan", "Commercial", 0.20, 1.0),
    ("PAY-02", "Brazos Valley Benefits", "Commercial", 0.16, 0.8),
    ("PAY-03", "Statewide Medicaid MCO", "Medicaid", 0.18, 1.4),
    ("PAY-04", "Silver Ridge Advantage", "Medicare Advantage", 0.17, 1.6),
    ("PAY-05", "Cottonwood Mutual", "Commercial", 0.12, 0.9),
    ("PAY-06", "Panhandle Care Partners", "Medicaid", 0.10, 1.3),
    ("PAY-07", "Meridian Select", "Commercial", 0.07, 1.1),
]

# service line, procedure group, share, typical charge, auth usually required
SERVICES = [
    ("Imaging", "Advanced Imaging", 0.13, 1850, True),
    ("Imaging", "Routine Imaging", 0.11, 420, False),
    ("Surgery", "Outpatient Surgery", 0.09, 7400, True),
    ("Surgery", "Inpatient Surgery", 0.04, 21500, True),
    ("Cardiology", "Diagnostic Cardiology", 0.08, 2300, True),
    ("Orthopedics", "Joint Injection", 0.07, 980, True),
    ("Primary Care", "Office Visit", 0.18, 185, False),
    ("Behavioral Health", "Therapy Session", 0.08, 220, False),
    ("Oncology", "Infusion Therapy", 0.05, 9800, True),
    ("Lab", "Routine Lab", 0.10, 95, False),
    ("Physical Therapy", "PT Course", 0.07, 310, True),
]

DENIAL_REASONS = [
    ("AUTH-01", "No prior authorization on file", "Authorization", True),
    ("AUTH-02", "Authorization expired or mismatched", "Authorization", True),
    ("ELIG-01", "Member not eligible on date of service", "Eligibility", True),
    ("ELIG-02", "Coordination of benefits unresolved", "Eligibility", True),
    ("DOC-01", "Medical necessity not documented", "Documentation", True),
    ("DOC-02", "Records not submitted with claim", "Documentation", True),
    ("COD-01", "Invalid or unbundled code combination", "Coding", True),
    ("COD-02", "Modifier missing or invalid", "Coding", True),
    ("TF-01", "Timely filing limit exceeded", "Timely Filing", True),
    ("CON-01", "Non-covered benefit under plan", "Coverage", False),
    ("CON-02", "Service not medically necessary per policy", "Coverage", False),
    ("DUP-01", "Duplicate claim", "Duplicate", True),
]

WORK_QUEUES = {
    "Authorization": "Authorization Review",
    "Eligibility": "Eligibility Review",
    "Documentation": "Clinical Documentation",
    "Coding": "Coding Review",
    "Timely Filing": "Billing Escalation",
    "Coverage": "Payer Relations",
    "Duplicate": "Billing Intake",
}

PREVENTION_RULES = [
    ("PR-01", "Authorization_Present = No and auth required", "Hold claim, verify authorization", "Authorization team", "AUTH-01"),
    ("PR-02", "Eligibility_Verified = No", "Verify active coverage for the date of service", "Billing intake", "ELIG-01"),
    ("PR-03", "Documentation_Complete = No", "Request missing clinical documentation", "Clinical documentation", "DOC-01"),
    ("PR-04", "Coding_Validation_Passed = No", "Route to coding review before submission", "Coding team", "COD-01"),
    ("PR-05", "Days_To_Submit > 20", "Expedite submission review", "Billing supervisor", "TF-01"),
]


def pick(options):
    return random.choices([o[0] for o in options], weights=[o[1] for o in options], k=1)[0]


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    os.makedirs(RAW, exist_ok=True)

    payer_share = [(p[0], p[3]) for p in PAYERS]
    payer_strict = {p[0]: p[4] for p in PAYERS}
    svc_share = [(i, s[2]) for i, s in enumerate(SERVICES)]

    rows = []
    span = (END - START).days

    for i in range(1, N_CLAIMS + 1):
        claim_id = f"CLM-2026-{i:06d}"
        service_date = START + timedelta(days=random.randint(0, span))
        payer_id = pick(payer_share)
        si = pick(svc_share)
        service_line, proc_group, _, base_charge, auth_required = SERVICES[si]

        # charge varies around the typical amount
        charge = round(float(np.random.lognormal(np.log(base_charge), 0.35)), 2)

        days_to_submit = int(np.random.gamma(shape=2.0, scale=4.0)) + 1
        if random.random() < 0.05:
            days_to_submit += random.randint(20, 70)  # the stragglers
        submission_date = service_date + timedelta(days=days_to_submit)

        # ---- control failures upstream of the claim ----
        auth_present = True
        if auth_required:
            miss_p = 0.14 * payer_strict[payer_id]
            auth_present = random.random() > min(miss_p, 0.45)

        elig_verified = random.random() > (0.07 if payer_id not in ("PAY-03", "PAY-06") else 0.13)
        doc_complete = random.random() > (0.12 if service_line in ("Surgery", "Oncology", "Cardiology") else 0.08)
        coding_passed = random.random() > (0.09 if proc_group in ("Outpatient Surgery", "Inpatient Surgery", "Advanced Imaging") else 0.05)

        if days_to_submit > 60:
            tf_risk = "High"
        elif days_to_submit > 20:
            tf_risk = "Medium"
        else:
            tf_risk = "Low"

        # ---- denial probability driven by the failures above ----
        p = 0.02
        reason = None
        if auth_required and not auth_present:
            p += 0.26 * payer_strict[payer_id] / 1.2
            reason = "AUTH-01"
        if not elig_verified:
            p += 0.20
            reason = reason or "ELIG-01"
        if not doc_complete:
            p += 0.15
            reason = reason or "DOC-01"
        if not coding_passed:
            p += 0.13
            reason = reason or "COD-01"
        if tf_risk == "High":
            p += 0.28
            reason = "TF-01"
        elif tf_risk == "Medium":
            p += 0.07

        denied_by_control = random.random() < min(p, 0.93)

        # denials no pre-submission control would have caught: plan coverage,
        # policy determinations, duplicates created downstream
        denied_other = random.random() < 0.05

        denied = denied_by_control or denied_other
        if denied and not denied_by_control:
            reason = None

        if denied and reason is None:
            # denials that no pre-submission control would have caught
            reason = random.choices(
                ["CON-01", "CON-02", "DUP-01", "AUTH-02", "ELIG-02", "DOC-02", "COD-02"],
                weights=[0.26, 0.22, 0.12, 0.10, 0.10, 0.10, 0.10],
            )[0]

        reason_meta = {r[0]: r for r in DENIAL_REASONS}

        if denied:
            status = "Denied"
            denied_amount = charge
            category = reason_meta[reason][2]
            preventable = reason_meta[reason][3]
            work_queue = WORK_QUEUES[category]

            resubmitted = random.random() < (0.72 if preventable else 0.38)
            if resubmitted:
                recovery_rate = random.uniform(0.45, 0.95) if preventable else random.uniform(0.10, 0.45)
                recovery = round(denied_amount * recovery_rate, 2)
            else:
                recovery = 0.0
            days_outstanding = int(np.random.gamma(shape=2.5, scale=14)) + 5
        else:
            status = random.choices(["Paid", "In Process"], weights=[0.93, 0.07])[0]
            denied_amount = 0.0
            reason = None
            preventable = False
            work_queue = None
            resubmitted = False
            recovery = 0.0
            days_outstanding = int(np.random.gamma(shape=2.0, scale=9)) + 2

        rows.append(
            {
                "Claim_ID": claim_id,
                "Service_Date": service_date,
                "Submission_Date": submission_date,
                "Payer_ID": payer_id,
                "Service_Line": service_line,
                "Procedure_Group": proc_group,
                "Claim_Amount": charge,
                "Denied_Amount": denied_amount,
                "Claim_Status": status,
                "Denial_Flag": "Yes" if denied else "No",
                "Denial_Reason_Code": reason,
                "Auth_Required": "Yes" if auth_required else "No",
                "Authorization_Present": "Yes" if auth_present else "No",
                "Eligibility_Verified": "Yes" if elig_verified else "No",
                "Documentation_Complete": "Yes" if doc_complete else "No",
                "Coding_Validation_Passed": "Yes" if coding_passed else "No",
                "Timely_Filing_Risk": tf_risk,
                "Days_To_Submit": days_to_submit,
                "Resubmission_Flag": "Yes" if resubmitted else "No",
                "Recovery_Amount": recovery,
                "Days_Outstanding": days_outstanding,
                "Work_Queue": work_queue,
                "Preventable_Flag": "Yes" if (denied and preventable) else "No",
            }
        )

    claims = pd.DataFrame(rows)

    # a pipeline of not-yet-submitted claims, which is what the risk queue works on
    pending = []
    for i in range(1, 901):
        service_date = END + timedelta(days=random.randint(-10, 3))
        payer_id = pick(payer_share)
        si = pick(svc_share)
        service_line, proc_group, _, base_charge, auth_required = SERVICES[si]
        charge = round(float(np.random.lognormal(np.log(base_charge), 0.35)), 2)
        days_held = random.randint(0, 34)
        pending.append(
            {
                "Claim_ID": f"CLM-2026-P{i:05d}",
                "Service_Date": service_date,
                "Payer_ID": payer_id,
                "Service_Line": service_line,
                "Procedure_Group": proc_group,
                "Claim_Amount": charge,
                "Auth_Required": "Yes" if auth_required else "No",
                "Authorization_Present": "Yes" if (not auth_required or random.random() > 0.18) else "No",
                "Eligibility_Verified": "Yes" if random.random() > 0.10 else "No",
                "Documentation_Complete": "Yes" if random.random() > 0.11 else "No",
                "Coding_Validation_Passed": "Yes" if random.random() > 0.07 else "No",
                "Days_To_Submit": days_held,
                "Claim_Status": "Not Submitted",
            }
        )
    pending = pd.DataFrame(pending)

    dim_payer = pd.DataFrame([(p[0], p[1], p[2]) for p in PAYERS],
                             columns=["Payer_ID", "Payer_Name", "Payer_Type"])
    dim_reason = pd.DataFrame(
        [(r[0], r[1], r[2], "Yes" if r[3] else "No") for r in DENIAL_REASONS],
        columns=["Denial_Reason_Code", "Reason_Description", "Reason_Category", "Preventable"],
    )
    dim_service = pd.DataFrame(
        [(s[0], s[1], "Yes" if s[4] else "No") for s in SERVICES],
        columns=["Service_Line", "Procedure_Group", "Auth_Typically_Required"],
    ).drop_duplicates()
    rules = pd.DataFrame(PREVENTION_RULES,
                         columns=["Rule_ID", "Trigger", "Prevention_Action", "Owner", "Linked_Denial_Reason"])

    days = pd.date_range(START, END + timedelta(days=120), freq="D")
    dim_date = pd.DataFrame({"Date_Key": days.date, "Year": days.year,
                             "Month_Num": days.month, "Month_Name": days.strftime("%b"),
                             "Quarter": "Q" + days.quarter.astype(str)})

    # light dirt so the validation step is not decorative
    dirty = pd.concat([claims, claims.sample(14, random_state=5)], ignore_index=True)
    idx = dirty.sample(20, random_state=6).index
    dirty.loc[idx, "Payer_ID"] = dirty.loc[idx, "Payer_ID"].str.lower()
    idx = dirty.sample(18, random_state=8).index
    dirty.loc[idx, "Claim_Status"] = "DENIED"
    bad = dirty[dirty["Denial_Flag"] == "Yes"].sample(15, random_state=9).index
    dirty.loc[bad, "Denial_Reason_Code"] = None
    bad = dirty.sample(10, random_state=10).index
    dirty.loc[bad, "Submission_Date"] = dirty.loc[bad, "Service_Date"] - pd.to_timedelta(3, unit="D")
    bad = dirty.sample(8, random_state=12).index
    dirty.loc[bad, "Claim_Amount"] = -dirty.loc[bad, "Claim_Amount"]
    dirty = dirty.sample(frac=1, random_state=2).reset_index(drop=True)

    dirty.to_csv(os.path.join(RAW, "claims_fact_raw.csv"), index=False)
    pending.to_csv(os.path.join(RAW, "pending_claims.csv"), index=False)
    dim_payer.to_csv(os.path.join(RAW, "dim_payer.csv"), index=False)
    dim_reason.to_csv(os.path.join(RAW, "dim_denial_reason.csv"), index=False)
    dim_service.to_csv(os.path.join(RAW, "dim_service_line.csv"), index=False)
    dim_date.to_csv(os.path.join(RAW, "dim_date.csv"), index=False)
    rules.to_csv(os.path.join(RAW, "prevention_rules.csv"), index=False)

    with pd.ExcelWriter(os.path.join(RAW, "04_synthetic_raw_data.xlsx")) as xl:
        dirty.to_excel(xl, sheet_name="claims_fact", index=False)
        pending.to_excel(xl, sheet_name="pending_claims", index=False)
        dim_payer.to_excel(xl, sheet_name="dim_payer", index=False)
        dim_reason.to_excel(xl, sheet_name="dim_denial_reason", index=False)
        rules.to_excel(xl, sheet_name="prevention_rules", index=False)

    print(f"claims: {len(dirty)}  pending: {len(pending)}")
    print(f"denial rate: {(claims['Denial_Flag'] == 'Yes').mean():.1%}")
    print(f"preventable share of denials: {(claims.loc[claims['Denial_Flag'] == 'Yes', 'Preventable_Flag'] == 'Yes').mean():.1%}")


if __name__ == "__main__":
    main()
