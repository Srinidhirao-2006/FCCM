import json
from kafka import KafkaProducer

# ============================================================
# Kafka Configuration
# ============================================================

KAFKA_SERVER = "localhost:9092"
TOPIC_NAME = "transactions"


# ============================================================
# Create Kafka Producer
# ============================================================

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)


# ============================================================
# High-Risk Test Transaction
# ============================================================

transaction = {

    "Transaction_ID": "KAFKA_ALERT_001",

    "Customer_ID": "CUST_ALERT_001",

    "Timestamp": "2026-10-03 15:20:00",

    "Amount": 1500000,

    "Transaction_Type": "Cash",

    "Merchant_Category": "Financial Services",

    "Country": "Iran",

    "Is_PEP": 1,

    "Account_Age_Days": 20,

    "Transaction_Count_24H": 15,

    "Total_Amount_24H": 5000000,

    "Device_ID": "DEV_ALERT_001",

    "IP_Risk_Score": 90,

    "Previous_Fraud_Count": 3,

    "Is_Fraud": 1
}


# ============================================================
# Send Transaction
# ============================================================

future = producer.send(
    TOPIC_NAME,
    value=transaction
)

metadata = future.get(timeout=10)

producer.flush()
producer.close()


# ============================================================
# Output
# ============================================================

print()
print("=" * 60)
print("HIGH-RISK TEST TRANSACTION SENT")
print("=" * 60)

print(f"Transaction ID : {transaction['Transaction_ID']}")
print(f"Customer ID    : {transaction['Customer_ID']}")
print(f"Amount         : ₹{transaction['Amount']}")
print(f"Country        : {transaction['Country']}")
print(f"PEP            : {transaction['Is_PEP']}")
print(f"Topic          : {metadata.topic}")
print(f"Partition      : {metadata.partition}")
print(f"Offset         : {metadata.offset}")

print("=" * 60)