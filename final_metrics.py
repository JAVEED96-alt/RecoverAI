"""
RecoverAI - Final Metrics Layer

Combines the policy and recovery outcome results
into one final evaluation report.

IMPORTANT:
Recovery figures are synthetic evaluation results.
"""

import os
import json
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

RECOVERY_CSV = os.path.join(
    OUTPUT_DIR,
    "recovery_outcomes.csv"
)

METRICS_JSON = os.path.join(
    OUTPUT_DIR,
    "final_metrics.json"
)


# ============================================================
# CREATE METRICS
# ============================================================

def generate_metrics():

    print()
    print("=" * 60)
    print("RecoverAI - Final Metrics")
    print("=" * 60)

    # --------------------------------------------------------
    # Load files
    # --------------------------------------------------------

    policy = pd.read_csv(
        POLICY_CSV
    )

    recovery = pd.read_csv(
        RECOVERY_CSV
    )

    # --------------------------------------------------------
    # Policy metrics
    # --------------------------------------------------------

    records_evaluated = len(policy)

    policy_decisions = len(policy)

    retry_now = len(
        policy[
            policy["action"] == "retry_now"
        ]
    )

    retry_later = len(
        policy[
            policy["action"] == "retry_later"
        ]
    )

    reminders = len(
        policy[
            policy["action"] == "send_reminder"
        ]
    )

    human_escalations = len(
        policy[
            policy["action"] == "escalate_human"
        ]
    )

    # --------------------------------------------------------
    # Recovery metrics
    # --------------------------------------------------------

    recovery_attempts = len(
        recovery
    )

    successful_recoveries = len(
        recovery[
            recovery["outcome"]
            == "recovered"
        ]
    )

    failed_recoveries = len(
        recovery[
            recovery["outcome"]
            == "failed"
        ]
    )

    revenue_at_risk = float(
        recovery["amount"].sum()
    )

    revenue_recovered = float(
        recovery["recovered_amount"].sum()
    )

    revenue_unrecovered = (
        revenue_at_risk
        - revenue_recovered
    )

    if recovery_attempts > 0:

        recovery_rate = (
            successful_recoveries
            / recovery_attempts
            * 100
        )

    else:

        recovery_rate = 0.0

    # --------------------------------------------------------
    # Exception count
    # --------------------------------------------------------

    exception_count = (
        failed_recoveries
        + human_escalations
    )

    # --------------------------------------------------------
    # Final metrics dictionary
    # --------------------------------------------------------

    metrics = {

        "records_evaluated":
            records_evaluated,

        "policy_decisions":
            policy_decisions,

        "retry_now":
            retry_now,

        "retry_later":
            retry_later,

        "send_reminder":
            reminders,

        "human_escalations":
            human_escalations,

        "recovery_attempts":
            recovery_attempts,

        "successful_recoveries":
            successful_recoveries,

        "failed_recoveries":
            failed_recoveries,

        "recovery_rate_percent":
            round(
                recovery_rate,
                2
            ),

        "revenue_at_risk":
            round(
                revenue_at_risk,
                2
            ),

        "revenue_recovered":
            round(
                revenue_recovered,
                2
            ),

        "revenue_unrecovered":
            round(
                revenue_unrecovered,
                2
            ),

        "exception_count":
            exception_count,

        "evaluation_type":
            "synthetic"
    }

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with open(
        METRICS_JSON,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print()
    print(
        f"Records evaluated:       "
        f"{records_evaluated}"
    )

    print(
        f"Policy decisions:        "
        f"{policy_decisions}"
    )

    print(
        f"Recovery attempts:       "
        f"{recovery_attempts}"
    )

    print(
        f"Successful recoveries:   "
        f"{successful_recoveries}"
    )

    print(
        f"Failed recoveries:       "
        f"{failed_recoveries}"
    )

    print(
        f"Recovery rate:            "
        f"{recovery_rate:.2f}%"
    )

    print(
        f"Revenue at risk:          "
        f"₹{revenue_at_risk:,.2f}"
    )

    print(
        f"Revenue recovered:        "
        f"₹{revenue_recovered:,.2f}"
    )

    print(
        f"Revenue unrecovered:      "
        f"₹{revenue_unrecovered:,.2f}"
    )

    print(
        f"Exceptions:               "
        f"{exception_count}"
    )

    print()
    print(
        f"Saved to:\n{METRICS_JSON}"
    )

    print("=" * 60)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    generate_metrics()