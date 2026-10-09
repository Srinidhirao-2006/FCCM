import json
from kafka import KafkaProducer

KAFKA_SERVER = "localhost:9092"
TOPIC_NAME = "transactions"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

test_transaction = {
    "Transaction_ID": "KAFKA_STRUCT_001",
    "Customer_ID": "CUST1001",
    "Amount": 450000,
    "Transaction_Type": "Cash",
    "Merchant_Category": "Retail",
    "Country": "India",
    "Is_PEP": 0,
    "Account_Age_Days": 500,
    "Transaction_Count_24H": 4,
    "Total_Amount_24H": 1800000,
    "Device_ID": "DEV_TEST",
    "IP_Risk_Score": 30,
    "Previous_Fraud_Count": 0
}

future = producer.send(
    TOPIC_NAME,
    value=test_transaction
)

record_metadata = future.get(timeout=10)

print("=" * 60)
print("KAFKA TEST TRANSACTION SENT")
print("=" * 60)
print(f"Transaction ID : {test_transaction['Transaction_ID']}")
print(f"Customer ID    : {test_transaction['Customer_ID']}")
print(f"Amount         : ₹{test_transaction['Amount']}")
print(f"Type           : {test_transaction['Transaction_Type']}")
print(f"Topic          : {record_metadata.topic}")
print(f"Partition      : {record_metadata.partition}")
print(f"Offset         : {record_metadata.offset}")
print("=" * 60)

producer.flush()
producer.close()