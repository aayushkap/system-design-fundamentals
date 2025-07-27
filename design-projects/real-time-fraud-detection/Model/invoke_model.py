import mlflow
import mlflow.lightgbm
import pandas as pd

from mlflow_train_test import (
    load_data,
    handle_missing,
    engineer_features,
    POTENTIAL_FEATURES,
    KEY_COLUMNS,
)

# 1) Define run & model URI
run_id = "8690438989484e2481073bbaf7e1f8df"
model_uri = f"runs:/{run_id}/model"

# 2) Load the model
loaded_model = mlflow.lightgbm.load_model(model_uri)

# 3) Load & preprocess both train & test (needed for group‑based features!)
train, test = load_data()
train = handle_missing(train, KEY_COLUMNS)
test  = handle_missing(test, KEY_COLUMNS)
train, test = engineer_features(train, test)

# 4) Select the exact features you trained on
feature_cols = [f for f in POTENTIAL_FEATURES if f in test.columns]
X_test = test[feature_cols]

# 5) Pick one random row
sample = X_test.sample(n=1, random_state=42)
print(f"Sample features: {sample.columns.tolist()}")

# 6) Score it
proba_fraud = loaded_model.predict(sample)
pred_label = (proba_fraud > 0.5).astype(int)  # adjust threshold if desired

print(f"Predicted fraud probability: {proba_fraud[0]:.4f}")
print(f"Predicted label (0=legit, 1=fraud): {pred_label[0]}")
