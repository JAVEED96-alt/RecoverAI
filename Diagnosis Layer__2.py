"""
Diagnosis Layer — ML Model
---------------------------
Predicts `root_cause_bucket` (the action-relevant diagnosis category)
using ONLY signals available at detection time:
    - error_code        (coarse: BAD_REQUEST_ERROR / GATEWAY_ERROR / SERVER_ERROR)
    - amount
    - method             (card / upi / netbanking / wallet / emandate)
    - hour_of_day, day_of_week   (derived from timestamp)
    - customer_fail_count  (engineered: how many times this customer has failed before)

We deliberately EXCLUDE `error_reason` and `error_description` as features —
those are just a verbose restatement of the label itself (root_cause_bucket
was derived directly from them), so using them would be label leakage, not
a real model. error_code alone is coarse/ambiguous (e.g. BAD_REQUEST_ERROR
maps to 5 different buckets), which is exactly what makes this a real,
non-trivial classification problem.

Model: Random Forest (baseline: Logistic Regression) — good fit because:
  - mostly categorical features, small dataset (~300 rows)
  - gives feature_importances_ for explainability
  - no scaling / heavy preprocessing needed
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import os

# ------------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------------
df = pd.read_csv("razorpay_failed_payments_synthetic (1).csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# ------------------------------------------------------------------
# 2. Feature engineering
# ------------------------------------------------------------------
df["hour_of_day"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.dayofweek  # 0=Mon
df = df.sort_values("timestamp")

# Running count of prior failures per customer (as-of-that-event, no leakage from future)
df["customer_fail_count"] = df.groupby("customer_id").cumcount()

FEATURES = ["error_code", "amount", "method", "hour_of_day",
            "day_of_week", "customer_fail_count"]
TARGET = "root_cause_bucket"

X = df[FEATURES]
y = df[TARGET]

print("Class distribution:\n", y.value_counts(), "\n")

# ------------------------------------------------------------------
# 3. Train/test split (stratified to preserve class balance)
# ------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# ------------------------------------------------------------------
# 4. Preprocessing + model pipeline
# ------------------------------------------------------------------
categorical_features = ["error_code", "method"]
numeric_features = ["amount", "hour_of_day", "day_of_week", "customer_fail_count"]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ],
    remainder="passthrough"  # numeric features pass through unchanged
)

# --- Baseline: Logistic Regression ---
baseline_pipe = Pipeline([
    ("prep", preprocessor),
    ("clf", LogisticRegression(max_iter=1000))
])
baseline_pipe.fit(X_train, y_train)
baseline_preds = baseline_pipe.predict(X_test)
baseline_acc = accuracy_score(y_test, baseline_preds)

# --- Main model: Random Forest ---
rf_pipe = Pipeline([
    ("prep", preprocessor),
    ("clf", RandomForestClassifier(
        n_estimators=200, max_depth=8, random_state=42, class_weight="balanced"
    ))
])
rf_pipe.fit(X_train, y_train)
rf_preds = rf_pipe.predict(X_test)
rf_acc = accuracy_score(y_test, rf_preds)

print(f"Baseline (Logistic Regression) accuracy: {baseline_acc:.3f}")
print(f"Random Forest accuracy:                  {rf_acc:.3f}\n")

print("=== Random Forest — classification report ===")
print(classification_report(y_test, rf_preds, zero_division=0))

# ------------------------------------------------------------------
# 5. Feature importance (explainability)
# ------------------------------------------------------------------
ohe = rf_pipe.named_steps["prep"].named_transformers_["cat"]
cat_feature_names = list(ohe.get_feature_names_out(categorical_features))
all_feature_names = cat_feature_names + numeric_features

importances = rf_pipe.named_steps["clf"].feature_importances_
imp_df = pd.DataFrame({
    "feature": all_feature_names,
    "importance": importances
}).sort_values("importance", ascending=False)

print("=== Top feature importances ===")
print(imp_df.head(10).to_string(index=False))

plt.figure(figsize=(8, 5))
top_imp = imp_df.head(10)
plt.barh(top_imp["feature"][::-1], top_imp["importance"][::-1], color="#4C72B0")
plt.xlabel("Importance")
plt.title("Diagnosis Model — Top Feature Importances")
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/feature_importance.png", dpi=150)
print("\nSaved feature importance chart -> feature_importance.png")

# ------------------------------------------------------------------
# 6. Confusion matrix (as CSV for easy inspection)
# ------------------------------------------------------------------
labels = sorted(y.unique())
cm = confusion_matrix(y_test, rf_preds, labels=labels)
cm_df = pd.DataFrame(cm, index=labels, columns=labels)
cm_df.to_csv("/mnt/user-data/outputs/confusion_matrix.csv")
print("\nSaved confusion matrix -> confusion_matrix.csv")

# ------------------------------------------------------------------
# 7. Save predictions with confidence (feeds the Policy Layer next)
# ------------------------------------------------------------------
probs = rf_pipe.predict_proba(X_test)
pred_confidence = probs.max(axis=1)

results = X_test.copy()
results["actual_bucket"] = y_test.values
results["predicted_bucket"] = rf_preds
results["confidence"] = pred_confidence
results.to_csv("diagnosis_predictions.csv", index=False)
print("Saved predictions with confidence -> diagnosis_predictions.csv")

# ------------------------------------------------------------------
# 8. Save the trained pipeline for reuse in the Policy Layer
# ------------------------------------------------------------------
joblib.dump(rf_pipe, "/mnt/user-data/outputs/diagnosis_model.pkl")
print("Saved trained model -> diagnosis_model.pkl")