import json
from pathlib import Path

import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_FILE = (
    PROJECT_ROOT
    / "machine_learning"
    / "models"
    / "pca_anomaly_model.npz"
)

METADATA_FILE = (
    PROJECT_ROOT
    / "machine_learning"
    / "models"
    / "pca_anomaly_metadata.json"
)


# ============================================================
# PCA CALIBRATION
# ============================================================

# The PCA model was originally trained using a conservative
# 95th-percentile anomaly threshold.
#
# We keep that original threshold unchanged.
#
# During real-time prediction, we apply a calibration factor
# so that moderately unusual transactions can be detected
# earlier instead of being immediately classified as NORMAL.

ANOMALY_THRESHOLD_MULTIPLIER = 0.65


# ============================================================
# FEATURE CONFIGURATION
# ============================================================

# These MUST match the training order.

FEATURES = [
    "Amount",
    "Account_Age_Days",
    "Transaction_Count_24H",
    "Total_Amount_24H",
    "IP_Risk_Score",
    "Previous_Fraud_Count",
    "Is_PEP",
]


# ============================================================
# LOAD MODEL
# ============================================================

def load_anomaly_model():

    if not MODEL_FILE.exists():

        raise FileNotFoundError(
            f"Anomaly model not found: {MODEL_FILE}"
        )

    model = np.load(
        MODEL_FILE
    )

    mean = model["mean"]

    std = model["std"]

    components = model["components"]

    trained_threshold = float(
        model["threshold"]
    )

    return (
        mean,
        std,
        components,
        trained_threshold
    )


# ============================================================
# LOAD METADATA
# ============================================================

def load_metadata():

    if not METADATA_FILE.exists():

        return {}

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# EXTRACT FEATURES
# ============================================================

def extract_features(transaction):

    values = []

    for feature in FEATURES:

        try:

            value = float(
                transaction.get(
                    feature,
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            value = 0.0

        values.append(value)

    return np.array(
        values,
        dtype=float
    )


# ============================================================
# CALCULATE PCA ANOMALY SCORE
# ============================================================

def calculate_anomaly_score(
    transaction
):

    # --------------------------------------------------------
    # Load trained PCA model
    # --------------------------------------------------------

    (
        mean,
        std,
        components,
        trained_threshold
    ) = load_anomaly_model()

    # --------------------------------------------------------
    # Apply prediction-time calibration
    # --------------------------------------------------------

    calibrated_threshold = (
        trained_threshold
        * ANOMALY_THRESHOLD_MULTIPLIER
    )

    # --------------------------------------------------------
    # Extract transaction features
    # --------------------------------------------------------

    X = extract_features(
        transaction
    )

    # --------------------------------------------------------
    # Standardize using training parameters
    # --------------------------------------------------------

    std_safe = np.where(
        std == 0,
        1.0,
        std
    )

    X_scaled = (
        X - mean
    ) / std_safe

    # --------------------------------------------------------
    # PCA projection
    # --------------------------------------------------------

    projected = np.dot(
        X_scaled,
        components.T
    )

    # --------------------------------------------------------
    # PCA reconstruction
    # --------------------------------------------------------

    reconstructed = np.dot(
        projected,
        components
    )

    # --------------------------------------------------------
    # Reconstruction error
    # --------------------------------------------------------

    anomaly_score = float(
        np.mean(
            (
                X_scaled
                - reconstructed
            ) ** 2
        )
    )

    # --------------------------------------------------------
    # Determine anomaly status
    # --------------------------------------------------------

    is_anomaly = (
        anomaly_score
        >= calibrated_threshold
    )

    # --------------------------------------------------------
    # Determine anomaly level
    # --------------------------------------------------------
    #
    # 0.50 x threshold -> WATCH
    # 0.65 x threshold -> ANOMALOUS
    # 1.00 x threshold -> SEVERE
    #
    # This creates multiple levels of unusual behaviour.

    if anomaly_score >= calibrated_threshold:

        anomaly_level = "SEVERE"

    elif anomaly_score >= (
        calibrated_threshold * 0.80
    ):

        anomaly_level = "ANOMALOUS"

    elif anomaly_score >= (
        calibrated_threshold * 0.50
    ):

        anomaly_level = "WATCH"

    else:

        anomaly_level = "NORMAL"

    return {

        # Raw reconstruction error
        "anomaly_score":
            anomaly_score,

        # Original threshold learned during PCA training
        "trained_threshold":
            trained_threshold,

        # Threshold used for real-time classification
        "anomaly_threshold":
            calibrated_threshold,

        # Calibration factor
        "threshold_multiplier":
            ANOMALY_THRESHOLD_MULTIPLIER,

        "anomaly_level":
            anomaly_level,

        "is_anomaly":
            bool(is_anomaly)
    }


# ============================================================
# ANOMALY RISK SCORE
# ============================================================

def anomaly_risk_score(
    anomaly_score,
    threshold
):

    if threshold <= 0:

        return 0.0

    # Convert PCA reconstruction error
    # into a 0-100 risk contribution.

    normalized = (
        anomaly_score
        / threshold
    ) * 50

    return float(
        min(
            max(
                normalized,
                0.0
            ),
            100.0
        )
    )


# ============================================================
# COMPLETE TRANSACTION ANALYSIS
# ============================================================

def analyze_transaction(
    transaction
):

    result = calculate_anomaly_score(
        transaction
    )

    anomaly_contribution = (
        anomaly_risk_score(
            result["anomaly_score"],
            result["anomaly_threshold"]
        )
    )

    result[
        "anomaly_risk_contribution"
    ] = anomaly_contribution

    result[
        "transaction_id"
    ] = transaction.get(
        "Transaction_ID",
        "UNKNOWN"
    )

    result[
        "customer_id"
    ] = transaction.get(
        "Customer_ID",
        "UNKNOWN"
    )

    return result


# ============================================================
# TEST TRANSACTION
# ============================================================

def test_anomaly_detection():

    transaction = {

        "Transaction_ID":
            "ANOMALY_TEST_001",

        "Customer_ID":
            "CUST_TEST_001",

        "Amount":
            1500000,

        "Account_Age_Days":
            20,

        "Transaction_Count_24H":
            18,

        "Total_Amount_24H":
            3000000,

        "IP_Risk_Score":
            90,

        "Previous_Fraud_Count":
            4,

        "Is_PEP":
            1
    }

    result = analyze_transaction(
        transaction
    )

    print()
    print("=" * 70)
    print("PCA ANOMALY DETECTION TEST")
    print("=" * 70)

    print(
        f"Transaction ID          : "
        f"{result['transaction_id']}"
    )

    print(
        f"Customer ID             : "
        f"{result['customer_id']}"
    )

    print(
        f"Anomaly Score           : "
        f"{result['anomaly_score']:.6f}"
    )

    print(
        f"Original PCA Threshold  : "
        f"{result['trained_threshold']:.6f}"
    )

    print(
        f"Calibrated Threshold     : "
        f"{result['anomaly_threshold']:.6f}"
    )

    print(
        f"Threshold Multiplier    : "
        f"{result['threshold_multiplier']:.2f}"
    )

    print(
        f"Anomaly Risk            : "
        f"{result['anomaly_risk_contribution']:.2f}/100"
    )

    print(
        f"Anomaly Level           : "
        f"{result['anomaly_level']}"
    )

    print(
        f"Is Anomaly              : "
        f"{result['is_anomaly']}"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    test_anomaly_detection()