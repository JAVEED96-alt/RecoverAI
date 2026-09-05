"""
Audit + Metrics Layer
======================
Final layer of the pipeline. Joins:

  Detection  -> razorpay_failed_payments_synthetic.csv
                (payment_id, amount, error_code, root_cause_bucket, ...)
  Policy     -> policy_decisions.csv
                (payment_id, diagnosed_bucket, confidence, action, attempt_number, ...)
                NOTE: this file already contains the diagnosis output merged in,
                so there's no separate diagnosis join needed.
  Execution  -> execution_log.csv
                (payment_id, action_taken, status, recovered_amount, timestamp)
                Created/appended by your execution layer as it runs.

into ONE audit table (one row per failed payment, showing what was detected,
decided, and what actually happened), plus a metrics summary.

NOT joined in: diagnosis_predictions.csv and detection_risk_scores.csv.
Both are model training/eval datasets — they have no payment_id column,
so there's nothing to join them on. They prove your models work; they
aren't part of the per-payment audit trail.

HOW TO USE
----------
1. From your execution layer, call log_execution_outcome(...) after every
   attempt (see function below for the exact call).
2. Run this file directly to build the audit table + print metrics:

       python backend/audit_metrics_layer.py
"""

import os
import pandas as pd
from datetime import datetime, timezone

# ---- File locations - adjust paths to match your project structure ----
DETECTION_CSV = "razorpay_failed_payments_synthetic (1).csv"
POLICY_CSV = "outputs/policy_decisions.csv"
EXECUTION_LOG_CSV = "execution_log.csv"      # created/appended by execution layer
AUDIT_OUTPUT_CSV = "audit_log.csv"


# ---------------------------------------------------------------------
# STEP 1: Called FROM your execution layer, once per attempt
# ---------------------------------------------------------------------
def log_execution_outcome(payment_id, action_taken, status, recovered_amount=0,
                           notes="", log_path=EXECUTION_LOG_CSV):
    """
    Append one row to execution_log.csv. Call this at the end of every
    execution attempt in your execution layer / razorpay_service.py, e.g.:

        from audit_metrics_layer import log_execution_outcome
        ...
        try:
            result = client.payment_link.create({...})
            log_execution_outcome(payment_id, "retry_now", "success",
                                   recovered_amount=amount)
        except Exception as e:
            log_execution_outcome(payment_id, "retry_now", "failed", notes=str(e))
    """
    row = {
        "payment_id": payment_id,
        "action_taken": action_taken,
        "execution_status": status,          # success / failed / skipped
        "recovered_amount": recovered_amount,
        "notes": notes,
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    dirpath = os.path.dirname(log_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    file_exists = os.path.isfile(log_path)
    pd.DataFrame([row]).to_csv(log_path, mode="a", header=not file_exists, index=False)
    return row


# ---------------------------------------------------------------------
# STEP 2: Build the full audit table: Detection -> Policy -> Execution
# ---------------------------------------------------------------------
def build_audit_table(detection_csv=DETECTION_CSV, policy_csv=POLICY_CSV,
                       execution_csv=EXECUTION_LOG_CSV):
    detection = pd.read_csv(detection_csv)

    # keep only the failed events - detection & successful-payments files
    # share a schema, but audit only cares about payments that needed recovery
    if "status" in detection.columns:
        detection = detection[detection["status"] == "failed"].copy()

    audit = detection.copy()

    if os.path.isfile(policy_csv):
        policy = pd.read_csv(policy_csv)
        audit = audit.merge(policy, on="payment_id", how="left", suffixes=("", "_policy"))
    else:
        for col in ["diagnosed_bucket", "confidence", "final_bucket_used",
                    "action", "reason", "attempt_number", "escalate"]:
            audit[col] = pd.NA

    if os.path.isfile(execution_csv):
        execution = pd.read_csv(execution_csv)
        audit = audit.merge(execution, on="payment_id", how="left", suffixes=("", "_exec"))
    else:
        audit["execution_status"] = pd.NA
        audit["recovered_amount"] = 0.0

    return audit


# ---------------------------------------------------------------------
# STEP 3: Compute summary metrics from the audit table
# ---------------------------------------------------------------------
def compute_metrics(audit_df):
    total_failed_events = len(audit_df)
    decided = audit_df[audit_df["action"].notna()] if "action" in audit_df else audit_df.iloc[0:0]
    executed = audit_df[audit_df["execution_status"].notna()]
    recovered = audit_df[audit_df["execution_status"] == "success"]

    total_amount_at_risk = audit_df["amount"].sum() if "amount" in audit_df else 0
    total_recovered = recovered["recovered_amount"].sum() if "recovered_amount" in audit_df else 0

    recovery_rate = (len(recovered) / len(executed) * 100) if len(executed) > 0 else 0.0

    metrics = {
        "total_failed_events": total_failed_events,
        "total_events_with_decision": len(decided),
        "total_attempts_executed": len(executed),
        "total_recovered_count": len(recovered),
        "recovery_rate_pct_of_executed": round(recovery_rate, 2),
        "total_amount_at_risk": round(float(total_amount_at_risk), 2),
        "total_amount_recovered": round(float(total_recovered), 2),
        "pct_of_at_risk_amount_recovered": round(
            (total_recovered / total_amount_at_risk * 100) if total_amount_at_risk else 0, 2
        ),
    }

    if "root_cause_bucket" in audit_df:
        metrics["by_root_cause"] = (
            audit_df.groupby("root_cause_bucket")
            .agg(events=("root_cause_bucket", "count"),
                 recovered=("execution_status", lambda s: (s == "success").sum()))
            .to_dict(orient="index")
        )

    if "action" in audit_df:
        metrics["by_action"] = (
            audit_df.dropna(subset=["action"])
            .groupby("action")
            .agg(events=("action", "count"),
                 recovered=("execution_status", lambda s: (s == "success").sum()))
            .to_dict(orient="index")
        )

    return metrics


# ---------------------------------------------------------------------
# Run standalone
# ---------------------------------------------------------------------
if __name__ == "__main__":
    audit = build_audit_table()
    audit.to_csv(AUDIT_OUTPUT_CSV, index=False)
    print(f"Audit table written to {AUDIT_OUTPUT_CSV} ({len(audit)} rows)\n")

    metrics = compute_metrics(audit)
    print("=== METRICS SUMMARY ===")
    for k, v in metrics.items():
        if isinstance(v, dict):
            print(f"\n{k}:")
            for sub_k, sub_v in v.items():
                print(f"  {sub_k}: {sub_v}")
        else:
            print(f"{k}: {v}")