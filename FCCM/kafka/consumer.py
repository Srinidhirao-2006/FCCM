import json
import sys
from pathlib import Path

from kafka import KafkaConsumer


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# FCCM IMPORTS
# ============================================================

from backend.services.rule_engine import evaluate_transaction
from backend.services.alert_service import create_alert
from backend.services.transaction_service import save_transaction

from machine_learning.predict import predict_transaction
from machine_learning.anomaly_predict import analyze_transaction

from explainability.risk_explanation import explain_transaction
from backend.services.behavioral_analysis import (
    analyze_customer_behavior,
    save_behavioral_analysis
)
from backend.services.explanation_service import save_explanation
from backend.services.behavioral_analysis import analyze_customer_behavior


# ============================================================
# KAFKA CONFIGURATION
# ============================================================

KAFKA_SERVER = "localhost:9092"
KAFKA_TOPIC = "transactions"

# New consumer group so this consumer starts independently
KAFKA_GROUP = "fccm-consumer-group-v4"


# ============================================================
# RISK FUSION WEIGHTS
# ============================================================

AML_WEIGHT = 0.35
ML_WEIGHT = 0.30
PCA_WEIGHT = 0.15
BEHAVIOR_WEIGHT = 0.20


# ============================================================
# RISK LEVEL
# ============================================================

def determine_risk_level(score):

    if score >= 70:
        return "CRITICAL"

    elif score >= 50:
        return "HIGH"

    elif score >= 25:
        return "MEDIUM"

    return "LOW"


# ============================================================
# COMBINED RISK SCORE
# ============================================================
def calculate_combined_risk(
    aml_score,
    ml_probability,
    anomaly_risk,
    behavioral_risk
):

    # AML can exceed 100 because multiple rules
    # can accumulate. Normalize before fusion.

    normalized_aml = min(float(aml_score), 100.0)

    ml_probability = float(ml_probability)

    anomaly_risk = float(anomaly_risk)

    behavioral_risk = float(behavioral_risk)

    combined_score = (
        normalized_aml * AML_WEIGHT
        + ml_probability * ML_WEIGHT
        + anomaly_risk * PCA_WEIGHT
        + behavioral_risk * BEHAVIOR_WEIGHT
    )

    return round(combined_score, 2)

# ============================================================
# PRINT PIPELINE
# ============================================================

def print_pipeline_header():

    print()
    print("=" * 80)
    print("FINANCIAL CRIME & COMPLIANCE MANAGEMENT SYSTEM")
    print("=" * 80)

    print()

    print("Kafka")
    print("   ↓")

    print("AML Rule Engine")
    print("   ↓")

    print("Random Forest ML")
    print("   ↓")

    print("PCA Anomaly Detection")
    print("   ↓")

    print("Multi-Model Risk Fusion")
    print("   ↓")

    print("Risk Explanation")
    print("   ↓")

    print("SQLite Database")
    print("   ↓")

    print("Alert Generation")

    print()
    print("=" * 80)


# ============================================================
# MAIN CONSUMER
# ============================================================

