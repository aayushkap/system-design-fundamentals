import pandas as pd
import numpy as np

# Load data
print("Loading data...")
train_trans = pd.read_csv('./data/train_transaction.csv')
train_id = pd.read_csv('./data/train_identity.csv')
test_trans = pd.read_csv('./data/test_transaction.csv')
test_id = pd.read_csv('./data/test_identity.csv')

# Merge data
print("Merging datasets...")
train = pd.merge(train_trans, train_id, on='TransactionID', how='left')
test = pd.merge(test_trans, test_id, on='TransactionID', how='left')

# Preserve key columns that might have high missing values
key_columns = ['P_emaildomain', 'R_emaildomain', 'DeviceType', 'DeviceInfo']

def handle_missing(df, key_cols):
    # Create copy to avoid fragmentation warnings
    df = df.copy()

    # Preserve key columns even if missing
    all_cols = df.columns.tolist()
    cols_to_clean = [col for col in all_cols if col not in key_cols]

    # Drop non-key columns with >70% missing
    df_clean = df[cols_to_clean].dropna(thresh=0.3*len(df), axis=1)

    # Combine key columns back
    df = pd.concat([df[key_cols], df_clean], axis=1)

    # Fill numericals with median
    num_cols = df.select_dtypes(include=np.number).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())

    # Fill categoricals with 'missing'
    cat_cols = df.select_dtypes(include='object').columns
    for col in cat_cols:
        df[col] = df[col].fillna('missing')

    return df

print("Handling missing values...")
train = handle_missing(train, key_columns)
test = handle_missing(test, key_columns)

# Feature engineering with safety checks
print("Engineering features...")

# We create TransactionHour based on TransactionDT.
train['TransactionHour'] = train['TransactionDT'] // 3600 % 24
test['TransactionHour'] = test['TransactionDT'] // 3600 % 24

# We create AmtPerCard based on card1. This feature is the average transaction amount per card. Outlier amounts may signal fraud.
if 'card1' in train.columns:
    card_avg = train.groupby('card1')['TransactionAmt'].mean().to_dict()
    train['AmtPerCard'] = train['card1'].map(card_avg)
    test['AmtPerCard'] = test['card1'].map(card_avg)

    # Avoid division by zero
    train['AmtPerCard'] = train['TransactionAmt'] / train['AmtPerCard'].replace(0, 1)
    test['AmtPerCard'] = test['TransactionAmt'] / test['AmtPerCard'].replace(0, 1)
else:
    print("card1 column missing - skipping AmtPerCard feature")

# How frequently each category occurs and use that as a new feature.
# This helps the model understand the rarity of a value. More rare categories may indicate unusual behavior.
for col in ['ProductCD', 'P_emaildomain', 'R_emaildomain']:
    if col in train.columns:
        freq = train[col].value_counts(normalize=True)
        train[f'{col}_freq'] = train[col].map(freq)
        test[f'{col}_freq'] = test[col].map(freq)
    else:
        print(f"Skipping frequency encoding for {col} - column not present")


# 1. Transaction velocity features (critical for fraud detection)
train['TxCount_24h'] = train.groupby('card1')['TransactionID'].transform('count')
test['TxCount_24h'] = test['card1'].map(train.groupby('card1')['TransactionID'].count().fillna(1))

# 2. High-risk email domains
risky_domains = ['protonmail.com', 'mail.ru', 'yandex.ru', 'tutanota.com']
train['RiskyEmail'] = train['P_emaildomain'].apply(lambda x: 1 if any(d in str(x) for d in risky_domains) else 0)
test['RiskyEmail'] = test['P_emaildomain'].apply(lambda x: 1 if any(d in str(x) for d in risky_domains) else 0)

# 3. Time since last transaction
train.sort_values(['card1', 'TransactionDT'], inplace=True)
train['TimeSinceLastTx'] = train.groupby('card1')['TransactionDT'].diff()
test.sort_values(['card1', 'TransactionDT'], inplace=True)
test['TimeSinceLastTx'] = test.groupby('card1')['TransactionDT'].diff()

print(f"Final train shape: {train.shape}")
print(f"Final test shape: {test.shape}")
print("Feature engineering completed successfully!")

