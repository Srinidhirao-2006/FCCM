import csv
import pickle
from pathlib import Path

import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "transactions.csv"
MODEL_DIR = PROJECT_ROOT / "machine_learning" / "models"
MODEL_FILE = MODEL_DIR / "fraud_model.pkl"


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "Amount",
    "Is_PEP",
    "Account_Age_Days",
    "Transaction_Count_24H",
    "Total_Amount_24H",
    "IP_Risk_Score",
    "Previous_Fraud_Count"
]

TARGET = "Is_Fraud"


# ============================================================
# LOAD DATA
# ============================================================

def load_dataset():

    X = []
    y = []

    with open(DATA_FILE, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            features = [
                float(row["Amount"]),
                float(row["Is_PEP"]),
                float(row["Account_Age_Days"]),
                float(row["Transaction_Count_24H"]),
                float(row["Total_Amount_24H"]),
                float(row["IP_Risk_Score"]),
                float(row["Previous_Fraud_Count"])
            ]

            X.append(features)
            y.append(int(row[TARGET]))

    return np.array(X, dtype=np.float64), np.array(y, dtype=np.float64)


# ============================================================
# STANDARDIZATION
# ============================================================

def standardize(X):

    mean = X.mean(axis=0)
    std = X.std(axis=0)

    # Prevent division by zero
    std[std == 0] = 1

    X_scaled = (X - mean) / std

    return X_scaled, mean, std


# ============================================================
# ACTIVATION FUNCTIONS
# ============================================================

def sigmoid(x):

    x = np.clip(x, -50, 50)

    return 1.0 / (1.0 + np.exp(-x))


def sigmoid_derivative(output):

    return output * (1.0 - output)


# ============================================================
# TRAIN NEURAL NETWORK
# ============================================================

def train_model(X, y):

    np.random.seed(42)

    n_samples = X.shape[0]
    n_features = X.shape[1]

    # --------------------------------------------------------
    # Network architecture
    #
    # 7 input features
    #       ↓
    # 16 hidden neurons
    #       ↓
    # 8 hidden neurons
    #       ↓
    # 1 output neuron
    # --------------------------------------------------------

    hidden1 = 16
    hidden2 = 8

    # Xavier-style initialization

    W1 = np.random.randn(n_features, hidden1) * np.sqrt(
        2.0 / n_features
    )

    b1 = np.zeros((1, hidden1))

    W2 = np.random.randn(hidden1, hidden2) * np.sqrt(
        2.0 / hidden1
    )

    b2 = np.zeros((1, hidden2))

    W3 = np.random.randn(hidden2, 1) * np.sqrt(
        2.0 / hidden2
    )

    b3 = np.zeros((1, 1))

    # --------------------------------------------------------
    # Class weights
    #
    # Fraud transactions are much fewer than normal
    # transactions, so give fraud examples more importance.
    # --------------------------------------------------------

    positive_count = np.sum(y == 1)
    negative_count = np.sum(y == 0)

    weight_positive = negative_count / positive_count

    sample_weights = np.where(
        y == 1,
        weight_positive,
        1.0
    ).reshape(-1, 1)

    learning_rate = 0.001
    epochs = 1500

    print()
    print("=" * 70)
    print("TRAINING NUMPY NEURAL NETWORK")
    print("=" * 70)

    print(f"Training samples : {n_samples}")
    print(f"Input features   : {n_features}")
    print(f"Hidden layer 1   : {hidden1}")
    print(f"Hidden layer 2   : {hidden2}")
    print(f"Fraud weight     : {weight_positive:.2f}")
    print(f"Epochs           : {epochs}")

    # --------------------------------------------------------
    # Training loop
    # --------------------------------------------------------

    for epoch in range(epochs):

        # Forward pass

        Z1 = X @ W1 + b1
        A1 = np.tanh(Z1)

        Z2 = A1 @ W2 + b2
        A2 = np.tanh(Z2)

        Z3 = A2 @ W3 + b3
        predictions = sigmoid(Z3)

        # ----------------------------------------------------
        # Weighted binary cross entropy
        # ----------------------------------------------------

        eps = 1e-8

        loss = -np.mean(
            sample_weights * (
                y.reshape(-1, 1) * np.log(predictions + eps)
                +
                (1 - y.reshape(-1, 1))
                * np.log(1 - predictions + eps)
            )
        )

        # ----------------------------------------------------
        # Backpropagation
        # ----------------------------------------------------

        dZ3 = (
            sample_weights
            * (predictions - y.reshape(-1, 1))
            / n_samples
        )

        dW3 = A2.T @ dZ3
        db3 = np.sum(dZ3, axis=0, keepdims=True)

        dA2 = dZ3 @ W3.T

        dZ2 = dA2 * (1 - A2 ** 2)

        dW2 = A1.T @ dZ2
        db2 = np.sum(dZ2, axis=0, keepdims=True)

        dA1 = dZ2 @ W2.T

        dZ1 = dA1 * (1 - A1 ** 2)

        dW1 = X.T @ dZ1
        db1 = np.sum(dZ1, axis=0, keepdims=True)

        # ----------------------------------------------------
        # Gradient descent
        # ----------------------------------------------------

        W3 -= learning_rate * dW3
        b3 -= learning_rate * db3

        W2 -= learning_rate * dW2
        b2 -= learning_rate * db2

        W1 -= learning_rate * dW1
        b1 -= learning_rate * db1

        # Print progress

        if (epoch + 1) % 100 == 0:

            print(
                f"Epoch {epoch + 1:4d}/{epochs} "
                f"| Loss: {loss:.6f}"
            )

    print()
    print("Training completed.")

    return {
        "W1": W1,
        "b1": b1,
        "W2": W2,
        "b2": b2,
        "W3": W3,
        "b3": b3
    }


# ============================================================
# PREDICTION
# ============================================================

def predict_proba(X, model):

    W1 = model["W1"]
    b1 = model["b1"]

    W2 = model["W2"]
    b2 = model["b2"]

    W3 = model["W3"]
    b3 = model["b3"]

    A1 = np.tanh(X @ W1 + b1)

    A2 = np.tanh(A1 @ W2 + b2)

    probabilities = sigmoid(A2 @ W3 + b3)

    return probabilities.ravel()


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(y_true, probabilities):

    predictions = (probabilities >= 0.5).astype(int)

    TP = np.sum((y_true == 1) & (predictions == 1))
    TN = np.sum((y_true == 0) & (predictions == 0))
    FP = np.sum((y_true == 0) & (predictions == 1))
    FN = np.sum((y_true == 1) & (predictions == 0))

    accuracy = (TP + TN) / len(y_true)

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0

    recall = TP / (TP + FN) if (TP + FN) > 0 else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "TP": TP,
        "TN": TN,
        "FP": FP,
        "FN": FN
    }


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

