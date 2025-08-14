import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import mlflow
import mlflow.lightgbm
import os
import tempfile

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME"))

# Constants declaration
RISKY_DOMAINS = ["protonmail.com", "mail.ru", "yandex.ru", "tutanota.com"]
KEY_COLUMNS = ["P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo"]
POTENTIAL_FEATURES = [
    "TransactionAmt",
    "TransactionHour",
    "ProductCD_freq",
    "TxCount_24h",
    "RiskyEmail",
    "TimeSinceLastTx",
    "card1",
    "card2",
    "card3",
    "card5",
    "addr1",
    "addr2",
    "dist1",
    "dist2",
    # "C1",
    # "C2",
    # "C4",
    # "C5",
    # "C6",
    # "C11",
    # "C12",
    # "C13",
    # "C14",
    # "D1",
    # "D2",
    # "D10",
    # "D15",
    # "V281",
    # "V282",
    # "V283",
    # "V284",
    # "V285",
    # "V286",
    # "V287",
]


def load_data():
    """Load and merge transaction and identity datasets"""
    print("Loading data...")
    print(f"Currrent Directory: {os.getcwd()}")
    train_trans = pd.read_csv("./data/train_transaction.csv")
    train_id = pd.read_csv("./data/train_identity.csv")
    test_trans = pd.read_csv("./data/test_transaction.csv")
    test_id = pd.read_csv("./data/test_identity.csv")

    train = pd.merge(train_trans, train_id, on="TransactionID", how="left")
    test = pd.merge(test_trans, test_id, on="TransactionID", how="left")
    return train, test


def handle_missing(df, key_cols):
    """Handle missing values while preserving key columns"""
    df = df.copy()
    all_cols = df.columns.tolist()
    cols_to_clean = [col for col in all_cols if col not in key_cols]

    # Drop non-key columns with >70% missing
    df_clean = df[cols_to_clean].dropna(thresh=0.3 * len(df), axis=1)
    df = pd.concat([df[key_cols], df_clean], axis=1)

    # Fill numericals with median
    num_cols = df.select_dtypes(include=np.number).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())

    # Fill categoricals with 'missing'
    cat_cols = df.select_dtypes(include="object").columns
    for col in cat_cols:
        df[col] = df[col].fillna("missing")

    return df


def engineer_features(train, test):
    """Create new features for both train and test datasets"""
    # Time-based features
    for df in [train, test]:
        df["TransactionHour"] = df["TransactionDT"] // 3600 % 24

    # Card-based features
    if "card1" in train.columns:
        card_avg = train.groupby("card1")["TransactionAmt"].mean().to_dict()
        train["AmtPerCard"] = train["card1"].map(card_avg)
        test["AmtPerCard"] = test["card1"].map(card_avg)

        # Avoid division by zero
        train["AmtPerCard"] = train["TransactionAmt"] / train["AmtPerCard"].replace(
            0, 1
        )
        test["AmtPerCard"] = test["TransactionAmt"] / test["AmtPerCard"].replace(0, 1)
    else:
        print("Skipping AmtPerCard - 'card1' column missing")

    # Frequency encoding
    for col in ["ProductCD", "P_emaildomain", "R_emaildomain"]:
        if col in train.columns:
            freq = train[col].value_counts(normalize=True)
            train[f"{col}_freq"] = train[col].map(freq)
            test[f"{col}_freq"] = test[col].map(freq)
        else:
            print(f"Skipping frequency encoding - '{col}' not present")

    # Transaction velocity
    train["TxCount_24h"] = train.groupby("card1")["TransactionID"].transform("count")
    test["TxCount_24h"] = test["card1"].map(
        train.groupby("card1")["TransactionID"].count().fillna(1)
    )

    # Email risk features
    for df in [train, test]:
        df["RiskyEmail"] = df["P_emaildomain"].apply(
            lambda x: 1 if any(d in str(x) for d in RISKY_DOMAINS) else 0
        )

    # Time since last transaction
    for df in [train, test]:
        df.sort_values(["card1", "TransactionDT"], inplace=True)
        df["TimeSinceLastTx"] = df.groupby("card1")["TransactionDT"].diff()

    print(f"Final train shape: {train.shape}")
    print(f"Final test shape: {test.shape}")
    return train, test