"""
TransactionAmt: The amount of the transaction.
TransactionHour: Hour of the day when the transaction occurred.
ProductCD_freq: Frequency of the product code in the training set (W, C, R, S, H).
card 1 - card 5: Hashed values for different parts of the card, like card ID, card type, card issuing bank, etc. These can be used to group transactions from the same card or user.
addr1, addr2: Address information, which can help identify the location of the transaction.
dist1, dist2: Distances from the billing address to the shipping address, which can indicate potential fraud if they are unusually high.
C1 - C14: Various categorical features that can provide additional context about the transaction.
D1, D2, D10, D15: Time-related features that can indicate the timing of the transaction. Helpful for identifying behavior patterns.
V281 - V287: Additional features that may capture specific behaviors or characteristics of the transaction. Despite being anonymized, they can still provide valuable information for fraud detection.
"""
# The thing about ML is, aslong as the patterns behave consistently, the model can learn from them. Even if we do not know the exact meaning of the features, they can still be useful for classification tasks like fraud detection.

# Check basic fraud distribution
fraud_pct = train['isFraud'].value_counts(normalize=True) * 100
print(f"Fraud distribution:\n{fraud_pct}")

# Select features - we'll use a robust set that should be available
potential_features = [
    'TransactionAmt', 'TransactionHour', 'ProductCD_freq', 'TxCount_24h',
    'RiskyEmail', 'TimeSinceLastTx',
    'card1', 'card2', 'card3', 'card5',
    'addr1', 'addr2', 'dist1', 'dist2',
    'C1', 'C2', 'C4', 'C5', 'C6', 'C11', 'C12', 'C13', 'C14',
    'D1', 'D2', 'D10', 'D15',
    'V281', 'V282', 'V283', 'V284', 'V285', 'V286', 'V287'
]

# Only include columns that actually exist
final_features = [f for f in potential_features if f in train.columns]
print(f"\nUsing {len(final_features)} features:\n{final_features}")

# Prepare training data
X = train[final_features]
y = train['isFraud']

import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt

# Split into train/validation sets
X_train, X_val, y_train, y_val = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y  # Maintain fraud ratio in both sets
)

# Calculate class weights (critical for fraud detection)
fraud_ratio = y_train.mean()
scale_pos_weight = (1 - fraud_ratio) / fraud_ratio
print(f"Using scale_pos_weight: {scale_pos_weight:.2f}")

# Configure LightGBM parameters
params = {
    'objective': 'binary',
    'boosting_type': 'gbdt',
    'metric': 'auc',
    'learning_rate': 0.01,  # Reduced for better convergence
    'num_leaves': 127,  # Increased complexity
    'max_depth': -1,
    'min_child_samples': 500,  # Reduced overfitting
    'subsample': 0.6,
    'colsample_bytree': 0.5,
    'reg_alpha': 0.5,  # Stronger regularization
    'reg_lambda': 0.5,
    'scale_pos_weight': scale_pos_weight * 1.5,  # More weight to fraud
    'n_jobs': -1,
    'random_state': 42
}

# Create datasets
train_data = lgb.Dataset(X_train, label=y_train)
val_data = lgb.Dataset(X_val, label=y_val)

# Train model with early stopping
model = lgb.train(
    params,
    train_data,
    num_boost_round=1000,
    valid_sets=[val_data],
    callbacks=[
        lgb.early_stopping(stopping_rounds=50, verbose=True),
        lgb.log_evaluation(period=50)
    ]
)

# Evaluate model
y_pred_proba = model.predict(X_val)
y_pred = (y_pred_proba > 0.3).astype(int) # Reducing this increases recall, which means less false negatives (less frauds missed)
# false negatives (missed fraud) are more costly than false positives

print("\n" + "="*50)
print(f"Validation AUC: {roc_auc_score(y_val, y_pred_proba):.4f}")
print("\nClassification Report:")
print(classification_report(y_val, y_pred))
print("\nConfusion Matrix:")
print(confusion_matrix(y_val, y_pred))

# Feature importance
lgb.plot_importance(model, max_num_features=20, figsize=(10, 6))
plt.title("Top 20 Feature Importance")
plt.show()

print("Production Feature Set:")
for i, feature in enumerate(final_features, 1):
    print(f"{i}. {feature}")