import os
import subprocess
import sys


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

BACKEND_DIR = os.path.join(
    BASE_DIR,
    "backend"
)


# ============================================================
# RUN PYTHON FILE
# ============================================================

def run_file(file_path):

    print()
    print("=" * 60)
    print(f"RUNNING: {file_path}")
    print("=" * 60)

    result = subprocess.run(
        [
            sys.executable,
            file_path
        ],
        cwd=BASE_DIR,
        capture_output=False,
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8"
        }
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"Pipeline failed: {file_path}"
        )

    print(
        f"COMPLETED: {file_path}"
    )


# ============================================================
# COMPLETE RECOVERY PIPELINE
# ============================================================

def run_pipeline():

    print()
    print("=" * 60)
    print("RecoverAI - COMPLETE PIPELINE")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Detection
    # --------------------------------------------------------

    detection_file = os.path.join(
        BASE_DIR,
        "Detection Layer — ML Model__1.py"
    )

    run_file(
        detection_file
    )

    # --------------------------------------------------------
    # 2. Diagnosis
    # --------------------------------------------------------

    diagnosis_file = os.path.join(
        BASE_DIR,
        "Diagnosis Layer__2.py"
    )

    run_file(
        diagnosis_file
    )

    # --------------------------------------------------------
    # 3. Policy
    # --------------------------------------------------------

    policy_file = os.path.join(
        BASE_DIR,
        "Policy Layer code__3.py"
    )

    run_file(
        policy_file
    )

    # --------------------------------------------------------
    # 4. Execution
    # --------------------------------------------------------

    execution_file = os.path.join(
        BACKEND_DIR,
        "Execution layer1.py"
    )

    run_file(
        execution_file
    )

    # --------------------------------------------------------
    # 5. Recovery Outcomes
    # --------------------------------------------------------

    recovery_file = os.path.join(
        BACKEND_DIR,
        "recovery_outcome_layer.py"
    )

    run_file(
        recovery_file
    )

    # --------------------------------------------------------
    # 6. Final Metrics
    # --------------------------------------------------------

    metrics_file = os.path.join(
        BACKEND_DIR,
        "final_metrics.py"
    )

    run_file(
        metrics_file
    )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RECOVERAI PIPELINE COMPLETE")
    print("=" * 60)

    print()
    print("Detection      OK")
    print("Diagnosis      OK")
    print("Policy         OK")
    print("Execution      OK")
    print("Recovery       OK")
    print("Metrics        OK")

    print()
    print("Dashboard can now refresh the results.")

    print("=" * 60)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    run_pipeline()