def prepare_data(train):
    """Prepare feature matrix and target vector with validation split"""
    # Check fraud distribution
    fraud_pct = train["isFraud"].value_counts(normalize=True) * 100
    print(f"Fraud distribution:\n{fraud_pct}")

    # Select existing features
    final_features = [f for f in POTENTIAL_FEATURES if f in train.columns]
    print(f"\nUsing {len(final_features)} features")

    X = train[final_features]
    y = train["isFraud"]
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def train_and_evaluate(X_train, y_train, X_val, y_val):
    """Train LightGBM model and evaluate performance"""
    # Compute class weight
    fraud_ratio = y_train.mean()
    scale_pos_weight = (1 - fraud_ratio) / fraud_ratio

    # Model parameters
    params = {
        # Type of machine learning task. 'binary' means binary classification (e.g., fraud vs. not fraud).
        "objective": "binary",
        # Boosting algorithm to use. 'gbdt' is Gradient Boosting Decision Tree, which builds an ensemble of decision trees sequentially.
        "boosting_type": "gbdt",
        # Evaluation metric used during training. 'auc' stands for Area Under the ROC Curve, useful for imbalanced classification tasks.
        "metric": "auc",
        # Learning rate. Lower values make the model learn more slowly but can improve generalization.
        "learning_rate": 0.01,
        # Maximum number of leaves per tree. Higher values can improve learning capacity but risk overfitting.
        "num_leaves": 127,
        # Minimum number of samples required to form a leaf node. Helps control overfitting by ensuring leaves are not too specific.
        "min_child_samples": 500,
        # Fraction of training data to use for fitting each individual tree (row sampling).
        "subsample": 0.6,
        # Fraction of features to consider when building each tree (column sampling). Reduces correlation between trees.
        "colsample_bytree": 0.5,
        # L1 regularization term on leaf weights. Helps prevent overfitting by penalizing large leaf weights.
        "reg_alpha": 0.5,
        # L2 regularization term on leaf weights. Also helps prevent overfitting.
        "reg_lambda": 0.5,
        # Weighting factor to balance positive and negative classes. Especially important in imbalanced datasets (like fraud detection).
        "scale_pos_weight": scale_pos_weight
        * 1.5,  # Multiplied by 1.5 for extra emphasis on positive (minority) class.
        # Seed for reproducibility. Ensures the same result each time you run the model.
        "random_state": 42,
    }

    # Create datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val)

    # Train model
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(50)],
    )

    # Generate predictions
    y_pred_proba = model.predict(X_val)
    y_pred = (y_pred_proba > 0.3).astype(int)

    # Calculate metrics
    auc = roc_auc_score(y_val, y_pred_proba)
    report = classification_report(y_val, y_pred, output_dict=True)
    cm = confusion_matrix(y_val, y_pred)

    return model, auc, report, cm, params


def log_results(model, auc, report, cm):
    """Log model and metrics to MLflow"""
    mlflow.log_metric("validation_auc", auc)
    mlflow.log_metric("precision", report["1"]["precision"])
    mlflow.log_metric("recall", report["1"]["recall"])
    mlflow.log_metric("f1_score", report["1"]["f1-score"])

    # Log confusion matrix
    with tempfile.TemporaryDirectory() as tmpdir:
        cm_df = pd.DataFrame(
            cm,
            index=["actual_0", "actual_1"],
            columns=["pred_0", "pred_1"]
        )
        cm_csv = os.path.join(tmpdir, "confusion_matrix.csv")
        cm_df.to_csv(cm_csv)
        mlflow.log_artifact(cm_csv, artifact_path="metrics")



def orchestrate():
    """Main orchestration function for the ML pipeline"""

    # Data pipeline
    train, test = load_data()
    train = handle_missing(train, KEY_COLUMNS)
    test = handle_missing(test, KEY_COLUMNS)
    train, test = engineer_features(train, test)
    X_train, X_val, y_train, y_val = prepare_data(train)

    # Model pipeline
    with mlflow.start_run(run_name=os.getenv("MLFLOW_EXPERIMENT_NAME")):
        model, auc, report, cm, params = train_and_evaluate(X_train, y_train, X_val, y_val)
        mlflow.log_params(
            {
                "test_size": 0.2,
                "random_state": params.get("random_state"),
                "features_used": len(
                    [f for f in POTENTIAL_FEATURES if f in train.columns]
                ),
            }
        )
        log_results(model, auc, report, cm)

    print("Pipeline executed successfully!")


if __name__ == "__main__":
    orchestrate()
