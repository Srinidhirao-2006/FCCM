import csv
import json
from pathlib import Path

import numpy as np


# ============================================================
# FCCM - PCA BASED UNSUPERVISED ANOMALY DETECTION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "transactions.csv"

MODEL_DIR = PROJECT_ROOT / "machine_learning" / "models"

MODEL_FILE = MODEL_DIR / "pca_anomaly_model.npz"

METADATA_FILE = MODEL_DIR / "pca_anomaly_metadata.json"


# ============================================================
# FEATURES USED FOR ANOMALY DETECTION
# ============================================================

FEATURES = [
    "Amount",
    "Account_Age_Days",
    "Transaction_Count_24H",
    "Total_Amount_24H",
    "IP_Risk_Score",
    "Previous_Fraud_Count",
    "Is_PEP",
]


# Percentage of variance that PCA should retain
VARIANCE_TO_KEEP = 0.95

# Minimum number of principal components
MIN_COMPONENTS = 2

# Maximum number of principal components
MAX_COMPONENTS = 5

# Percentile used to determine anomaly threshold
ANOMALY_PERCENTILE = 95


# ============================================================
# LOAD TRANSACTION DATA
# ============================================================

def load_transactions():

    rows = []

    print()
    print("Reading transaction dataset...")

    with open(
        DATA_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=1):

            values = []

            for feature in FEATURES:

                try:
                    value = float(row.get(feature, 0))
                except (ValueError, TypeError):
                    value = 0.0

                values.append(value)

            rows.append(values)

    if not rows:
        raise ValueError(
            "No transaction records found in the dataset."
        )

    X = np.array(
        rows,
        dtype=float
    )

    return X


# ============================================================
# STANDARDIZATION
# ============================================================

def standardize(X):

    print()
    print("Standardizing transaction features...")

    # Calculate mean
    mean = np.mean(
        X,
        axis=0
    )

    # Calculate standard deviation
    std = np.std(
        X,
        axis=0
    )

    # Prevent division by zero
    std[std == 0] = 1.0

    # Standardization
    X_scaled = (
        X - mean
    ) / std

    return (
        X_scaled,
        mean,
        std
    )


# ============================================================
# PCA TRAINING USING SVD
# ============================================================

def train_pca(
    X_scaled,
    variance_to_keep=0.95
):

    print()
    print("Performing PCA using Singular Value Decomposition...")

    # --------------------------------------------------------
    # Center data
    # --------------------------------------------------------

    X_centered = (
        X_scaled -
        np.mean(
            X_scaled,
            axis=0
        )
    )

    # --------------------------------------------------------
    # SVD
    # --------------------------------------------------------

    U, S, Vt = np.linalg.svd(
        X_centered,
        full_matrices=False
    )

    # --------------------------------------------------------
    # Calculate explained variance
    # --------------------------------------------------------

    explained_variance = S ** 2

    total_variance = np.sum(
        explained_variance
    )

    if total_variance == 0:

        raise ValueError(
            "Unable to calculate PCA variance. "
            "Dataset may contain insufficient variation."
        )

    explained_ratio = (
        explained_variance /
        total_variance
    )

    cumulative_variance = np.cumsum(
        explained_ratio
    )

    # --------------------------------------------------------
    # Automatically select components
    # --------------------------------------------------------

    n_components = (
        np.searchsorted(
            cumulative_variance,
            variance_to_keep
        )
        + 1
    )

    # Keep within configured limits
    n_components = max(
        MIN_COMPONENTS,
        n_components
    )

    n_components = min(
        MAX_COMPONENTS,
        n_components,
        Vt.shape[0]
    )

    # --------------------------------------------------------
    # Principal components
    # --------------------------------------------------------

    components = Vt[
        :n_components
    ]

    retained_variance = float(
        np.sum(
            explained_ratio[
                :n_components
            ]
        )
    )

    return (
        components,
        explained_ratio,
        cumulative_variance,
        n_components,
        retained_variance
    )


# ============================================================
# PCA TRANSFORMATION
# ============================================================

def transform_pca(
    X_scaled,
    components
):

    projected = np.dot(
        X_scaled,
        components.T
    )

    return projected


# ============================================================
# RECONSTRUCTION
# ============================================================

def reconstruct_data(
    projected,
    components
):

    reconstructed = np.dot(
        projected,
        components
    )

    return reconstructed


# ============================================================
# CALCULATE ANOMALY SCORES
# ============================================================

def calculate_anomaly_scores(
    X_scaled,
    components
):

    # --------------------------------------------------------
    # Project data into PCA space
    # --------------------------------------------------------

    projected = transform_pca(
        X_scaled,
        components
    )

    # --------------------------------------------------------
    # Reconstruct original data
    # --------------------------------------------------------

    reconstructed = reconstruct_data(
        projected,
        components
    )

    # --------------------------------------------------------
    # Reconstruction error
    # --------------------------------------------------------

    reconstruction_error = np.mean(
        (
            X_scaled -
            reconstructed
        ) ** 2,
        axis=1
    )

    return reconstruction_error


# ============================================================
# CALCULATE ANOMALY THRESHOLD
# ============================================================

def calculate_threshold(scores):

    # 95th percentile
    threshold = float(
        np.percentile(
            scores,
            ANOMALY_PERCENTILE
        )
    )

    # Safety fallback
    if threshold <= 0:

        mean_score = float(
            np.mean(scores)
        )

        std_score = float(
            np.std(scores)
        )

        threshold = (
            mean_score +
            3 * std_score
        )

    return threshold


