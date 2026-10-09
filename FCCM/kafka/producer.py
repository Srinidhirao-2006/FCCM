import csv
import json
import time
from pathlib import Path

from kafka import KafkaProducer


# ============================================================
# Kafka Configuration
# ============================================================

KAFKA_SERVER = "localhost:9092"
TOPIC_NAME = "transactions"

# Locate the dataset relative to the FCCM project
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = PROJECT_ROOT / "data" / "transactions.csv"

# Delay between transactions to simulate real-time streaming
STREAM_DELAY = 0.1


# ============================================================
# Helper: Convert CSV values to appropriate Python types
# ============================================================

def convert_value(column, value):

    if value == "":
        return None

    integer_columns = {
        "Is_PEP",
        "Account_Age_Days",
        "Transaction_Count_24H",
        "Previous_Fraud_Count",
        "Is_Fraud"
    }

    float_columns = {
        "Amount",
        "Total_Amount_24H",
        "IP_Risk_Score"
    }

    if column in integer_columns:
        try:
            return int(float(value))
        except ValueError:
            return value

    if column in float_columns:
        try:
            return float(value)
        except ValueError:
            return value

    return value


# ============================================================
# Create Kafka Producer
# ============================================================

print("=" * 60)
print("FCCM KAFKA PRODUCER")
print("=" * 60)

print(f"Dataset: {CSV_FILE}")
print(f"Kafka server: {KAFKA_SERVER}")
print(f"Kafka topic: {TOPIC_NAME}")
print("=" * 60)


producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)


# ============================================================
# Read CSV and Stream Transactions
# ============================================================

transaction_count = 0

with open(
    CSV_FILE,
    mode="r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        transaction = {}

        # Convert CSV values into suitable Python types
        for column, value in row.items():
            transaction[column] = convert_value(
                column,
                value
            )

        # Send transaction to Kafka
        future = producer.send(
            TOPIC_NAME,
            value=transaction
        )

        # Wait for Kafka acknowledgement
        metadata = future.get(timeout=10)

        transaction_count += 1

        print(
            f"[{transaction_count}] "
            f"Transaction sent | "
            f"ID: {transaction.get('Transaction_ID')} | "
            f"Amount: {transaction.get('Amount')} | "
            f"Partition: {metadata.partition} | "
            f"Offset: {metadata.offset}"
        )

        # Simulate real-time transaction arrival
        time.sleep(STREAM_DELAY)


# ============================================================
# Flush and Close
# ============================================================

producer.flush()
producer.close()

print("=" * 60)
print("ALL TRANSACTIONS SUCCESSFULLY SENT TO KAFKA")
print(f"Total transactions sent: {transaction_count}")
print("=" * 60)