def main():

    print_pipeline_header()

    print()
    print("Connecting to Kafka...")
    print(f"Kafka Server : {KAFKA_SERVER}")
    print(f"Topic        : {KAFKA_TOPIC}")
    print(f"Group ID     : {KAFKA_GROUP}")
    print()

    # --------------------------------------------------------
    # CREATE KAFKA CONSUMER
    # --------------------------------------------------------

    consumer = KafkaConsumer(
        KAFKA_TOPIC,

        bootstrap_servers=[KAFKA_SERVER],

        group_id=KAFKA_GROUP,

        value_deserializer=lambda value:
            json.loads(value.decode("utf-8")),

        auto_offset_reset="latest",

        enable_auto_commit=True,

        consumer_timeout_ms=-1
    )

    print("=" * 80)
    print("Kafka consumer connected successfully.")
    print("Waiting for transactions...")
    print("=" * 80)

    try:

        # ====================================================
        # RECEIVE TRANSACTIONS
        # ====================================================

        for message in consumer:

            transaction = message.value

            print()
            print()
            print("=" * 80)
            print("NEW TRANSACTION RECEIVED FROM KAFKA")
            print("=" * 80)

            # ------------------------------------------------
            # KAFKA MESSAGE INFORMATION
            # ------------------------------------------------

            print(
                f"Topic       : {message.topic}"
            )

            print(
                f"Partition   : {message.partition}"
            )

            print(
                f"Offset      : {message.offset}"
            )

            print(
                f"Transaction : "
                f"{transaction.get('Transaction_ID')}"
            )

            print(
                f"Customer    : "
                f"{transaction.get('Customer_ID')}"
            )

            print(
                f"Amount      : ₹"
                f"{float(transaction.get('Amount', 0)):,.2f}"
            )

            print(
                f"Country     : "
                f"{transaction.get('Country')}"
            )

            # =================================================
            # 1. AML RULE ENGINE
            # =================================================

            print()
            print("-" * 80)
            print("1. AML RULE ENGINE")
            print("-" * 80)

            aml_result = evaluate_transaction(transaction)

            aml_score = float(
                aml_result.get(
                    "aml_risk_score",
                    0
                )
            )

            aml_level = aml_result.get(
                "aml_risk_level",
                "LOW"
            )

            rules_triggered = aml_result.get(
                "rules_triggered",
                []
            )

            print(
                f"AML Risk Score   : {aml_score}"
            )

            print(
                f"AML Risk Level   : {aml_level}"
            )

            print(
                f"Rules Triggered  : "
                f"{len(rules_triggered)}"
            )

            if rules_triggered:

                for rule in rules_triggered:

                    if isinstance(rule, dict):

                        print(
                            f"  • "
                            f"{rule.get('rule', 'RULE')} "
                            f"→ "
                            f"{rule.get('description', '')}"
                        )

                    else:

                        print(
                            f"  • {rule}"
                        )

            # =================================================
            # 2. MACHINE LEARNING FRAUD DETECTION
            # =================================================

            print()
            print("-" * 80)
            print("2. MACHINE LEARNING FRAUD DETECTION")
            print("-" * 80)

            ml_result = predict_transaction(transaction)

            ml_probability = float(
                ml_result.get(
                    "fraud_probability",
                    0
                )
            )

            ml_prediction = ml_result.get(
                "ml_prediction",
                "NORMAL"
            )

            print(
                f"Fraud Probability : "
                f"{ml_probability:.2f}%"
            )

            print(
                f"ML Prediction     : "
                f"{ml_prediction}"
            )

            # =================================================
            # 3. PCA ANOMALY DETECTION
            # =================================================

            print()
            print("-" * 80)
            print("3. PCA ANOMALY DETECTION")
            print("-" * 80)

            anomaly_result = analyze_transaction(
                transaction
            )

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

            anomaly_risk = float(
                anomaly_result.get(
                    "anomaly_risk_contribution",
                    0
                )
            )

            is_anomaly = bool(
                anomaly_result.get(
                    "is_anomaly",
                    False
                )
            )

            print(
                f"Anomaly Score    : "
                f"{anomaly_score:.6f}"
            )

            print(
                f"Threshold        : "
                f"{anomaly_threshold:.6f}"
            )

            print(
                f"Anomaly Level    : "
                f"{anomaly_level}"
            )

            print(
                f"Anomaly Risk     : "
                f"{anomaly_risk:.2f}/100"
            )

            print(
                f"Is Anomaly       : "
                f"{is_anomaly}"
            )
            # =================================================
