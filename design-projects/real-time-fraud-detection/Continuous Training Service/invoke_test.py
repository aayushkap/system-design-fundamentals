import pandas as pd
import os
import numpy as np

# Constants
KEY_COLUMNS = ["P_emaildomain", "R_emaildomain", "DeviceType", "DeviceInfo"]

POTENTIAL_FEATURES = [
    "TransactionAmt",
    "TransactionHour",
    "ProductCD_freq",
    "TxCount_24h",
    "RiskyEmail",
    "TimeSinceLastTx",
    # "card1",
    "card2",
    "card3",
    "card5",
    "addr1",
    "addr2",
    "dist1",
    "dist2",
]

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

# Load merged data
train_trans = pd.read_csv("./data/train_transaction.csv")
train_id = pd.read_csv("./data/train_identity.csv")
train = pd.merge(train_trans, train_id, on="TransactionID", how="left")

# Handle missing values first
train = handle_missing(train, key_cols=KEY_COLUMNS)

# Now keep only features that exist after cleaning
existing_features = [f for f in POTENTIAL_FEATURES if f in train.columns]

# Print first 5 rows
print(train[existing_features].head(10))

# Optional: print the list of features that survived
print("\nFeatures available for the model:")
print(existing_features)

# for card 1, 2, 3, 5, print all the unique values
for col in ["card1", "card2", "card3", "card5"]:
    print(f"\nUnique values in {col}:")
    print(train[col].unique())
