import pickle
from pathlib import Path
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_FILE = (
    PROJECT_ROOT
    / "machine_learning"
    / "models"
    / "fraud_model.pkl"
)


FEATURES = [
    "Amount",
    "Is_PEP",
    "Account_Age_Days",
    "Transaction_Count_24H",
    "Total_Amount_24H",
    "IP_Risk_Score",
    "Previous_Fraud_Count"
]


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    with open(MODEL_FILE, "rb") as file:
        model_package = pickle.load(file)

    return model_package


# ============================================================
# PREPARE TRANSACTION
# ============================================================

def prepare_features(transaction, model_package):

    values = [
        float(transaction["Amount"]),
        float(transaction["Is_PEP"]),
        float(transaction["Account_Age_Days"]),
        float(transaction["Transaction_Count_24H"]),
        float(transaction["Total_Amount_24H"]),
        float(transaction["IP_Risk_Score"]),
        float(transaction["Previous_Fraud_Count"])
    ]

    X = np.array(
        [values],
        dtype=np.float64
    )

    mean = model_package["mean"]
    std = model_package["std"]

    X_scaled = (X - mean) / std

    return X_scaled


# ============================================================
# PREDICT FRAUD
# ============================================================

def predict_transaction(transaction):

    model_package = load_model()

    model = model_package["model"]

    X = prepare_features(
        transaction,
        model_package
    )

    W1 = model["W1"]
    b1 = model["b1"]

    W2 = model["W2"]
    b2 = model["b2"]

    W3 = model["W3"]
    b3 = model["b3"]

    # Forward pass

    A1 = np.tanh(
        X @ W1 + b1
    )

    A2 = np.tanh(
        A1 @ W2 + b2
    )

    output = A2 @ W3 + b3

    output = np.clip(
        output,
        -50,
        50
    )

    probability = (
        1.0 / (1.0 + np.exp(-output))
    )[0][0]

    fraud_probability = probability * 100

    prediction = (
        "FRAUD"
        if probability >= model_package["threshold"]
        else "NORMAL"
    )

    return {
        "fraud_probability": round(
            fraud_probability,
            2
        ),
        "ml_prediction": prediction
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_transaction = {

        "Amount": 450000,

        "Is_PEP": 0,

        "Account_Age_Days": 500,

        "Transaction_Count_24H": 4,

        "Total_Amount_24H": 1800000,

        "IP_Risk_Score": 30,

        "Previous_Fraud_Count": 0
    }

    result = predict_transaction(
        test_transaction
    )

    print()
    print("=" * 60)
    print("FCCM ML FRAUD PREDICTION TEST")
    print("=" * 60)

    print(
        f"Fraud Probability : "
        f"{result['fraud_probability']}%"
    )

    print(
        f"ML Prediction     : "
        f"{result['ml_prediction']}"
    )

    print("=" * 60)