"""
Decision / Policy Layer
-------------------------
Takes each diagnosed event (predicted_bucket + confidence from the ML
diagnosis model) and outputs a BOUNDED, EXPLAINABLE action.

Core safety rule: if the model isn't confident enough, don't trust its
bucket — route to human escalation instead of guessing. This is what
makes the pipeline "gated" rather than fully autonomous.

Bounds enforced:
  - max_attempts per payment (hard cap, no infinite retries)
  - cooldown windows per bucket (don't hammer the same payment)
  - low-confidence predictions -> always escalate_human
  - fraud-flagged bucket -> always escalate_human, never auto-act
  - high amount + low confidence -> escalate_human (extra caution on big ₹)
"""

import os

import pandas as pd
from datetime import datetime, timedelta

# ------------------------------------------------------------------
# Config: bounded policy rules
# ------------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.55       # below this -> don't trust the model's bucket
HIGH_VALUE_THRESHOLD = 20000      # ₹ amount considered "high value"
MAX_ATTEMPTS = {
    "retryable_transient": 3,
    "retryable_with_delay": 2,
    "abandoned_checkout": 2,
    "non_retryable": 0,           # never auto-retry, needs new payment method
    "escalate_human": 0,
}
COOLDOWN_HOURS = {
    "retryable_transient": 0.5,   # retry soon
    "retryable_with_delay": 24,   # wait for next salary/settlement cycle
    "abandoned_checkout": 2,      # nudge reminder after short delay
}

ACTION_MAP = {
    "retryable_transient": "retry_now",
    "retryable_with_delay": "retry_later",
    "abandoned_checkout": "send_reminder",
    "non_retryable": "request_new_payment_method",
    "escalate_human": "escalate_human",
}

REASON_TEMPLATES = {
    "retry_now": "Transient failure (network/gateway) — safe to retry immediately.",
    "retry_later": "Likely insufficient funds — retrying after a cooldown window improves success odds.",
    "send_reminder": "Customer abandoned checkout — a reminder/payment link nudge is the appropriate action.",
    "request_new_payment_method": "Card/instrument issue (expired, declined, invalid CVV) — retrying same method won't help.",
    "escalate_human": "Low model confidence or high-risk signal — routed to human review instead of auto-acting.",
}


def decide_action(row, attempt_count=0):
    """
    row: dict-like with keys: predicted_bucket, confidence, amount, method, payment_id
    attempt_count: how many times we've already tried this payment_id
    Returns: dict with action, reason, retry_at, escalate (bool), attempt_number
    """
    bucket = row["predicted_bucket"]
    confidence = row["confidence"]
    amount = row["amount"]

    escalate = False
    override_reason = None

    # --- Gate 1: low confidence -> don't trust the diagnosis, escalate ---
    if confidence < CONFIDENCE_THRESHOLD:
        bucket = "escalate_human"
        escalate = True
        override_reason = f"Model confidence {confidence:.2f} below threshold {CONFIDENCE_THRESHOLD} — cannot safely act on this diagnosis."

    # --- Gate 2: fraud bucket -> always escalate, never auto-act ---
    elif bucket == "escalate_human":
        escalate = True

    # --- Gate 3: high value + borderline confidence -> extra caution ---
    elif amount > HIGH_VALUE_THRESHOLD and confidence < 0.75:
        bucket = "escalate_human"
        escalate = True
        override_reason = f"High-value payment (₹{amount:,.0f}) with only {confidence:.2f} confidence — escalated for human sign-off."

    # --- Gate 4: attempt cap exceeded -> stop retrying, escalate ---
    max_allowed = MAX_ATTEMPTS.get(bucket, 0)
    if not escalate and attempt_count >= max_allowed:
        bucket = "escalate_human"
        escalate = True
        override_reason = f"Max retry attempts ({max_allowed}) reached for bucket '{row['predicted_bucket']}' — stopping and escalating."

    action = ACTION_MAP.get(bucket, "escalate_human")
    reason = override_reason or REASON_TEMPLATES.get(action, "")

    cooldown_hrs = COOLDOWN_HOURS.get(bucket, 0)
    retry_at = (datetime.now() + timedelta(hours=cooldown_hrs)) if action in ("retry_now", "retry_later", "send_reminder") else None

    return {
        "payment_id": row["payment_id"],
        "diagnosed_bucket": row["predicted_bucket"],
        "confidence": round(confidence, 3),
        "final_bucket_used": bucket,
        "action": action,
        "reason": reason,
        "attempt_number": attempt_count + 1,
        "max_attempts_allowed": max_allowed,
        "escalate": escalate,
        "retry_at": retry_at.strftime("%Y-%m-%d %H:%M:%S") if retry_at else None,
    }


if __name__ == "__main__":
    # Load diagnosis model predictions from the previous layer
    preds = pd.read_csv("diagnosis_predictions.csv")

    # Need payment_id + amount for policy decisions — re-attach from original data
    original = pd.read_csv("razorpay_failed_payments_synthetic (1).csv")
    preds = preds.reset_index(drop=True)
    preds["payment_id"] = original.loc[preds.index, "payment_id"].values if len(original) >= len(preds) else [f"pay_test_{i}" for i in range(len(preds))]

    decisions = []
    for _, row in preds.iterrows():
        decision = decide_action(row, attempt_count=0)
        decisions.append(decision)
    os.makedirs("outputs", exist_ok=True)
    decisions_df = pd.DataFrame(decisions)
    decisions_df.to_csv("outputs/policy_decisions.csv", index=False)

    print("=== Action distribution ===")
    print(decisions_df["action"].value_counts())
    print(f"\nEscalated to human: {decisions_df['escalate'].sum()} / {len(decisions_df)}")
    print("\nSample decisions:")
    print(decisions_df[["payment_id", "diagnosed_bucket", "confidence", "action", "reason"]].head(8).to_string(index=False))
    print("\nSaved -> policy_decisions.csv")