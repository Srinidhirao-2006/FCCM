import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from explainability.risk_explanation import (
    explain_transaction,
    print_explanation
)


# ---------------------------------------------------------
# TEST TRANSACTION
# ---------------------------------------------------------

transaction = {
    "Transaction_ID": "EXPLAIN_TEST_001",
    "Customer_ID": "CUST_EXPLAIN_001",

    "Amount": 1500000,
    "Transaction_Type": "Cash",
    "Merchant_Category": "Financial Services",
    "Country": "Iran",

    "Is_PEP": 1,
    "Account_Age_Days": 20,

    "Transaction_Count_24H": 18,
    "Total_Amount_24H": 3000000,

    "Device_ID": "DEV_TEST",

    "IP_Risk_Score": 90,
    "Previous_Fraud_Count": 4
}


# ---------------------------------------------------------
# AML RESULT
# ---------------------------------------------------------

aml_result = {

    "aml_risk_score": 160,

    "aml_risk_level": "CRITICAL",

    "rules_triggered": [

        {
            "rule": "HIGH_VALUE_TRANSACTION",
            "description": "Transaction amount exceeds ₹10 lakh",
            "risk_points": 25
        },

        {
            "rule": "HIGH_RISK_COUNTRY",
            "description": "Transaction originates from high-risk country: Iran",
            "risk_points": 30
        },

        {
            "rule": "PEP_TRANSACTION",
            "description": "Transaction associated with a Politically Exposed Person",
            "risk_points": 20
        },

        {
            "rule": "HIGH_TRANSACTION_FREQUENCY",
            "description": "More than 10 transactions detected within 24 hours",
            "risk_points": 20
        },

        {
            "rule": "HIGH_24H_TRANSACTION_VALUE",
            "description": "Total transaction value in 24 hours exceeds ₹15 lakh",
            "risk_points": 25
        },

        {
            "rule": "PREVIOUS_FRAUD_HISTORY",
            "description": "Customer has previous fraud history",
            "risk_points": 25
        },

        {
            "rule": "HIGH_IP_RISK",
            "description": "IP risk score is 70 or higher",
            "risk_points": 15
        }
    ]
}


# ---------------------------------------------------------
# ML RESULT
# ---------------------------------------------------------

ml_result = {

    "fraud_probability": 50.33,

    "ml_prediction": "FRAUD"
}


# ---------------------------------------------------------
# PCA ANOMALY RESULT
# ---------------------------------------------------------

anomaly_result = {

    "anomaly_score": 4.587355,

    "anomaly_threshold": 0.674565,

    "anomaly_level": "SEVERE",

    "is_anomaly": True,

    "anomaly_risk_contribution": 100.0
}


# ---------------------------------------------------------
# GENERATE EXPLANATION
# ---------------------------------------------------------

result = explain_transaction(

    transaction=transaction,

    aml_result=aml_result,

    ml_result=ml_result,

    anomaly_result=anomaly_result,

    combined_score=82.62,

    final_risk_level="CRITICAL"
)


# ---------------------------------------------------------
# DISPLAY EXPLANATION
# ---------------------------------------------------------

print_explanation(result)