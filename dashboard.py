import requests
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="RecoverAI",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# API FUNCTIONS
# ============================================================

def get_api_data(endpoint):

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            f"Could not connect to FastAPI: {e}"
        )

        return None


def run_evaluation():

    try:

        response = requests.post(
            f"{API_URL}/run-evaluation",
            timeout=300
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            f"Evaluation failed: {e}"
        )

        return None


# ============================================================
# HEADER
# ============================================================

st.title("💰 RecoverAI")

st.subheader(
    "AI Revenue Recovery Controller"
)

st.write(
    "Detect revenue at risk → diagnose the failure → "
    "choose the best recovery action → execute recovery → "
    "measure the outcome."
)

st.divider()


# ============================================================
# FASTAPI CONNECTION
# ============================================================

metrics = get_api_data("/metrics")

recovery_data = get_api_data(
    "/recovery-outcomes"
)

exception_data = get_api_data(
    "/exceptions"
)

policy_data = get_api_data(
    "/policy-decisions"
)


# ============================================================
# API CONNECTION CHECK
# ============================================================

if metrics is None:

    st.error(
        "🔴 FastAPI is not available."
    )

    st.info(
        "Start FastAPI with:\n\n"
        "uvicorn backend.api:app --reload"
    )

    st.stop()


st.success(
    "🟢 Connected to RecoverAI FastAPI"
)


# ============================================================
# RECOVERY CONTROL
# ============================================================

st.header("🚀 Recovery Control")

st.write(
    "Run the complete RecoverAI pipeline from Detection "
    "through Final Metrics."
)


if st.button(
    "🚀 Run Complete Recovery Evaluation",
    type="primary",
    use_container_width=True
):

    with st.spinner(
        "Running Detection → Diagnosis → Policy → "
        "Execution → Recovery → Metrics..."
    ):

        result = run_evaluation()

    if result:

        st.success(
            "✅ Recovery evaluation completed successfully!"
        )

        st.rerun()


st.divider()


# ============================================================
# CONVERT API DATA TO DATAFRAMES
# ============================================================

if recovery_data:

    recovery_df = pd.DataFrame(
        recovery_data.get(
            "data",
            []
        )
    )

else:

    recovery_df = pd.DataFrame()


if exception_data:

    exceptions_df = pd.DataFrame(
        exception_data.get(
            "data",
            []
        )
    )

else:

    exceptions_df = pd.DataFrame()


if policy_data:

    policy_df = pd.DataFrame(
        policy_data.get(
            "data",
            []
        )
    )

else:

    policy_df = pd.DataFrame()


# ============================================================
# MAIN KPI SECTION
# ============================================================

st.header("📊 Recovery Performance")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Records Evaluated",
        metrics.get(
            "records_evaluated",
            0
        )
    )


with col2:

    st.metric(
        "Revenue at Risk",
        f"₹{metrics.get('revenue_at_risk', 0):,.2f}"
    )


with col3:

    st.metric(
        "Revenue Recovered",
        f"₹{metrics.get('revenue_recovered', 0):,.2f}"
    )


with col4:

    st.metric(
        "Recovery Rate",
        f"{metrics.get('recovery_rate_percent', 0):.2f}%"
    )


# ============================================================
# SECOND KPI ROW
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Recovery Attempts",
        metrics.get(
            "recovery_attempts",
            0
        )
    )


with col2:

    st.metric(
        "Successful Recoveries",
        metrics.get(
            "successful_recoveries",
            0
        )
    )


with col3:

    st.metric(
        "Failed Recoveries",
        metrics.get(
            "failed_recoveries",
            0
        )
    )


with col4:

    st.metric(
        "Exceptions",
        metrics.get(
            "exception_count",
            0
        )
    )


# ============================================================
# SYNTHETIC EVALUATION NOTICE
# ============================================================

st.info(
    "⚠️ Evaluation type: SYNTHETIC. "
    "The recovery and revenue figures shown here "
    "are synthetic evaluation results."
)


# ============================================================
# REVENUE OVERVIEW
# ============================================================

st.header("💰 Revenue Overview")


revenue_df = pd.DataFrame({

    "Category": [
        "Revenue at Risk",
        "Revenue Recovered",
        "Revenue Unrecovered"
    ],

    "Amount": [
        metrics.get(
            "revenue_at_risk",
            0
        ),

        metrics.get(
            "revenue_recovered",
            0
        ),

        metrics.get(
            "revenue_unrecovered",
            0
        )
    ]

})


st.bar_chart(
    revenue_df.set_index(
        "Category"
    )
)


# ============================================================
# RECOVERY OUTCOME CHART
# ============================================================

st.header("🎯 Recovery Outcomes")


outcome_df = pd.DataFrame({

    "Outcome": [
        "Successful",
        "Failed"
    ],

    "Count": [
        metrics.get(
            "successful_recoveries",
            0
        ),

        metrics.get(
            "failed_recoveries",
            0
        )
    ]

})


st.bar_chart(
    outcome_df.set_index(
        "Outcome"
    )
)


# ============================================================
# POLICY DECISIONS
# ============================================================

st.header("🤖 AI Policy Decisions")


if not policy_df.empty:

    if "action" in policy_df.columns:

        policy_counts = (
            policy_df["action"]
            .value_counts()
            .rename_axis("Action")
            .reset_index(
                name="Count"
            )
        )

        st.bar_chart(
            policy_counts.set_index(
                "Action"
            )
        )

    else:

        st.warning(
            "Policy data does not contain an 'action' column."
        )

else:

    st.warning(
        "No policy decisions available."
    )


# ============================================================
# POLICY TABLE
# ============================================================

st.subheader(
    "Policy Decision Details"
)


if not policy_df.empty:

    st.dataframe(
        policy_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No policy records available."
    )


# ============================================================
# RECOVERY AUDIT
# ============================================================

st.header("🔍 Recovery Audit")


if not recovery_df.empty:

    st.dataframe(
        recovery_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No recovery outcome records available."
    )


# ============================================================
# EXCEPTIONS
# ============================================================

st.header("⚠️ Recovery Exceptions")


if not exceptions_df.empty:

    st.warning(
        f"{len(exceptions_df)} failed recovery "
        "records detected."
    )

    st.dataframe(
        exceptions_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No recovery exceptions."
    )


# ============================================================
# SYSTEM ARCHITECTURE
# ============================================================

st.header("🏗️ RecoverAI Architecture")


st.code(
"""
Payment Data
      ↓
Detection Layer
      ↓
Diagnosis Layer
      ↓
Policy Layer
      ↓
Execution Layer
      ↓
Recovery Outcome Layer
      ↓
Final Metrics
      ↓
FastAPI
      ↓
Streamlit Dashboard
""",
language="text"
)


# ============================================================
# SYSTEM STATUS
# ============================================================

st.header("🟢 System Status")


status_col1, status_col2, status_col3 = st.columns(3)


with status_col1:

    st.success(
        "FastAPI\n\nConnected"
    )


with status_col2:

    st.success(
        "Pipeline\n\nOperational"
    )


with status_col3:

    st.success(
        "Dashboard\n\nOperational"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "RecoverAI | AI Revenue Recovery Controller | "
    "FastAPI + Streamlit | Synthetic Evaluation"
)