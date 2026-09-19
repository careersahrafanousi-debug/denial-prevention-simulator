"""
Cleans the claims extract, logs data-quality exceptions, and applies the three
scoring models: preventable denial risk, recovery priority, prevention opportunity.

Run after generate_data.py:  python src/clean_and_score.py
"""

import os

import numpy as np
import pandas as pd

RAW = os.path.join("data", "raw")
CLEAN = os.path.join("data", "clean")

VALID_STATUS = {"Paid", "Denied", "In Process"}
YN = ["Authorization_Present", "Eligibility_Verified", "Documentation_Complete",
      "Coding_Validation_Passed", "Denial_Flag", "Resubmission_Flag", "Preventable_Flag",
      "Auth_Required"]

exceptions = []


def log(rule, record, severity, desc):
    exceptions.append({"Exception_ID": f"EX-{len(exceptions)+1:05d}", "Rule_ID": rule,
                       "Record_ID": record, "Severity": severity, "Description": desc,
                       "Owner": "Revenue Cycle Analyst", "Status": "Open"})


def clean(df):
    df = df.copy()
    df["Payer_ID"] = df["Payer_ID"].astype(str).str.strip().str.upper()
    df["Claim_Status"] = df["Claim_Status"].astype(str).str.strip().str.title()
    for c in YN:
        df[c] = df[c].astype(str).str.strip().str.title().replace({"Y": "Yes", "N": "No"})
    for c in ["Service_Date", "Submission_Date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    # DQ-01 duplicates
    for cid in df[df.duplicated("Claim_ID", keep="first")]["Claim_ID"]:
        log("DQ-01", cid, "High", "Duplicate Claim_ID in extract")
    df = df.drop_duplicates("Claim_ID", keep="first")

    # DQ-02 denied claims need a reason code
    for cid in df[(df["Denial_Flag"] == "Yes") & (df["Denial_Reason_Code"].isna())]["Claim_ID"]:
        log("DQ-02", cid, "Critical", "Denied claim with no denial reason code")

    # DQ-03 denied amount cannot exceed the billed amount
    for cid in df[df["Denied_Amount"] > df["Claim_Amount"].abs()]["Claim_ID"]:
        log("DQ-03", cid, "Critical", "Denied amount exceeds claim amount")

    # DQ-04 charges must be positive
    for cid in df[df["Claim_Amount"] <= 0]["Claim_ID"]:
        log("DQ-04", cid, "Critical", "Claim amount is zero or negative")

    # DQ-05 submission cannot precede service
    for cid in df[df["Submission_Date"] < df["Service_Date"]]["Claim_ID"]:
        log("DQ-05", cid, "Critical", "Submission date precedes service date")

    # DQ-06 status must be approved value
    for cid in df[~df["Claim_Status"].isin(VALID_STATUS)]["Claim_ID"]:
        log("DQ-06", cid, "Medium", "Claim status not in approved value list")

    # DQ-07 status and denial flag must agree
    bad = df[((df["Claim_Status"] == "Denied") & (df["Denial_Flag"] == "No")) |
             ((df["Claim_Status"] == "Paid") & (df["Denial_Flag"] == "Yes"))]
    for cid in bad["Claim_ID"]:
        log("DQ-07", cid, "High", "Claim status conflicts with denial flag")

    # DQ-08 payer reference integrity
    payers = set(pd.read_csv(os.path.join(RAW, "dim_payer.csv"))["Payer_ID"])
    for cid in df[~df["Payer_ID"].isin(payers)]["Claim_ID"]:
        log("DQ-08", cid, "High", "Payer_ID not present in dim_payer")

    # DQ-09 reason code reference integrity
    reasons = set(pd.read_csv(os.path.join(RAW, "dim_denial_reason.csv"))["Denial_Reason_Code"])
    bad = df[df["Denial_Reason_Code"].notna() & ~df["Denial_Reason_Code"].isin(reasons)]
    for cid in bad["Claim_ID"]:
        log("DQ-09", cid, "High", "Denial reason code not present in dim_denial_reason")

    # DQ-10 recovery cannot exceed denied amount
    for cid in df[df["Recovery_Amount"] > df["Denied_Amount"] + 0.01]["Claim_ID"]:
        log("DQ-10", cid, "Critical", "Recovery amount exceeds denied amount")

    critical = {e["Record_ID"] for e in exceptions if e["Severity"] == "Critical"}
    return df[~df["Claim_ID"].isin(critical)].copy(), critical


def preventable_risk(df):
    """Transparent additive score. Weights are stated, not fitted."""
    auth_fail = (df["Auth_Required"] == "Yes") & (df["Authorization_Present"] == "No")
    score = (
        auth_fail * 30
        + (df["Eligibility_Verified"] == "No") * 20
        + (df["Documentation_Complete"] == "No") * 20
        + (df["Coding_Validation_Passed"] == "No") * 15
        + (df.get("Timely_Filing_Risk", pd.Series("Low", index=df.index)) == "High") * 15
    )
    return score.astype(int)


def risk_band(score):
    return pd.cut(score, bins=[-1, 14, 29, 999], labels=["Low", "Medium", "High"])


def add_scores(df):
    df = df.copy()
    df["Preventable_Risk_Score"] = preventable_risk(df)
    df["Risk_Band"] = risk_band(df["Preventable_Risk_Score"])

    # Recovery priority - only meaningful for denied claims
    denied = df["Denial_Flag"] == "Yes"
    amt = df["Denied_Amount"]
    amt_idx = (amt / amt[denied].max() * 100).fillna(0)

    likelihood = np.where(df["Preventable_Flag"] == "Yes", 75, 30)
    filing_urgency = np.where(df["Days_Outstanding"] > 60, 100,
                              np.where(df["Days_Outstanding"] > 30, 60, 25))
    age_risk = (df["Days_Outstanding"] / df["Days_Outstanding"].max() * 100).fillna(0)

    df["Recovery_Priority_Score"] = (
        0.45 * amt_idx + 0.30 * likelihood + 0.15 * filing_urgency + 0.10 * age_risk
    ).round(1)
    df.loc[~denied, "Recovery_Priority_Score"] = np.nan

    # Prevention opportunity - denied dollars weighted by how preventable the reason is
    preventable_prob = np.where(df["Preventable_Flag"] == "Yes", 0.8, 0.0)
    df["Prevention_Opportunity"] = (df["Denied_Amount"] * preventable_prob).round(2)
    return df


def score_pending(path_out):
    """The pre-submission queue. Same score, applied before anything is sent."""
    p = pd.read_csv(os.path.join(RAW, "pending_claims.csv"))
    p["Timely_Filing_Risk"] = np.where(p["Days_To_Submit"] > 60, "High",
                                       np.where(p["Days_To_Submit"] > 20, "Medium", "Low"))
    p["Denial_Flag"] = "No"
    p["Denied_Amount"] = 0.0
    p["Preventable_Risk_Score"] = preventable_risk(p)
    p["Risk_Band"] = risk_band(p["Preventable_Risk_Score"])

    rules = pd.read_csv(os.path.join(RAW, "prevention_rules.csv"))

    def triggered(r):
        hits = []
        if r["Auth_Required"] == "Yes" and r["Authorization_Present"] == "No":
            hits.append("PR-01")
        if r["Eligibility_Verified"] == "No":
            hits.append("PR-02")
        if r["Documentation_Complete"] == "No":
            hits.append("PR-03")
        if r["Coding_Validation_Passed"] == "No":
            hits.append("PR-04")
        if r["Days_To_Submit"] > 20:
            hits.append("PR-05")
        return ";".join(hits)

    p["Triggered_Rules"] = p.apply(triggered, axis=1)
    owner_map = dict(zip(rules["Rule_ID"], rules["Owner"]))
    p["Primary_Owner"] = p["Triggered_Rules"].str.split(";").str[0].map(owner_map).fillna("None")
    p["At_Risk_Amount"] = np.where(p["Risk_Band"] == "High", p["Claim_Amount"], 0.0)
    p.drop(columns=["Denial_Flag", "Denied_Amount"]).to_csv(path_out, index=False)
    return p


def main():
    os.makedirs(CLEAN, exist_ok=True)
    raw = pd.read_csv(os.path.join(RAW, "claims_fact_raw.csv"))
    total_in = len(raw)

    df, critical = clean(raw)
    df = add_scores(df)
    df.to_csv(os.path.join(CLEAN, "claims_fact.csv"), index=False)

    ex = pd.DataFrame(exceptions)
    ex.to_csv(os.path.join(CLEAN, "dq_exceptions.csv"), index=False)

    pending = score_pending(os.path.join(CLEAN, "pre_submission_queue.csv"))

    dq = 100 * (1 - ex["Record_ID"].nunique() / total_in)
    denied = df[df["Denial_Flag"] == "Yes"]

    print(f"rows in / out:            {total_in} / {len(df)}")
    print(f"exceptions / blocked:     {len(ex)} / {len(critical)}")
    print(f"Data Quality Score:       {dq:.2f}%")
    print(f"denial rate:              {len(denied)/len(df):.1%}")
    print(f"denied dollars:           ${denied['Denied_Amount'].sum():,.0f}")
    print(f"preventable denied $:     ${denied.loc[denied['Preventable_Flag']=='Yes','Denied_Amount'].sum():,.0f}")
    print(f"prevention opportunity:   ${df['Prevention_Opportunity'].sum():,.0f}")
    print(f"pending high risk:        {(pending['Risk_Band']=='High').sum()} claims, "
          f"${pending.loc[pending['Risk_Band']=='High','Claim_Amount'].sum():,.0f} at risk")


if __name__ == "__main__":
    main()
