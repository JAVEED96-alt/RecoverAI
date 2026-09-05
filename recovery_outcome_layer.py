"""
RecoverAI - Recovery Outcome Layer

Evaluates the outcome of executed recovery actions
on the synthetic dataset.

IMPORTANT:
These are SYNTHETIC evaluation outcomes.
They are not real customer payments.

Real recovery will later come from the Razorpay webhook.
"""

import os
import hashlib
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

POLICY_CSV = os.path.join(
    OUTPUT_DIR,
    "policy_decisions.csv"
)

DETECTION_CSV = os.path.join(
    BASE_DIR,
    "razorpay_failed_payments_synthetic (1).csv"
)

OUTPUT_CSV = os.path.join(
    OUTPUT_DIR,
    "recovery_outcomes.csv"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# DETERMINISTIC RECOVERY PROBABILITY
# ============================================================

def recovery_probability(payment_id):

    """
    Creates a deterministic probability from payment_id.

    This means the same input always produces
    the same result.

    We are NOT randomly cherry-picking successful
    recoveries.
    """

    value = hashlib.sha256(
        str(payment_id).encode()
    ).hexdigest()

    number = int(
        value[:8],
        16
    )

    return (
        number % 100
    ) / 100


# ============================================================
# RUN OUTCOME EVALUATION
# ============================================================

def run_recovery_outcomes():

    print()
    print("=" * 60)
    print("RecoverAI - Recovery Outcome Layer")
    print("=" * 60)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    policy = pd.read_csv(
        POLICY_CSV
    )

    detection = pd.read_csv(
        DETECTION_CSV
    )

    # --------------------------------------------------------
    # Merge policy + payment data
    # --------------------------------------------------------

    df = policy.merge(
        detection[
            [
                "payment_id",
                "amount"
            ]
        ],
        on="payment_id",
        how="left"
    )

    # --------------------------------------------------------
    # Only executed recovery actions
    # --------------------------------------------------------

    recovery_df = df[
        df["action"] == "retry_now"
    ].copy()

    print(
        f"Recovery actions evaluated: "
        f"{len(recovery_df)}"
    )

    results = []

    # ========================================================
    # EVALUATE EACH RECOVERY
    # ========================================================

    for _, row in recovery_df.iterrows():

        payment_id = row[
            "payment_id"
        ]

        amount = float(
            row["amount"]
        )

        probability = recovery_probability(
            payment_id
        )

        # ----------------------------------------------------
        # Recovery rule
        # ----------------------------------------------------
        #
        # 60% threshold.
        #
        # This is a synthetic benchmark,
        # not a claim about real customer behavior.
        #

        if probability < 0.60:

            outcome = "recovered"

            recovered_amount = amount

            reason = (
                "Synthetic recovery success"
            )

        else:

            outcome = "failed"

            recovered_amount = 0

            reason = (
                "Synthetic recovery unsuccessful"
            )

        results.append({

            "payment_id":
                payment_id,

            "action":
                row["action"],

            "amount":
                amount,

            "recovery_probability":
                round(
                    probability,
                    4
                ),

            "outcome":
                outcome,

            "recovered_amount":
                recovered_amount,

            "reason":
                reason
        })

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    outcomes = pd.DataFrame(
        results
    )

    outcomes.to_csv(
        OUTPUT_CSV,
        index=False
    )

    # ========================================================
    # METRICS
    # ========================================================

    total_attempts = len(
        outcomes
    )

    successful = len(
        outcomes[
            outcomes["outcome"]
            == "recovered"
        ]
    )

    failed = len(
        outcomes[
            outcomes["outcome"]
            == "failed"
        ]
    )

    total_at_risk = outcomes[
        "amount"
    ].sum()

    total_recovered = outcomes[
        "recovered_amount"
    ].sum()

    recovery_rate = (
        successful / total_attempts * 100
        if total_attempts > 0
        else 0
    )

    unrecovered = (
        total_at_risk
        - total_recovered
    )

    # ========================================================
    # PRINT REPORT
    # ========================================================

    print()
    print("=" * 60)
    print("RECOVERY RESULTS")
    print("=" * 60)

    print(
        f"Total recovery attempts: "
        f"{total_attempts}"
    )

    print(
        f"Successful recoveries:   "
        f"{successful}"
    )

    print(
        f"Failed recoveries:       "
        f"{failed}"
    )

    print(
        f"Recovery rate:           "
        f"{recovery_rate:.2f}%"
    )

    print(
        f"Revenue at risk:         "
        f"₹{total_at_risk:,.2f}"
    )

    print(
        f"Revenue recovered:       "
        f"₹{total_recovered:,.2f}"
    )

    print(
        f"Revenue unrecovered:     "
        f"₹{unrecovered:,.2f}"
    )

    print("=" * 60)

    print()
    print(
        f"Saved to:\n{OUTPUT_CSV}"
    )

    print()
    print(
        "NOTE: These recovery figures are "
        "synthetic evaluation results."
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    run_recovery_outcomes()