"""
FCCM - AML Rule Engine

Evaluates incoming transactions against multiple
Anti-Money Laundering (AML) risk rules.
"""


# ============================================================
# AML Threshold Configuration
# ============================================================

HIGH_VALUE_THRESHOLD = 1_000_000       # ₹10 lakh
HIGH_RISK_IP_THRESHOLD = 70
HIGH_FREQUENCY_THRESHOLD = 10
HIGH_24H_AMOUNT_THRESHOLD = 1_500_000  # ₹15 lakh
PREVIOUS_FRAUD_THRESHOLD = 0

HIGH_RISK_COUNTRIES = {
    "Iran",
    "Syria",
    "North Korea"
}


# ============================================================
# Main Rule Evaluation Function
# ============================================================

def evaluate_transaction(transaction):
    """
    Evaluate one transaction against AML rules.

    Parameters
    ----------
    transaction : dict
        Transaction received from Kafka.

    Returns
    -------
    dict
        AML rule evaluation result.
    """

    triggered_rules = []
    risk_points = 0

    # --------------------------------------------------------
    # Safely extract transaction values
    # --------------------------------------------------------

    transaction_id = transaction.get(
        "Transaction_ID",
        "UNKNOWN"
    )

    customer_id = transaction.get(
        "Customer_ID",
        "UNKNOWN"
    )

    amount = float(
        transaction.get("Amount", 0) or 0
    )

    country = str(
        transaction.get("Country", "")
    ).strip()

    is_pep = int(
        transaction.get("Is_PEP", 0) or 0
    )

    transaction_count_24h = int(
        transaction.get(
            "Transaction_Count_24H",
            0
        ) or 0
    )

    total_amount_24h = float(
        transaction.get(
            "Total_Amount_24H",
            0
        ) or 0
    )

    ip_risk_score = float(
        transaction.get(
            "IP_Risk_Score",
            0
        ) or 0
    )

    previous_fraud_count = int(
        transaction.get(
            "Previous_Fraud_Count",
            0
        ) or 0
    )

    transaction_type = str(
        transaction.get(
            "Transaction_Type",
            ""
        )
    ).strip()


    # ========================================================
    # RULE 1 — High Value Transaction
    # ========================================================

    if amount > HIGH_VALUE_THRESHOLD:

        triggered_rules.append({
            "rule": "HIGH_VALUE_TRANSACTION",
            "description": (
                "Transaction amount exceeds ₹10 lakh"
            ),
            "risk_points": 25
        })

        risk_points += 25


    # ========================================================
    # RULE 2 — High Risk Country
    # ========================================================

    if country in HIGH_RISK_COUNTRIES:

        triggered_rules.append({
            "rule": "HIGH_RISK_COUNTRY",
            "description": (
                f"Transaction originates from "
                f"high-risk country: {country}"
            ),
            "risk_points": 30
        })

        risk_points += 30


    # ========================================================
    # RULE 3 — PEP Transaction
    # ========================================================

    if is_pep == 1:

        triggered_rules.append({
            "rule": "PEP_TRANSACTION",
            "description": (
                "Transaction associated with a "
                "Politically Exposed Person"
            ),
            "risk_points": 20
        })

        risk_points += 20


    # ========================================================
    # RULE 4 — High Transaction Frequency
    # ========================================================

    if transaction_count_24h > HIGH_FREQUENCY_THRESHOLD:

        triggered_rules.append({
            "rule": "HIGH_TRANSACTION_FREQUENCY",
            "description": (
                "More than 10 transactions "
                "detected within 24 hours"
            ),
            "risk_points": 20
        })

        risk_points += 20


    # ========================================================
    # RULE 5 — High Total Amount in 24 Hours
    # ========================================================

    if total_amount_24h > HIGH_24H_AMOUNT_THRESHOLD:

        triggered_rules.append({
            "rule": "HIGH_24H_TRANSACTION_VALUE",
            "description": (
                "Total transaction value in 24 hours "
                "exceeds ₹15 lakh"
            ),
            "risk_points": 25
        })

        risk_points += 25


    # ========================================================
    # RULE 6 — Previous Fraud History
    # ========================================================

    if previous_fraud_count > PREVIOUS_FRAUD_THRESHOLD:

        triggered_rules.append({
            "rule": "PREVIOUS_FRAUD_HISTORY",
            "description": (
                "Customer has previous fraud history"
            ),
            "risk_points": 25
        })

        risk_points += 25


    # ========================================================
    # RULE 7 — High IP Risk
    # ========================================================

    if ip_risk_score >= HIGH_RISK_IP_THRESHOLD:

        triggered_rules.append({
            "rule": "HIGH_IP_RISK",
            "description": (
                "IP risk score is 70 or higher"
            ),
            "risk_points": 15
        })

        risk_points += 15


    # ========================================================
    # RULE 8 — Cash Structuring / Smurfing Indicator
    # ========================================================

    if (
        transaction_type == "Cash"
        and 300000 <= amount <= 500000
        and transaction_count_24h >= 3
    ):

        triggered_rules.append({
            "rule": "STRUCTURING_SMURFING",
            "description": (
                "Cash transaction falls within "
                "structuring range with repeated "
                "transactions"
            ),
            "risk_points": 30
        })

        risk_points += 30


    # ========================================================
    # Determine AML Risk Level
    # ========================================================

    if risk_points >= 70:

        risk_level = "CRITICAL"

    elif risk_points >= 50:

        risk_level = "HIGH"

    elif risk_points >= 25:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"


    # ========================================================
    # Final AML Result
    # ========================================================

    return {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "aml_risk_score": risk_points,
        "aml_risk_level": risk_level,
        "rules_triggered": triggered_rules,
        "rule_count": len(triggered_rules),
        "is_suspicious": len(triggered_rules) > 0
    }


# ============================================================
# Simple Standalone Test
# ============================================================

if __name__ == "__main__":

    test_transaction = {
        "Transaction_ID": "TEST001",
        "Customer_ID": "CUST1001",
        "Amount": 1200000,
        "Transaction_Type": "Cash",
        "Country": "India",
        "Is_PEP": 1,
        "Transaction_Count_24H": 5,
        "Total_Amount_24H": 1800000,
        "IP_Risk_Score": 82,
        "Previous_Fraud_Count": 1
    }

    result = evaluate_transaction(
        test_transaction
    )

    print("=" * 70)
    print("FCCM AML RULE ENGINE TEST")
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
        f"AML Risk Score : "
        f"{result['aml_risk_score']}"
    )

    print(
        f"Risk Level     : "
        f"{result['aml_risk_level']}"
    )

    print(
        f"Rules Triggered: "
        f"{result['rule_count']}"
    )

    print(
        f"Suspicious     : "
        f"{result['is_suspicious']}"
    )

    print("-" * 70)

    for rule in result["rules_triggered"]:

        print(
            f"[{rule['rule']}] "
            f"+{rule['risk_points']} points"
        )

        print(
            f"  {rule['description']}"
        )

    print("=" * 70)