"""Loads cleaned claims data into SQLite so sql/07_sql_analysis.sql can run."""

import os
import sqlite3

import pandas as pd

DB = os.path.join("data", "claims.db")
TABLES = {
    "claims_fact": os.path.join("data", "clean", "claims_fact.csv"),
    "pre_submission_queue": os.path.join("data", "clean", "pre_submission_queue.csv"),
    "dq_exceptions": os.path.join("data", "clean", "dq_exceptions.csv"),
    "dim_payer": os.path.join("data", "raw", "dim_payer.csv"),
    "dim_denial_reason": os.path.join("data", "raw", "dim_denial_reason.csv"),
    "dim_service_line": os.path.join("data", "raw", "dim_service_line.csv"),
    "dim_date": os.path.join("data", "raw", "dim_date.csv"),
    "prevention_rules": os.path.join("data", "raw", "prevention_rules.csv"),
}


def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    for name, path in TABLES.items():
        df = pd.read_csv(path)
        df.to_sql(name, con, if_exists="replace", index=False)
        print(f"{name:<22} {len(df):>6} rows")
    con.execute("CREATE INDEX IF NOT EXISTS ix_claims_payer ON claims_fact(Payer_ID)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_claims_reason ON claims_fact(Denial_Reason_Code)")
    con.commit()
    con.close()
    print(f"\nwrote {DB}")


if __name__ == "__main__":
    main()
