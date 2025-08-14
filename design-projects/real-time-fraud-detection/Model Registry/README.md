# Model Training, Testing & Management

---

In this directory we handle the training and testing of our machine learning models using MLflow for tracking experiments and managing model versions. The code includes the setup of model parameters, training the model, logging metrics, and saving the trained model for future use.

We use `LightGBM` as our machine learning framework, which is efficient for large datasets and provides good performance for classification tasks like fraud detection. Machine learning frameworks like LightGBM are pre-built tools that provide optimized algorithms for training models, allowing us to focus on the data and the problem rather than the underlying implementation details.

We use `Gradient Boosting Decision Trees` (GBDT) as our boosting algorithm. A boosting algorithm is a technique that combines multiple weak learners (in this case, decision trees) to create a strong predictive model.

    - A weak learner is a model that performs slightly better than random guessing (e.g., a shallow decision tree).
    - Boosting trains these weak learners sequentially, with each one learning from the errors of the previous.
    - Over time, it focuses more on the hard-to-predict samples.

In gradient boosting, we use `gradient descent` to minimize the loss function, which measures how well the model is performing. The model is trained iteratively, where each new tree corrects the errors made by the previous trees.

## Training Process

1. **Data Preparation**: The initial model is build from the [IEEE Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection/data) dataset. The data is split into training and validation sets.

   - We handle missing values by dropping rows with more than 70% missing values, using 'missing' for categoricals and medians for numerics.

2. **Feature Engineering**: We create new features based on existing ones. This allows us to provide the model with more expressive information, which can improve its performance.
   - We create `TransactionHour`, `AmtPerCard`, `TimeSinceLastTx`, and `TxCount_24h` features to capture time based patterns and transaction behaviors.
   - We perform frequency encoding on the transaction email domains to capture the frequency of each domain in the dataset. It is logical that domains with more transactions are more likely to be legitimate.
   - We have a list of risky email domains that are known to be associated with fraud. We create a binary feature `RiskyDomain` to indicate whether the transaction email domain is in this list.

[Feature Importance](./Figure_1.png) shows the importance of each feature in the model.The number against each features tells us the number of times the feature was used to split the data across all trees in the model. Higher values indicate more important features.

3. **Model Training**: We define some basic parameters for the LightGBM model.
   - The dataset is highly imbalanced, so we use the `AUC` (Area Under the ROC Curve) metric to evaluate the model's performance. This metric tells us the model's ability to distinguish between the positive class (fraud) and the negative class (non-fraud).
   - We use weighted sampling to handle the class imbalance, giving more weight to the minority class (fraud) during training.