def calculate_feature_importance(model):

    W1 = model["W1"]

    importance = np.mean(
        np.abs(W1),
        axis=1
    )

    importance = importance / np.sum(importance)

    return importance


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

def train_test_split(X, y, test_size=0.20):

    np.random.seed(42)

    indices = np.arange(len(X))

    np.random.shuffle(indices)

    split_index = int(len(X) * (1 - test_size))

    train_indices = indices[:split_index]

    test_indices = indices[split_index:]

    return (
        X[train_indices],
        X[test_indices],
        y[train_indices],
        y[test_indices]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FCCM FRAUD DETECTION MODEL TRAINING")
    print("=" * 70)

    # Load dataset

    X, y = load_dataset()

    print()
    print(f"Dataset shape      : {X.shape}")
    print(f"Total transactions : {len(y)}")
    print(f"Fraud transactions : {int(np.sum(y))}")
    print(
        f"Fraud percentage   : "
        f"{np.mean(y) * 100:.2f}%"
    )

    # Train/test split

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20
    )

    print()
    print(f"Training samples   : {len(X_train)}")
    print(f"Testing samples    : {len(X_test)}")

    # Standardization

    X_train_scaled, mean, std = standardize(X_train)

    X_test_scaled = (
        (X_test - mean) / std
    )

    # Train

    model = train_model(
        X_train_scaled,
        y_train
    )

    # Test

    probabilities = predict_proba(
        X_test_scaled,
        model
    )

    metrics = calculate_metrics(
        y_test,
        probabilities
    )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("MODEL PERFORMANCE")
    print("=" * 70)

    print(
        f"Accuracy  : {metrics['accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision : {metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Recall    : {metrics['recall'] * 100:.2f}%"
    )

    print(
        f"F1 Score  : {metrics['f1'] * 100:.2f}%"
    )

    print()
    print("CONFUSION MATRIX")
    print("-" * 40)

    print(
        f"True Negative  : {metrics['TN']}"
    )

    print(
        f"False Positive : {metrics['FP']}"
    )

    print(
        f"False Negative : {metrics['FN']}"
    )

    print(
        f"True Positive  : {metrics['TP']}"
    )

    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    importance = calculate_feature_importance(model)

    print()
    print("=" * 70)
    print("FEATURE IMPORTANCE")
    print("=" * 70)

    feature_ranking = sorted(
        zip(FEATURES, importance),
        key=lambda x: x[1],
        reverse=True
    )

    for feature, score in feature_ranking:

        print(
            f"{feature:<30} "
            f"{score * 100:6.2f}%"
        )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    model_package = {
        "model": model,
        "features": FEATURES,
        "mean": mean,
        "std": std,
        "threshold": 0.5,
        "metrics": metrics
    }

    with open(
        MODEL_FILE,
        "wb"
    ) as file:

        pickle.dump(
            model_package,
            file
        )

    print()
    print("=" * 70)
    print("MODEL SAVED")
    print("=" * 70)

    print(
        f"Location: {MODEL_FILE}"
    )

    print()
    print("FCCM ML MODEL TRAINED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()