# 4. CUSTOMER BEHAVIORAL ANALYSIS
# =================================================

            # =================================================
            # 4. CUSTOMER BEHAVIORAL ANALYSIS
            # =================================================

            print()
            print("-" * 80)
            print("4. CUSTOMER BEHAVIORAL ANALYSIS")
            print("-" * 80)

            customer_id = transaction.get("Customer_ID")

            behavioral_result = analyze_customer_behavior(
                customer_id
            )

            print(
                f"Customer ID           : "
                f"{behavioral_result.get('customer_id')}"
            )

            print(
                f"Transactions Analyzed : "
                f"{behavioral_result.get('transaction_count', 0)}"
            )

            print(
                f"Behavioral Risk Score : "
                f"{behavioral_result.get('behavioral_risk_score', 0.0):.2f}"
            )

            print(
                f"Behavioral Risk Level : "
                f"{behavioral_result.get('behavioral_risk_level', 'LOW')}"
            )

            print(
                f"Suspicious Behavior   : "
                f"{'YES' if behavioral_result.get('is_suspicious') else 'NO'}"
            )

            print()

            if behavioral_result.get("risk_factors"):

                print("BEHAVIORAL RISK FACTORS")
                print("-" * 80)

                for index, factor in enumerate(
                    behavioral_result["risk_factors"],
                    start=1
                ):

                    print(
                        f"{index}. "
                        f"{factor.get('rule')}"
                    )

                    print(
                        f"   {factor.get('description')}"
                    )

                    print(
                        f"   Contribution: "
                        f"+{factor.get('contribution', 0):.2f}"
                    )

            else:

                print(
                    "No significant behavioral risk factors detected."
                )


            # =================================================
            # 4. MULTI-MODEL RISK FUSION
            # =================================================

            print()
            print("-" * 80)
            print("4. MULTI-MODEL RISK FUSION")
            print("-" * 80)

            
            combined_score = calculate_combined_risk(
                aml_result["aml_risk_score"],
                ml_result["fraud_probability"],
                anomaly_result.get("anomaly_risk", anomaly_result.get("risk_score", 0)),
                behavioral_result.get("behavioral_risk_score", 0)
            )

            final_risk_level = determine_risk_level(
                combined_score
            )

            print(
                f"AML Contribution : "
                f"{min(aml_score, 100):.2f} × 40%"
            )

            print(
                f"ML Contribution  : "
                f"{ml_probability:.2f} × 35%"
            )

            print(
                f"PCA Contribution : "
                f"{anomaly_risk:.2f} × 25%"
            )

            print()

            print(
                f"Combined Risk Score : "
                f"{combined_score:.2f}"
            )

            print(
                f"Final Risk Level    : "
                f"{final_risk_level}"
            )

            # =================================================
            # 5. RISK EXPLANATION
            # =================================================

            print()
            print("-" * 80)
            print("5. RISK EXPLANATION")
            print("-" * 80)

            explanation_result = explain_transaction(
                transaction=transaction,
                aml_result=aml_result,
                ml_result=ml_result,
                anomaly_result=anomaly_result,
                combined_score=combined_score,
                final_risk_level=final_risk_level
            )
            save_explanation(explanation_result)

            print(
                f"Explanation Count : "
                f"{explanation_result.get('explanation_count', 0)}"
            )

            explanations = explanation_result.get(
                "explanations",
                []
            )

            for index, item in enumerate(
                explanations,
                start=1
            ):

                print()

                print(
                    f"{index}. "
                    f"{item.get('title', item.get('factor', 'Risk Factor'))}"
                )

                print(
                    f"   {item.get('description', '')}"
                )

                if "contribution" in item:

                    print(
                        f"   Contribution: "
                        f"+{item.get('contribution', 0)}"
                    )

            # -------------------------------------------------
            # CONVERT EXPLANATION TO JSON
            # -------------------------------------------------

            explanation_json = json.dumps(
                explanation_result,
                ensure_ascii=False
            )

            print()
            print("WHY WAS THIS TRANSACTION FLAGGED?")
            print("=" * 60)

            for index, item in enumerate(
                explanation_result.get(
                    "explanations",
                    []
                ),
                start=1
            ):

                print()

                print(
                    f"{index}. "
                    f"{item.get('title', item.get('factor', 'Risk Factor'))}"
                )

                print(
                    f"   {item.get('description', '')}"
                )

                if "contribution" in item:

                    print(
                        f"   Contribution: "
                        f"+{item.get('contribution', 0)}"
                    )

            print("=" * 60)

            # =================================================
            # 6. SQLITE DATABASE
            # =================================================

            print()
            print("-" * 80)
            print("6. SQLITE DATABASE")
            print("-" * 80)

            save_transaction(
                transaction,
                ml_probability,
                combined_score,
                final_risk_level
            )

            print(
                f"Transaction saved : "
                f"{transaction.get('Transaction_ID')}"
            )
                        # =================================================
            # 7. CUSTOMER BEHAVIORAL ANALYSIS
            # =================================================

            print()
            print("-" * 80)
            print("7. CUSTOMER BEHAVIORAL ANALYSIS")
            print("-" * 80)

            customer_id = transaction.get("Customer_ID")

            behavioral_result = analyze_customer_behavior(
                customer_id
            )
            # Save behavioral analysis to SQLite
            save_behavioral_analysis(behavioral_result)

            behavioral_score = float(
                behavioral_result.get(
                    "behavioral_risk_score",
                    0
                )
            )

            behavioral_level = behavioral_result.get(
                "behavioral_risk_level",
                "LOW"
            )

            behavioral_suspicious = behavioral_result.get(
                "is_suspicious",
                False
            )

            behavioral_factors = behavioral_result.get(
                "risk_factors",
                []
            )

            behavioral_statistics = behavioral_result.get(
                "statistics",
                {}
            )

            print(
                f"Customer ID              : "
                f"{customer_id}"
            )

            print(
                f"Transactions Analyzed    : "
                f"{behavioral_result.get('transaction_count', 0)}"
            )

            print(
                f"Behavioral Risk Score    : "
                f"{behavioral_score:.2f}"
            )

            print(
                f"Behavioral Risk Level    : "
                f"{behavioral_level}"
            )

            print(
                f"Suspicious Behavior      : "
                f"{'YES' if behavioral_suspicious else 'NO'}"
            )

            print()

            print("Behavioral Risk Factors:")

            if behavioral_factors:

                for index, factor in enumerate(
                    behavioral_factors,
                    start=1
                ):

                    print(
                        f"  {index}. "
                        f"{factor.get('rule', 'UNKNOWN')}"
                    )

                    print(
                        f"     "
                        f"{factor.get('description', '')}"
                    )

                    print(
                        f"     Contribution: "
                        f"+{float(factor.get('contribution', 0)):.2f}"
                    )

            else:

                print(
                    "  No significant behavioral risk factors detected."
                )

            print()

            print("Behavioral Statistics:")

            print(
                f"  Total Transaction Amount : "
                f"₹{float(behavioral_statistics.get('total_transaction_amount', 0)):,.2f}"
            )

            print(
                f"  Average Transaction      : "
                f"₹{float(behavioral_statistics.get('average_transaction_amount', 0)):,.2f}"
            )

            print(
                f"  Maximum 24H Count        : "
                f"{behavioral_statistics.get('maximum_24h_transaction_count', 0)}"
            )

            print(
                f"  Maximum 24H Amount       : "
                f"₹{float(behavioral_statistics.get('maximum_24h_transaction_amount', 0)):,.2f}"
            )

            print(
                f"  High-Value Transactions  : "
                f"{behavioral_statistics.get('high_value_transaction_count', 0)}"
            )

            print(
                f"  Unique Countries         : "
                f"{behavioral_statistics.get('unique_country_count', 0)}"
            )

            print(
                f"  Unique Devices           : "
                f"{behavioral_statistics.get('unique_device_count', 0)}"
            )

            print(
                f"  Transaction Types        : "
                f"{behavioral_statistics.get('unique_transaction_type_count', 0)}"
            )

            print(
                f"  Structuring Transactions: "
                f"{behavioral_statistics.get('structuring_transaction_count', 0)}"
            )

            # =================================================
            # 8. ALERT GENERATION
            # =================================================

            alert_created = False

            if final_risk_level in [
                "HIGH",
                "CRITICAL"
            ]:

                print()
                print("-" * 80)
                print("7. ALERT GENERATION")
                print("-" * 80)

                description = (
                    "High-risk transaction detected. "
                    f"AML Score: {aml_score:.2f}, "
                    f"ML Fraud Probability: "
                    f"{ml_probability:.2f}%, "
                    f"PCA Anomaly Risk: "
                    f"{anomaly_risk:.2f}/100, "
                    f"Combined Risk Score: "
                    f"{combined_score:.2f}"
                )

                alert_id = create_alert(
                    transaction_id=transaction.get(
                        "Transaction_ID"
                    ),

                    customer_id=transaction.get(
                        "Customer_ID"
                    ),

                    alert_type="HIGH_RISK_TRANSACTION",

                    description=description,

                    risk_score=combined_score,

                    severity=final_risk_level
                )

                alert_created = True

                print(
                    f"Alert ID : {alert_id}"
                )

            else:

                print()
                print(
                    "No alert generated "
                    f"because risk level is "
                    f"{final_risk_level}."
                )

            # =================================================
            # FINAL PROCESSING SUMMARY
            # =================================================

            print()
            print("=" * 80)
            print("TRANSACTION PROCESSING COMPLETE")
            print("=" * 80)

            print(
                f"Transaction ID        : "
                f"{transaction.get('Transaction_ID')}"
            )

            print(
                f"AML Risk              : "
                f"{aml_score:.2f}"
            )

            print(
                f"ML Fraud Probability  : "
                f"{ml_probability:.2f}%"
            )

            print(
                f"PCA Anomaly           : "
                f"{anomaly_level}"
            )

            print(
                f"Combined Risk Score   : "
                f"{combined_score:.2f}"
            )

            print(
                f"Final Risk            : "
                f"{final_risk_level}"
            )

            print(
                "Explanation Generated : YES"
            )

            print(
                "Explanation Stored    : YES"
            )

            print(
                f"Alert Generated       : "
                f"{'YES' if alert_created else 'NO'}"
            )

            print("=" * 80)

    except KeyboardInterrupt:

        print()
        print("=" * 80)
        print("Kafka consumer stopped by user.")
        print("=" * 80)

    finally:

        consumer.close()

        print()
        print("Kafka consumer connection closed.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()