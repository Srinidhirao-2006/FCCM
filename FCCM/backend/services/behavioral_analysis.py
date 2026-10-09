"""
Customer Behavioral & Cross-Account Risk Analysis
--------------------------------------------------
Analyzes a customer's recent transaction behavior to detect:

1. High transaction frequency
2. High transaction volume
3. Structuring / smurfing patterns
4. Multiple countries
5. Multiple devices
6. Multiple transaction types
7. Repeated high-value transactions

This module is intentionally independent of Kafka for now.
After testing, it will be integrated into the Kafka consumer.
"""
import json
import sqlite3
from pathlib import Path
from collections import Counter


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"


# ============================================================
# BEHAVIORAL THRESHOLDS
# ============================================================

HIGH_FREQUENCY_THRESHOLD = 10
HIGH_24H_AMOUNT_THRESHOLD = 1_500_000
HIGH_VALUE_THRESHOLD = 1_000_000

STRUCTURING_MIN_AMOUNT = 300_000
STRUCTURING_MAX_AMOUNT = 500_000
STRUCTURING_MIN_TRANSACTIONS = 3

HIGH_COUNTRY_COUNT = 3
HIGH_DEVICE_COUNT = 3


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """Create a connection to the FCCM SQLite database."""
    return sqlite3.connect(DB_PATH)


# ============================================================
# FETCH CUSTOMER TRANSACTIONS
# ============================================================

