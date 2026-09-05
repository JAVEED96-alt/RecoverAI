"""
Explanation Layer
==================
Turns a payment_id into a grounded, human-readable explanation of why the
payment failed and what RecoverAI decided to do about it.

Joins every layer already computed by the pipeline, for ONE payment:

    Detection            -> razorpay_failed_payments_synthetic (1).csv
                             (raw error_code / error_reason / error_description)
    Diagnosis + Policy   -> outputs/policy_decisions.csv
                             (diagnosed_bucket, confidence, action, reason)
    Execution            -> execution_log.csv
                             (action_taken, execution_status, notes)
    Recovery             -> outputs/recovery_outcomes.csv
                             (only present for retry_now cases: outcome, recovered_amount)

Design choice: this does ONE deterministic lookup/join per payment_id, not a
multi-step agent loop. The retrieval is a fixed join, so there's nothing for
an agent to "decide" to fetch — keeping it single-shot removes a class of
failure (wrong tool call, missed field) without losing any explainability.
The model is instructed to use ONLY the fields it's given and to say so
explicitly if a step (e.g. execution) hasn't happened yet — never guess.

HOW TO USE
----------
1. pip install anthropic --break-system-packages
2. Add ANTHROPIC_API_KEY=... to backend/.env
3. Call explain_payment("pay_xxx") directly, or hit GET /explain/{payment_id}
   once this is wired into api.py.
"""

import os
import sys
import json

import pandas as pd
from dotenv import load_dotenv
from google import genai

# ============================================================
# PATHS  (mirrors api.py's layout)
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

DETECTION_CSV = os.path.join(BASE_DIR, "razorpay_failed_payments_synthetic (1).csv")
SUCCESS_CSV = os.path.join(BASE_DIR, "razorpay_successful_payments_synthetic.csv")
POLICY_CSV = os.path.join(OUTPUT_DIR, "policy_decisions.csv")
EXECUTION_LOG_CSV = os.path.join(BASE_DIR, "execution_log.csv")
RECOVERY_CSV = os.path.join(OUTPUT_DIR, "recovery_outcomes.csv")

ENV_PATH = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY not found. Add it to backend/.env"
    )

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# STEP 1: Build the grounded case record for one payment_id
# ============================================================

def _clean(record: dict) -> dict:
    """Replace NaN/NaT with None so json.dumps doesn't choke."""
    cleaned = {}
    for key, value in record.items():
        if isinstance(value, float) and pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned


def get_payment_case(payment_id: str) -> dict | None:
    """
    Joins every layer's output for a single payment_id.

    Returns:
        dict   - the full case record if the payment was seen at Detection
        {"status": "captured", ...}  - if it's actually a SUCCESSFUL payment
        None   - if the payment_id doesn't exist anywhere in our data
    """
    if not os.path.exists(DETECTION_CSV):
        raise FileNotFoundError(f"Detection file not found: {DETECTION_CSV}")

    detection = pd.read_csv(DETECTION_CSV)
    match = detection[detection["payment_id"] == payment_id]

    if match.empty:
        # Not a failure — check if it's actually a successful payment,
        # so we don't invent a failure story for a payment that never failed.
        if os.path.exists(SUCCESS_CSV):
            success = pd.read_csv(SUCCESS_CSV)
            s_match = success[success["payment_id"] == payment_id]
            if not s_match.empty:
                record = _clean(s_match.iloc[0].to_dict())
                record["_note"] = "This payment succeeded — it never appears in the failed-payments data."
                return record
        return None

    case = _clean(match.iloc[0].to_dict())

    # --- Diagnosis + Policy decision ---
    if os.path.exists(POLICY_CSV):
        policy = pd.read_csv(POLICY_CSV)
        p_match = policy[policy["payment_id"] == payment_id]
        if not p_match.empty:
            case.update(_clean(p_match.iloc[0].to_dict()))

    # --- Execution outcome (take the most recent attempt, if several) ---
    if os.path.exists(EXECUTION_LOG_CSV):
        execution = pd.read_csv(EXECUTION_LOG_CSV)
        e_match = execution[execution["payment_id"] == payment_id]
        if not e_match.empty:
            if "execution_timestamp" in e_match.columns:
                e_match = e_match.sort_values("execution_timestamp")
            case.update(_clean(e_match.iloc[-1].to_dict()))

    # --- Recovery outcome (only exists for retry_now cases) ---
    # Prefixed with recovery_ so it never collides with execution's own
    # recovered_amount / reason fields — both stay visible to the model.
    if os.path.exists(RECOVERY_CSV):
        recovery = pd.read_csv(RECOVERY_CSV)
        r_match = recovery[recovery["payment_id"] == payment_id]
        if not r_match.empty:
            raw = _clean(r_match.iloc[0].to_dict())
            if "recovery_probability" in raw:
                case["recovery_probability"] = raw["recovery_probability"]
            for key in ("outcome", "recovered_amount", "reason"):
                if key in raw:
                    case[f"recovery_{key}"] = raw[key]

    return case


