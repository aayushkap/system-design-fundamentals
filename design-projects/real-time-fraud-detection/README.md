Advanced Real-Time Credit-Card Fraud Detection System for thousands of Transactions.

This design project will cover the model training, version control, and end-to-end system design and implementation.

High level plan:

Debit cards and credit cards are handeled differently, as debit cards need to be handled in real-time, while credit cards can be handled asynchronously.

Debit Fraud Response: Hard stop immediately. Fraud checks must happen before approval of the transaction.
Credit Fraud Response: Can be slightly delayed

The EMV and ISO 8583 standards define a request/response model for card transactions. No webhooks.

Small Bank:

Average TPS (transactions per second):
- 50 k/day → ~0.6 tps (36 tpm)
- 200 k/day → ~2.3 tps (140 tpm)


gRPC - Calling a function on a remote server, with a response. Using HTTP/2 for performance. You can define workers using threadspools and RPC will internally handle queuing and load balancing. This is our built-in queuing system.

Peak TPS (e.g. lunch­time/after‑payroll spikes): roughly 5–10× the daily average → 3–20 tps (180–1,200 tpm).


1.  Offline Training (Batch) - https://www.kaggle.com/c/ieee-fraud-detection/data
    Collect a big dataset of past transactions across all users.

    Compute features for each transaction, e.g.:

        “Amount of this transaction” (raw)

        “# of transactions this user did in the last hour” (aggregate)

        “Average transaction amount for this user over the last 24 h”

        “Device risk score”

    Train one model (e.g. XGBoost) on those feature‑vectors → label (fraud or not).

    Validate model’s performance (ROC‑AUC, precision/recall).

    Save model (“Model v1.0”) into model registry.

    This happens periodically (e.g. nightly, weekly), whenever you have enough new labeled transactions to improve your model (Airflow + SparkML + MLflow).

2.  Online Inference (Real-Time)
    When a new transaction comes in, compute the same features as above.

    Load the latest model from the model registry.

    Get the feature vector for the new transaction, for that user (Redis / Cassandra).

    Pass the feature vector to the model for inference.

    Get the prediction (fraud or not).

    Return the prediction to the user.

    Update the user’s profile with the new transaction.