# ============================================================
# CLASSIFY ANOMALIES
# ============================================================

def classify_anomalies(
    scores,
    threshold
):

    predictions = (
        scores > threshold
    )

    return predictions


# ============================================================
# TRAIN COMPLETE ANOMALY MODEL
# ============================================================

def train_anomaly_model():

    print()
    print("=" * 75)
    print("FCCM UNSUPERVISED ANOMALY DETECTION")
    print("PCA + RECONSTRUCTION ERROR")
    print("=" * 75)

    # ========================================================
    # LOAD DATA
    # ========================================================

    X = load_transactions()

    print()
    print(
        f"Total transactions : {len(X)}"
    )

    print(
        f"Features used      : {len(FEATURES)}"
    )

    print()
    print("Features:")

    for index, feature in enumerate(
        FEATURES,
        start=1
    ):

        print(
            f"  {index}. {feature}"
        )

    # ========================================================
    # STANDARDIZATION
    # ========================================================

    X_scaled, mean, std = standardize(
        X
    )

    # ========================================================
    # PCA TRAINING
    # ========================================================

    (
        components,
        explained_ratio,
        cumulative_variance,
        n_components,
        retained_variance
    ) = train_pca(
        X_scaled,
        variance_to_keep=VARIANCE_TO_KEEP
    )

    print()
    print(
        f"Target variance        : "
        f"{VARIANCE_TO_KEEP * 100:.2f}%"
    )

    print(
        f"Components selected    : "
        f"{n_components}"
    )

    print(
        f"Variance retained      : "
        f"{retained_variance * 100:.2f}%"
    )

    # ========================================================
    # DISPLAY PCA VARIANCE
    # ========================================================

    print()
    print("PCA Explained Variance:")

    for index in range(
        len(explained_ratio)
    ):

        print(
            f"  Component {index + 1}: "
            f"{explained_ratio[index] * 100:.2f}% "
            f"| Cumulative: "
            f"{cumulative_variance[index] * 100:.2f}%"
        )

    # ========================================================
    # CALCULATE ANOMALY SCORES
    # ========================================================

    print()
    print("Calculating reconstruction errors...")

    scores = calculate_anomaly_scores(
        X_scaled,
        components
    )

    # ========================================================
    # THRESHOLD
    # ========================================================

    threshold = calculate_threshold(
        scores
    )

    # ========================================================
    # ANOMALY PREDICTIONS
    # ========================================================

    predictions = classify_anomalies(
        scores,
        threshold
    )

    anomaly_count = int(
        np.sum(predictions)
    )

    normal_count = int(
        len(predictions) -
        anomaly_count
    )

    anomaly_percentage = (
        anomaly_count /
        len(predictions)
    ) * 100

    # ========================================================
    # MODEL DIRECTORY
    # ========================================================

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # SAVE PCA MODEL
    # ========================================================

    np.savez(
        MODEL_FILE,

        mean=mean,

        std=std,

        components=components,

        threshold=threshold
    )

    # ========================================================
    # SAVE METADATA
    # ========================================================

    metadata = {

        "algorithm":
            "PCA Reconstruction Error",

        "model_type":
            "Unsupervised Anomaly Detection",

        "features":
            FEATURES,

        "training_samples":
            int(len(X)),

        "total_features":
            int(len(FEATURES)),

        "target_variance":
            float(VARIANCE_TO_KEEP),

        "n_components":
            int(n_components),

        "variance_retained":
            float(retained_variance),

        "anomaly_percentile":
            int(ANOMALY_PERCENTILE),

        "anomaly_threshold":
            float(threshold),

        "normal_transactions":
            int(normal_count),

        "anomalous_transactions":
            int(anomaly_count),

        "anomaly_percentage":
            float(anomaly_percentage)
    }

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4
        )

    # ========================================================
    # DISPLAY SCORE STATISTICS
    # ========================================================

    print()
    print("Anomaly Score Statistics:")

    print(
        f"  Minimum score : "
        f"{np.min(scores):.8f}"
    )

    print(
        f"  Maximum score : "
        f"{np.max(scores):.8f}"
    )

    print(
        f"  Mean score    : "
        f"{np.mean(scores):.8f}"
    )

    print(
        f"  Median score  : "
        f"{np.median(scores):.8f}"
    )

    print(
        f"  Threshold     : "
        f"{threshold:.8f}"
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print()
    print("=" * 75)
    print("ANOMALY DETECTION RESULTS")
    print("=" * 75)

    print()
    print(
        f"Training samples       : {len(X)}"
    )

    print(
        f"Normal transactions    : {normal_count}"
    )

    print(
        f"Anomalous transactions : {anomaly_count}"
    )

    print(
        f"Anomaly percentage     : "
        f"{anomaly_percentage:.2f}%"
    )

    print()
    print(
        f"Anomaly threshold      : "
        f"{threshold:.8f}"
    )

    # ========================================================
    # SAVE MODEL INFORMATION
    # ========================================================

    print()
    print("Model saved:")
    print(
        f"  {MODEL_FILE}"
    )

    print()
    print("Metadata saved:")
    print(
        f"  {METADATA_FILE}"
    )

    print()
    print("=" * 75)
    print("ANOMALY MODEL READY")
    print("=" * 75)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    train_anomaly_model()