# ============================================================
# STEP 2: Generate a grounded explanation
# ============================================================

def _fmt_confidence(value):
    """Format model confidence safely."""
    try:
        value = float(value)
        if value <= 1:
            value *= 100
        return f"{value:.1f}%"
    except (TypeError, ValueError):
        return "not available"


def _fmt_amount(value):
    """Format INR amount safely."""
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "an unknown amount"


def explain_payment(payment_id: str) -> dict:
    """
    Generate a grounded human-readable explanation using Gemini.

    Gemini only explains the case.
    It does NOT make the recovery decision.
    """

    case = get_payment_case(payment_id)

    # --------------------------------------------------------
    # Payment not found
    # --------------------------------------------------------

    if case is None:
        return {
            "payment_id": payment_id,
            "found": False,
            "explanation": (
                f"I don't have any record of payment {payment_id} — "
                "it doesn't appear in either the failed or successful "
                "payments data, so I can't explain what happened to it."
            ),
            "case": None,
        }

    # --------------------------------------------------------
    # Successful payment
    # --------------------------------------------------------

    if case.get("_note"):
        amount = _fmt_amount(case.get("amount"))
        method = case.get("method", "an unknown payment method")

        return {
            "payment_id": payment_id,
            "found": True,
            "explanation": (
                f"Payment {payment_id} actually succeeded. "
                f"It was captured for {amount} via {method}. "
                "It does not appear in the failed-payments data, "
                "so there is no payment failure to explain.\n\n"
                "Based on: status, amount, method"
            ),
            "case": case,
        }

    # --------------------------------------------------------
    # Gemini explanation
    # --------------------------------------------------------

    prompt = f"""
You are the explanation engine for RecoverAI.

Your job is ONLY to explain the payment case.
Do NOT make a new recovery decision.

Use ONLY the information contained in the case record.

STRICT RULES:

1. Never invent information.
2. Never invent a payment amount, customer, reason,
   recovery result, or execution result.
3. Explain the failure in simple language.
4. Explain the diagnosed root cause and confidence.
5. Explain the policy action already selected by RecoverAI.
6. Explain why that policy action was selected if a reason exists.
7. Explain the execution status if available.
8. Explain the recovery outcome if available.
9. IMPORTANT:
   "sent" or "executed" does NOT mean money was recovered.
10. If recovery data is missing, explicitly say that the
    recovery outcome is not available yet.
11. Do not change or reinterpret the policy decision.
12. Keep the explanation concise and useful for a support agent.

Use exactly this structure:

What happened:
[plain-language explanation]

Why it happened:
[diagnosis and confidence]

What RecoverAI decided:
[existing policy action and reason]

What happened next:
[execution and recovery status]

Based on:
[list the exact fields used]

Payment ID:
{payment_id}

CASE RECORD:
{case}
"""

    try:

        response = gemini_client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
        )

        explanation = response.text

        if not explanation:
            raise RuntimeError(
                "Gemini returned an empty explanation."
            )

    except Exception as e:

        # ----------------------------------------------------
        # Safe fallback
        # ----------------------------------------------------

        explanation = (
            "Gemini explanation was unavailable.\n\n"
            f"Reason: {str(e)}\n\n"
            "The underlying RecoverAI case data is still available."
        )

    return {
        "payment_id": payment_id,
        "found": True,
        "explanation": explanation,
        "case": case,
    }