def get_customer_transactions(customer_id, limit=100):
    """
    Retrieve recent transactions belonging to a customer.
    """

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            transaction_id,
            customer_id,
            timestamp,
            amount,
            transaction_type,
            merchant_category,
            country,
            is_pep,
            account_age_days,
            transaction_count_24h,
            total_amount_24h,
            device_id,
            ip_risk_score,
            previous_fraud_count,
            actual_fraud,
            fraud_probability,
            risk_score,
            risk_level
        FROM transactions
        WHERE customer_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """

    cursor.execute(query, (customer_id, limit))

    columns = [description[0] for description in cursor.description]

    rows = cursor.fetchall()

    connection.close()

    transactions = []

    for row in rows:
        transactions.append(dict(zip(columns, row)))

    return transactions


# ============================================================
# STRUCTURING DETECTION
# ============================================================

def detect_structuring(transactions):
    """
    Detect possible structuring / smurfing behavior.

    Structuring is suspected when multiple transactions:
    - fall within the defined amount range
    - occur for the same customer
    - appear repeatedly in the available transaction history
    """

    qualifying_transactions = []

    for transaction in transactions:

        amount = float(transaction["amount"] or 0)

        if (
            STRUCTURING_MIN_AMOUNT
            <= amount
            <= STRUCTURING_MAX_AMOUNT
        ):
            qualifying_transactions.append(transaction)

    is_structuring = (
        len(qualifying_transactions)
        >= STRUCTURING_MIN_TRANSACTIONS
    )

    return {
        "is_structuring": is_structuring,
        "transaction_count": len(qualifying_transactions),
        "transactions": qualifying_transactions,
    }


# ============================================================
# BEHAVIORAL ANALYSIS
# ============================================================

def analyze_customer_behavior(customer_id):
    """
    Analyze the customer's transaction behavior.

    Returns:
        customer behavioral risk score
        behavioral risk level
        detected patterns
        supporting statistics
    """

    transactions = get_customer_transactions(customer_id)

    if not transactions:
        return {
            "customer_id": customer_id,
            "transaction_count": 0,
            "behavioral_risk_score": 0.0,
            "behavioral_risk_level": "LOW",
            "is_suspicious": False,
            "risk_factors": [],
            "statistics": {},
        }

    risk_score = 0.0
    risk_factors = []

    # ========================================================
    # BASIC STATISTICS
    # ========================================================

    amounts = [
        float(t["amount"] or 0)
        for t in transactions
    ]

    total_amount = sum(amounts)

    average_amount = (
        total_amount / len(amounts)
        if amounts
        else 0
    )

    countries = [
        t["country"]
        for t in transactions
        if t["country"]
    ]

    devices = [
        t["device_id"]
        for t in transactions
        if t["device_id"]
    ]

    transaction_types = [
        t["transaction_type"]
        for t in transactions
        if t["transaction_type"]
    ]

    unique_countries = set(countries)
    unique_devices = set(devices)
    unique_transaction_types = set(transaction_types)

    # ========================================================
    # RULE 1: HIGH TRANSACTION FREQUENCY
    # ========================================================

    maximum_frequency = max(
        [
            int(t["transaction_count_24h"] or 0)
            for t in transactions
        ],
        default=0,
    )

    if maximum_frequency > HIGH_FREQUENCY_THRESHOLD:

        risk_score += 15

        risk_factors.append({
            "rule": "HIGH_CUSTOMER_FREQUENCY",
            "description": (
                f"Customer recorded more than "
                f"{HIGH_FREQUENCY_THRESHOLD} transactions "
                f"within 24 hours."
            ),
            "contribution": 15.0,
        })

    # ========================================================
    # RULE 2: HIGH TRANSACTION VOLUME
    # ========================================================

    maximum_24h_amount = max(
        [
            float(t["total_amount_24h"] or 0)
            for t in transactions
        ],
        default=0,
    )

    if maximum_24h_amount > HIGH_24H_AMOUNT_THRESHOLD:

        risk_score += 15

        risk_factors.append({
            "rule": "HIGH_CUSTOMER_24H_VOLUME",
            "description": (
                "Customer transaction volume exceeds "
                "the ₹15 lakh 24-hour threshold."
            ),
            "contribution": 15.0,
        })

    # ========================================================
    # RULE 3: REPEATED HIGH-VALUE TRANSACTIONS
    # ========================================================

    high_value_transactions = [
        t
        for t in transactions
        if float(t["amount"] or 0) >= HIGH_VALUE_THRESHOLD
    ]

    if len(high_value_transactions) >= 2:

        risk_score += 15

        risk_factors.append({
            "rule": "REPEATED_HIGH_VALUE",
            "description": (
                f"Customer performed "
                f"{len(high_value_transactions)} "
                "high-value transactions."
            ),
            "contribution": 15.0,
        })

    # ========================================================
    # RULE 4: STRUCTURING / SMURFING
    # ========================================================

    structuring_result = detect_structuring(transactions)

    if structuring_result["is_structuring"]:

        risk_score += 25

        risk_factors.append({
            "rule": "CUSTOMER_STRUCTURING",
            "description": (
                f"Possible structuring detected: "
                f"{structuring_result['transaction_count']} "
                "transactions fall within the "
                "₹3–₹5 lakh range."
            ),
            "contribution": 25.0,
        })

    # ========================================================
    # RULE 5: MULTIPLE COUNTRIES
    # ========================================================

    if len(unique_countries) >= HIGH_COUNTRY_COUNT:

        risk_score += 10

        risk_factors.append({
            "rule": "MULTIPLE_COUNTRIES",
            "description": (
                f"Customer activity spans "
                f"{len(unique_countries)} different countries."
            ),
            "contribution": 10.0,
        })

    # ========================================================
    # RULE 6: MULTIPLE DEVICES
    # ========================================================

    if len(unique_devices) >= HIGH_DEVICE_COUNT:

        risk_score += 10

        risk_factors.append({
            "rule": "MULTIPLE_DEVICES",
            "description": (
                f"Customer used "
                f"{len(unique_devices)} different devices."
            ),
            "contribution": 10.0,
        })

    # ========================================================
    # RULE 7: MULTIPLE TRANSACTION TYPES
    # ========================================================

    if len(unique_transaction_types) >= 3:

        risk_score += 5

        risk_factors.append({
            "rule": "MULTIPLE_TRANSACTION_TYPES",
            "description": (
                f"Customer used "
                f"{len(unique_transaction_types)} "
                "different transaction types."
            ),
            "contribution": 5.0,
        })

    # ========================================================
    # CAP SCORE
    # ========================================================

    risk_score = min(risk_score, 100.0)

    # ========================================================
    # DETERMINE RISK LEVEL
    # ========================================================

    if risk_score >= 70:
        risk_level = "CRITICAL"

    elif risk_score >= 50:
        risk_level = "HIGH"

    elif risk_score >= 25:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "customer_id": customer_id,
        "transaction_count": len(transactions),

        "behavioral_risk_score": round(
            risk_score,
            2,
        ),

        "behavioral_risk_level": risk_level,

        "is_suspicious": risk_score >= 25,

        "risk_factors": risk_factors,

        "statistics": {
            "total_transaction_amount": round(
                total_amount,
                2,
            ),

            "average_transaction_amount": round(
                average_amount,
                2,
            ),

            "maximum_24h_transaction_count": (
                maximum_frequency
            ),

            "maximum_24h_transaction_amount": round(
                maximum_24h_amount,
                2,
            ),

            "high_value_transaction_count": (
                len(high_value_transactions)
            ),

            "unique_country_count": (
                len(unique_countries)
            ),

            "unique_device_count": (
                len(unique_devices)
            ),

            "unique_transaction_type_count": (
                len(unique_transaction_types)
            ),

            "structuring_transaction_count": (
                structuring_result["transaction_count"]
            ),
        },
    }


# ============================================================
# PRINT RESULT
# ============================================================

def print_behavioral_analysis(result):
    """Print a readable behavioral risk report."""

    print()
    print("=" * 70)
    print("CUSTOMER BEHAVIORAL RISK ANALYSIS")
    print("=" * 70)

    print(
        f"Customer ID              : "
        f"{result['customer_id']}"
    )

    print(
        f"Transactions Analyzed    : "
        f"{result['transaction_count']}"
    )

    print(
        f"Behavioral Risk Score    : "
        f"{result['behavioral_risk_score']:.2f}"
    )

    print(
        f"Behavioral Risk Level    : "
        f"{result['behavioral_risk_level']}"
    )

    print(
        f"Suspicious Behavior      : "
        f"{'YES' if result['is_suspicious'] else 'NO'}"
    )

    print()
    print("-" * 70)
    print("BEHAVIORAL RISK FACTORS")
    print("-" * 70)

    if result["risk_factors"]:

        for index, factor in enumerate(
            result["risk_factors"],
            start=1,
        ):

            print(
                f"{index}. "
                f"{factor['rule']}"
            )

            print(
                f"   {factor['description']}"
            )

            print(
                f"   Contribution: "
                f"+{factor['contribution']:.2f}"
            )

    else:

        print(
            "No significant behavioral risk factors detected."
        )

    print()
    print("-" * 70)
    print("CUSTOMER BEHAVIOR STATISTICS")
    print("-" * 70)

    statistics = result["statistics"]

    for key, value in statistics.items():

        formatted_key = key.replace(
            "_",
            " ",
        ).title()

        print(
            f"{formatted_key:<35}: {value}"
        )

    print("=" * 70)


# ============================================================
# TEST ENTRY POINT
# ============================================================

if __name__ == "__main__":

    print()
    print("FCCM CUSTOMER BEHAVIORAL ANALYSIS TEST")
    print("=" * 70)

    # Change this customer ID if you want to test another customer.
    TEST_CUSTOMER_ID = "CUST1001"

    result = analyze_customer_behavior(
        TEST_CUSTOMER_ID
    )

    print_behavioral_analysis(result)
    # ============================================================
# SAVE BEHAVIORAL ANALYSIS TO DATABASE
# ============================================================

def save_behavioral_analysis(result):
    """
    Save or update customer behavioral analysis in SQLite.
    """

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    statistics = result.get("statistics", {})

    cursor.execute(
        """
        INSERT INTO behavioral_analysis (
            customer_id,
            transaction_count,
            behavioral_risk_score,
            behavioral_risk_level,
            is_suspicious,
            unique_country_count,
            unique_device_count,
            structuring_transaction_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(customer_id)
        DO UPDATE SET
            transaction_count = excluded.transaction_count,
            behavioral_risk_score = excluded.behavioral_risk_score,
            behavioral_risk_level = excluded.behavioral_risk_level,
            is_suspicious = excluded.is_suspicious,
            unique_country_count = excluded.unique_country_count,
            unique_device_count = excluded.unique_device_count,
            structuring_transaction_count = excluded.structuring_transaction_count
        """,
        (
            result.get("customer_id"),
            result.get("transaction_count", 0),
            result.get("behavioral_risk_score", 0),
            result.get("behavioral_risk_level", "LOW"),
            1 if result.get("is_suspicious", False) else 0,

            # These values come from result["statistics"]
            statistics.get("unique_country_count", 0),
            statistics.get("unique_device_count", 0),
            statistics.get("structuring_transaction_count", 0),
        )
    )

    connection.commit()
    connection.close()

    print(
        f"Behavioral analysis saved successfully for customer: "
        f"{result.get('customer_id')}"
    )