import os
import json
import math
import pandas as pd
import subprocess
import sys

from fastapi import FastAPI, HTTPException


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="RecoverAI Data API",
    description="API for RecoverAI metrics and recovery results",
    version="1.0.0"
)


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

METRICS_FILE = os.path.join(
    OUTPUT_DIR,
    "final_metrics.json"
)

RECOVERY_FILE = os.path.join(
    OUTPUT_DIR,
    "recovery_outcomes.csv"
)

POLICY_FILE = os.path.join(
    OUTPUT_DIR,
    "policy_decisions.csv"
)


# ============================================================
# CLEAN DATA FOR JSON
# ============================================================

def clean_value(value):

    # Handle None
    if value is None:
        return None

    # Handle NaN / Infinity
    if isinstance(value, float):

        if math.isnan(value) or math.isinf(value):
            return None

    return value


def dataframe_to_records(df):

    records = df.to_dict(
        orient="records"
    )

    cleaned_records = []

    for record in records:

        cleaned_record = {
            key: clean_value(value)
            for key, value in record.items()
        }

        cleaned_records.append(
            cleaned_record
        )

    return cleaned_records


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "RecoverAI Data API is running",
        "version": "1.0.0"
    }


# ============================================================
# METRICS
# ============================================================

@app.get("/metrics")
def get_metrics():

    if not os.path.exists(METRICS_FILE):

        raise HTTPException(
            status_code=404,
            detail="final_metrics.json not found"
        )

    with open(
        METRICS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        metrics = json.load(file)

    return metrics


# ============================================================
# RECOVERY OUTCOMES
# ============================================================

@app.get("/recovery-outcomes")
def get_recovery_outcomes():

    if not os.path.exists(RECOVERY_FILE):

        raise HTTPException(
            status_code=404,
            detail="recovery_outcomes.csv not found"
        )

    df = pd.read_csv(
        RECOVERY_FILE
    )

    records = dataframe_to_records(
        df
    )

    return {
        "count": len(records),
        "data": records
    }


# ============================================================
# EXCEPTIONS
# ============================================================

@app.get("/exceptions")
def get_exceptions():

    if not os.path.exists(RECOVERY_FILE):

        raise HTTPException(
            status_code=404,
            detail="recovery_outcomes.csv not found"
        )

    df = pd.read_csv(
        RECOVERY_FILE
    )

    if "outcome" not in df.columns:

        raise HTTPException(
            status_code=500,
            detail="Column 'outcome' not found"
        )

    exceptions = df[
        df["outcome"].astype(str).str.lower()
        == "failed"
    ]

    records = dataframe_to_records(
        exceptions
    )

    return {
        "count": len(records),
        "data": records
    }


# ============================================================
# POLICY DECISIONS
# ============================================================

@app.get("/policy-decisions")
def get_policy_decisions():

    if not os.path.exists(POLICY_FILE):

        raise HTTPException(
            status_code=404,
            detail="policy_decisions.csv not found"
        )

    df = pd.read_csv(
        POLICY_FILE
    )

    records = dataframe_to_records(
        df
    )

    return {
        "count": len(records),
        "data": records
    }


# ============================================================
# POLICY SUMMARY
# ============================================================

@app.get("/policy-summary")
def get_policy_summary():

    if not os.path.exists(POLICY_FILE):

        raise HTTPException(
            status_code=404,
            detail="policy_decisions.csv not found"
        )

    df = pd.read_csv(
        POLICY_FILE
    )

    if "action" not in df.columns:

        raise HTTPException(
            status_code=500,
            detail="Column 'action' not found"
        )

    summary = (
        df["action"]
        .value_counts()
        .to_dict()
    )

    return summary

# ============================================================
# RUN COMPLETE RECOVERY EVALUATION
# ============================================================

@app.post("/run-evaluation")
def run_evaluation():

    pipeline_file = os.path.join(
        BASE_DIR,
        "backend",
        "pipeline.py"
    )

    if not os.path.exists(pipeline_file):

        raise HTTPException(
            status_code=404,
            detail="pipeline.py not found"
        )

    try:

        result = subprocess.run(
            [
                sys.executable,
                pipeline_file
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:

            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Pipeline failed",
                    "output": result.stdout,
                    "error": result.stderr
                }
            )

        return {
            "status": "success",
            "message": "RecoverAI evaluation completed",
            "output": result.stdout
        }

    except subprocess.TimeoutExpired:

        raise HTTPException(
            status_code=500,
            detail="Pipeline timed out"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )