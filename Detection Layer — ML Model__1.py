"""
Detection Layer — ML Model
-----------------------------
Predicts `at_risk` (1 = will fail, 0 = will succeed) for a transaction,
using only signals available at/near transaction time — NOT the error
fields (those only exist after failure, so using them would be leakage;
a real detector must flag risk before or as the failure happens).

Features used:
    - amount
    - method
    - hour_of_day, day_of_week      (derived from timestamp)
    - customer_prior_fail_rate      (engineered: this customer's historical
                                      failure rate up to this point in time)
    - customer_txn_count_so_far     (engineered: how many transactions this
                                      customer has made so far — thin-history
                                      customers are often riskier)

Model: Random Forest (baseline: Logistic Regression), evaluated with
ROC-AUC (better than accuracy for imbalanced success/failure data) and
a precision-recall view since false negatives (missed at-risk txns) and
false positives (crying wolf on healthy txns) have different costs.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score, classification_report, precision_recall_curve,
    RocCurveDisplay, confusion_matrix
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib

# ------------------------------------------------------------------
# 1. Load + combine failed + successful transactions
# ------------------------------------------------------------------
failed = pd.read_csv("razorpay_failed_payments_synthetic (1).csv")
success = pd.read_csv("razorpay_successful_payments_synthetic.csv")

failed["at_risk"] = 1
success["at_risk"] = 0

df = pd.concat([failed, success], ignore_index=True)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

# ------------------------------------------------------------------
# 2. Feature engineering (time-ordered, no future leakage)
# ------------------------------------------------------------------
df["hour_of_day"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.dayofweek

# Expanding (as-of-that-point-in-time) customer failure rate & txn count
df["customer_txn_count_so_far"] = df.groupby("customer_id").cumcount()

def expanding_fail_rate(group):
    # fail rate BEFORE the current transaction (shift avoids leakage)
    return group["at_risk"].expanding().mean().shift(1)

df["customer_prior_fail_rate"] = (
    df.groupby("customer_id", group_keys=False).apply(expanding_fail_rate)
)
df["customer_prior_fail_rate"] = df["customer_prior_fail_rate"].fillna(0.0)  # no history yet -> assume neutral

FEATURES = ["amount", "method", "hour_of_day", "day_of_week",
            "customer_prior_fail_rate", "customer_txn_count_so_far"]
TARGET = "at_risk"

X = df[FEATURES]
y = df[TARGET]

print("Class balance:\n", y.value_counts(normalize=True).round(3), "\n")

# ------------------------------------------------------------------
# 3. Train/test split
# ------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

categorical_features = ["method"]
numeric_features = ["amount", "hour_of_day", "day_of_week",
                     "customer_prior_fail_rate", "customer_txn_count_so_far"]

preprocessor = ColumnTransformer(
    transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)],
    remainder="passthrough"
)

# --- Baseline ---
baseline_pipe = Pipeline([
    ("prep", preprocessor),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))
])
baseline_pipe.fit(X_train, y_train)
baseline_auc = roc_auc_score(y_test, baseline_pipe.predict_proba(X_test)[:, 1])

# --- Main model ---
rf_pipe = Pipeline([
    ("prep", preprocessor),
    ("clf", RandomForestClassifier(
        n_estimators=300, max_depth=6, random_state=42, class_weight="balanced"
    ))
])
rf_pipe.fit(X_train, y_train)
rf_probs = rf_pipe.predict_proba(X_test)[:, 1]
rf_auc = roc_auc_score(y_test, rf_probs)

print(f"Baseline (Logistic Regression) ROC-AUC: {baseline_auc:.3f}")
print(f"Random Forest ROC-AUC:                  {rf_auc:.3f}\n")

rf_preds = (rf_probs >= 0.5).astype(int)
print("=== Random Forest — classification report (threshold=0.5) ===")
print(classification_report(y_test, rf_preds, target_names=["not_at_risk", "at_risk"]))

# ------------------------------------------------------------------
# 4. ROC curve
# ------------------------------------------------------------------
plt.figure(figsize=(6, 6))
RocCurveDisplay.from_predictions(y_test, rf_probs, name="Random Forest")
plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random guess")
plt.title("Detection Model — ROC Curve")
plt.legend()
plt.tight_layout()
plt.savefig("detection_roc_curve.png", dpi=150)

# ------------------------------------------------------------------
# 5. Feature importance
# ------------------------------------------------------------------
ohe = rf_pipe.named_steps["prep"].named_transformers_["cat"]
cat_names = list(ohe.get_feature_names_out(categorical_features))
all_names = cat_names + numeric_features
importances = rf_pipe.named_steps["clf"].feature_importances_
imp_df = pd.DataFrame({"feature": all_names, "importance": importances}).sort_values(
    "importance", ascending=False
)
print("\n=== Feature importances ===")
print(imp_df.to_string(index=False))

plt.figure(figsize=(8, 5))
plt.barh(imp_df["feature"][::-1], imp_df["importance"][::-1], color="#C44E52")
plt.xlabel("Importance")
plt.title("Detection Model — Feature Importances")
plt.tight_layout()
plt.savefig("detection_feature_importance.png", dpi=150)

# ------------------------------------------------------------------
# 6. Save risk-scored output (feeds the Diagnosis Layer next)
# ------------------------------------------------------------------
results = X_test.copy()
results["actual_at_risk"] = y_test.values
results["risk_score"] = rf_probs
results["flagged_at_risk"] = rf_preds
results.to_csv("detection_risk_scores.csv", index=False)

joblib.dump(rf_pipe, "detection_model.pkl")
print("\nSaved model, risk scores, and charts.")