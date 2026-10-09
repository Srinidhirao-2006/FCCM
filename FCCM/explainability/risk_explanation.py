# explainability/risk_explanation.py


# ---------------------------------------------------------
# AML RULE RISK POINTS
# ---------------------------------------------------------

AML_RULE_POINTS = {
    "HIGH_VALUE_TRANSACTION": 25,
    "HIGH_RISK_COUNTRY": 30,
    "PEP_TRANSACTION": 20,
    "HIGH_TRANSACTION_FREQUENCY": 20,
    "HIGH_24H_TRANSACTION_VALUE": 25,
    "PREVIOUS_FRAUD_HISTORY": 25,
    "HIGH_IP_RISK": 15,
    "CASH_STRUCTURING": 30
}


# ---------------------------------------------------------
# GENERATE RISK EXPLANATION
# ---------------------------------------------------------

def explain_transaction(
    transaction,
    aml_result,
    ml_result,
    anomaly_result,
    combined_score,
    final_risk_level
):
    """
    Generate a human-readable explanation for why
    a transaction was assigned a particular risk level.
    """

    explanations = []

    transaction_id = transaction.get(
        "Transaction_ID",
        "UNKNOWN"
    )

    customer_id = transaction.get(
        "Customer_ID",
        "UNKNOWN"
    )

    # -----------------------------------------------------
    # 1. AML RULE EXPLANATIONS
    # -----------------------------------------------------

    rules_triggered = aml_result.get(
        "rules_triggered",
        []
    )

    for rule in rules_triggered:

        rule_name = rule.get(
            "rule",
            "UNKNOWN_RULE"
        )

        description = rule.get(
            "description",
            "AML rule was triggered."
        )

        risk_points = rule.get(
            "risk_points",
            AML_RULE_POINTS.get(rule_name, 0)
        )

        explanations.append({
            "category": "AML",
            "rule": rule_name,
            "description": description,
            "contribution": float(risk_points)
        })

    # -----------------------------------------------------
    # 2. ML FRAUD EXPLANATION
    # -----------------------------------------------------

    fraud_probability = float(
        ml_result.get(
            "fraud_probability",
            0
        )
    )

    ml_prediction = ml_result.get(
        "ml_prediction",
        "NORMAL"
    )

    if ml_prediction == "FRAUD":

        explanations.append({
            "category": "ML",
            "rule": "ML_FRAUD_PREDICTION",
            "description": (
                f"Machine Learning model classified the "
                f"transaction as FRAUD with "
                f"{fraud_probability:.2f}% fraud probability."
            ),
            "contribution": fraud_probability
        })

    elif fraud_probability >= 50:

        explanations.append({
            "category": "ML",
            "rule": "HIGH_ML_FRAUD_PROBABILITY",
            "description": (
                f"Machine Learning model assigned a "
                f"{fraud_probability:.2f}% fraud probability."
            ),
            "contribution": fraud_probability
        })

    # -----------------------------------------------------
    # 3. PCA ANOMALY EXPLANATION
    # -----------------------------------------------------

    anomaly_score = float(
        anomaly_result.get(
            "anomaly_score",
            0
        )
    )

    anomaly_threshold = float(
        anomaly_result.get(
            "anomaly_threshold",
            0
        )
    )

    anomaly_level = anomaly_result.get(
        "anomaly_level",
        "NORMAL"
    )

    is_anomaly = anomaly_result.get(
        "is_anomaly",
        False
    )

    anomaly_risk = float(
        anomaly_result.get(
            "anomaly_risk_contribution",
            0
        )
    )

    if is_anomaly:

        explanations.append({
            "category": "PCA",
            "rule": "PCA_ANOMALY",
            "description": (
                f"PCA anomaly detection identified unusual "
                f"transaction behaviour. "
                f"Anomaly level: {anomaly_level}. "
                f"Score: {anomaly_score:.6f}, "
                f"threshold: {anomaly_threshold:.6f}."
            ),
            "contribution": anomaly_risk
        })

    # -----------------------------------------------------
    # 4. ADD IMPORTANT TRANSACTION CONTEXT
    # -----------------------------------------------------

    amount = float(
        transaction.get("Amount", 0)
    )

    country = transaction.get(
        "Country",
        "Unknown"
    )

    is_pep = transaction.get(
        "Is_PEP",
        0
    )

    transaction_count = int(
        transaction.get(
            "Transaction_Count_24H",
            0
        )
    )

    total_amount_24h = float(
        transaction.get(
            "Total_Amount_24H",
            0
        )
    )

    previous_fraud_count = int(
        transaction.get(
            "Previous_Fraud_Count",
            0
        )
    )

    ip_risk = float(
        transaction.get(
            "IP_Risk_Score",
            0
        )
    )

    # -----------------------------------------------------
    # 5. SORT BY CONTRIBUTION
    # -----------------------------------------------------

    explanations.sort(
        key=lambda x: x["contribution"],
        reverse=True
    )

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    return {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "final_risk_level": final_risk_level,
        "combined_risk_score": float(combined_score),

        "transaction_context": {
            "amount": amount,
            "country": country,
            "is_pep": is_pep,
            "transaction_count_24h": transaction_count,
            "total_amount_24h": total_amount_24h,
            "previous_fraud_count": previous_fraud_count,
            "ip_risk_score": ip_risk
        },

        "ml_fraud_probability": fraud_probability,

        "pca_anomaly_score": anomaly_score,

        "pca_anomaly_threshold": anomaly_threshold,

        "pca_anomaly_level": anomaly_level,

        "explanation_count": len(explanations),

        "explanations": explanations
    }


# ---------------------------------------------------------
# PRINT EXPLANATION
# ---------------------------------------------------------

def print_explanation(result):
    """
    Print the generated explanation in a readable format.
    """

    print()
    print("=" * 70)
    print("WHY WAS THIS TRANSACTION FLAGGED?")
    print("=" * 70)

    print(
        f"Transaction ID : "
        f"{result['transaction_id']}"
    )

    print(
        f"Customer ID    : "
        f"{result['customer_id']}"
    )

    print(
        f"Risk Level     : "
        f"{result['final_risk_level']}"
    )

    print(
        f"Combined Risk  : "
        f"{result['combined_risk_score']:.2f}"
    )

    print("-" * 70)

    print("RISK FACTORS")
    print("-" * 70)

    for index, explanation in enumerate(
        result["explanations"],
        start=1
    ):

        print(
            f"\n{index}. "
            f"[{explanation['category']}] "
            f"{explanation['rule']}"
        )

        print(
            f"   {explanation['description']}"
        )

        print(
            f"   Risk Contribution: "
            f"+{explanation['contribution']:.2f}"
        )

    print()
    print("-" * 70)

    print("ML FRAUD DETECTION")
    print("-" * 70)

    print(
        f"Fraud Probability : "
        f"{result['ml_fraud_probability']:.2f}%"
    )

    print("-" * 70)

    print("PCA ANOMALY DETECTION")
    print("-" * 70)

    print(
        f"Anomaly Score     : "
        f"{result['pca_anomaly_score']:.6f}"
    )

    print(
        f"Threshold         : "
        f"{result['pca_anomaly_threshold']:.6f}"
    )

    print(
        f"Anomaly Level     : "
        f"{result['pca_anomaly_level']}"
    )

    print()
    print("=" * 70)