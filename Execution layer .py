"""
Execution Layer
================
Reads each row of policy_decisions.csv (the Policy Layer's output) and
actually DOES something with it via Razorpay, then logs the outcome
through audit_metrics_layer.log_execution_outcome() so the Audit layer
has real data instead of zeros.

Action -> what actually happens:
  retry_now       -> create a real Razorpay Payment Link (test mode) and
                      send it back for the customer to pay
  retry_later     -> not executed now; logged as "skipped" (a scheduler
                      would pick this up at retry_at time - not built yet)
  send_reminder   -> logged as "skipped" (would trigger an SMS/email in
                      a real system - notification sending not built yet)
  escalate_human  -> no API call; logged as "skipped" because it's meant
                      for a human to handle, not automation

HOW TO RUN
----------
    python backend/execution_layer.py

This will:
  1. Read policy_decisions.csv
  2. For each row, attempt the action
  3. Append one row to execution_log.csv per attempt (via log_execution_outcome)
  4. You can then re-run audit_metrics_layer.py to see updated numbers
"""

import os
import pandas as pd
import razorpay
from dotenv import load_dotenv

from audit_metrics_layer import log_execution_outcome

load_dotenv()

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")
client = razorpay.Client(auth=(key_id, key_secret))

POLICY_CSV = "outputs/policy_decisions.csv"
DETECTION_CSV = "razorpay_failed_payments_synthetic (1).csv"


def attempt_retry_now(payment_id, amount, customer_id=""):
    """
    Creates a real (test-mode) Razorpay Payment Link for the failed amount.
    Returns (status, recovered_amount, notes).
    NOTE: this doesn't auto-mark the payment as "recovered" - a real
    recovery only happens once the customer actually pays the link. For
    now we log status='sent' to mean "retry attempt sent successfully",
    not "money recovered". Wire a webhook later to flip this to 'success'
    when Razorpay confirms the link was paid.
    """
    try:
        amount_paise = int(round(amount * 100))  # Razorpay expects paise
        link = client.payment_link.create({
            "amount": amount_paise,
            "currency": "INR",
            "description": f"Retry for failed payment {payment_id}",
            "reference_id": payment_id,
            "notes": {"original_payment_id": payment_id},
        })
        return "sent", 0, f"payment_link_id={link.get('id')}"
    except Exception as e:
        return "failed", 0, str(e)


def run_execution():
    policy = pd.read_csv(POLICY_CSV)
    detection = pd.read_csv(DETECTION_CSV)
    amounts = detection.set_index("payment_id")["amount"].to_dict()

    results = {"sent": 0, "failed": 0, "skipped": 0}

    for _, row in policy.iterrows():
        payment_id = row["payment_id"]
        action = row["action"]
        amount = amounts.get(payment_id, 0)

        if action == "retry_now":
            status, recovered, notes = attempt_retry_now(payment_id, amount)
        elif action in ("retry_later", "send_reminder"):
            status, recovered, notes = "skipped", 0, f"'{action}' not yet automated - needs a scheduler/notifier"
        elif action == "escalate_human":
            status, recovered, notes = "skipped", 0, "routed to human review, no automated action taken"
        else:
            status, recovered, notes = "skipped", 0, f"unrecognized action: {action}"

        log_execution_outcome(payment_id, action, status, recovered_amount=recovered, notes=notes)
        results[status] = results.get(status, 0) + 1

    print("Execution run complete:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("\nLogged to execution_log.csv - run audit_metrics_layer.py to see updated metrics.")


if __name__ == "__main__":
    run_execution()