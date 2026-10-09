import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ============================================================
# FCCM - Synthetic Transaction Dataset Generator
# ============================================================

np.random.seed(42)

NUM_TRANSACTIONS = 10000

transaction_types = [
    "Cash",
    "Transfer",
    "Online",
    "ATM"
]

merchant_categories = [
    "Retail",
    "Grocery",
    "Electronics",
    "Travel",
    "Food",
    "Jewellery",
    "Fuel",
    "Online Services"
]

normal_countries = [
    "India",
    "USA",
    "UK",
    "Singapore",
    "UAE",
    "Germany",
    "Australia"
]

high_risk_countries = [
    "Iran",
    "Syria",
    "North Korea"
]


# ============================================================
# Generate basic transaction information
# ============================================================

start_date = datetime(2026, 1, 1)

timestamps = [
    start_date + timedelta(
        minutes=int(np.random.randint(0, 43200))
    )
    for _ in range(NUM_TRANSACTIONS)
]

timestamps.sort()


data = []

for i in range(NUM_TRANSACTIONS):

    customer_id = f"CUST{np.random.randint(1000, 1200)}"

    amount = round(
        np.random.lognormal(mean=8.0, sigma=1.0),
        2
    )

    transaction_type = np.random.choice(
        transaction_types,
        p=[0.15, 0.35, 0.35, 0.15]
    )

    merchant_category = np.random.choice(
        merchant_categories
    )

    country = np.random.choice(
        normal_countries,
        p=[0.60, 0.08, 0.07, 0.07, 0.07, 0.06, 0.05]
    )

    is_pep = np.random.choice(
        [0, 1],
        p=[0.97, 0.03]
    )

    account_age_days = np.random.randint(
        30,
        3650
    )

    transaction_count_24h = np.random.poisson(
        4
    )

    total_amount_24h = round(
        amount * np.random.uniform(1.2, 5.0),
        2
    )

    device_id = f"DEV{np.random.randint(1000, 1500)}"

    ip_risk_score = round(
        np.random.uniform(0, 100),
        2
    )

    previous_fraud_count = np.random.poisson(
        0.2
    )

    # --------------------------------------------------------
    # Fraud probability generation
    # --------------------------------------------------------

    fraud_probability = 0.005

    # Large transaction
    if amount > 500000:
        fraud_probability += 0.20

    # Very large transaction
    if amount > 1000000:
        fraud_probability += 0.25

    # High-risk country
    if country in high_risk_countries:
        fraud_probability += 0.30

    # PEP + large transaction
    if is_pep == 1 and amount > 500000:
        fraud_probability += 0.20

    # High transaction frequency
    if transaction_count_24h > 10:
        fraud_probability += 0.15

    # High IP risk
    if ip_risk_score > 80:
        fraud_probability += 0.15

    # Previous fraud history
    if previous_fraud_count > 0:
        fraud_probability += 0.20

    fraud_probability = min(
        fraud_probability,
        0.95
    )

    is_fraud = np.random.random() < fraud_probability

    data.append({
        "Transaction_ID": f"TXN{i+1:06d}",
        "Customer_ID": customer_id,
        "Timestamp": timestamps[i],
        "Amount": amount,
        "Transaction_Type": transaction_type,
        "Merchant_Category": merchant_category,
        "Country": country,
        "Is_PEP": is_pep,
        "Account_Age_Days": account_age_days,
        "Transaction_Count_24H": transaction_count_24h,
        "Total_Amount_24H": total_amount_24h,
        "Device_ID": device_id,
        "IP_Risk_Score": ip_risk_score,
        "Previous_Fraud_Count": previous_fraud_count,
        "Is_Fraud": int(is_fraud)
    })


# ============================================================
# Create DataFrame
# ============================================================

df = pd.DataFrame(data)
# ============================================================
# Inject specific AML scenarios
# ============================================================

# 1. High-value transactions
# Create transactions above ₹10 lakh
high_value_indices = np.random.choice(
    df.index,
    size=100,
    replace=False
)

df.loc[high_value_indices, "Amount"] = np.random.uniform(
    1_000_001,
    5_000_000,
    size=len(high_value_indices)
).round(2)


# 2. Large cash transactions
# Some high-value transactions are specifically Cash
cash_indices = np.random.choice(
    high_value_indices,
    size=50,
    replace=False
)

df.loc[cash_indices, "Transaction_Type"] = "Cash"


# 3. High-risk country transactions
high_risk_indices = np.random.choice(
    df.index,
    size=100,
    replace=False
)

df.loc[high_risk_indices, "Country"] = np.random.choice(
    ["Iran", "Syria", "North Korea"],
    size=len(high_risk_indices)
)


# 4. PEP + high-value transactions
pep_indices = np.random.choice(
    df.index,
    size=50,
    replace=False
)

df.loc[pep_indices, "Is_PEP"] = 1

df.loc[pep_indices, "Amount"] = np.random.uniform(
    500_001,
    3_000_000,
    size=len(pep_indices)
).round(2)


# 5. High transaction frequency
high_frequency_indices = np.random.choice(
    df.index,
    size=150,
    replace=False
)

df.loc[
    high_frequency_indices,
    "Transaction_Count_24H"
] = np.random.randint(
    11,
    25,
    size=len(high_frequency_indices)
)


# 6. High total transaction amount in 24 hours
df.loc[
    high_frequency_indices,
    "Total_Amount_24H"
] = np.random.uniform(
    1_000_000,
    5_000_000,
    size=len(high_frequency_indices)
).round(2)


# 7. Previous fraud history
previous_fraud_indices = np.random.choice(
    df.index,
    size=100,
    replace=False
)

df.loc[
    previous_fraud_indices,
    "Previous_Fraud_Count"
] = np.random.randint(
    1,
    5,
    size=len(previous_fraud_indices)
)
# 8. Structuring / Smurfing scenarios
# Create multiple transactions for the same customers
# within a short time period.

structuring_customers = [
    "CUST1001",
    "CUST1002",
    "CUST1003",
    "CUST1004",
    "CUST1005"
]

for customer in structuring_customers:

    customer_indices = df.index[
        df["Customer_ID"] == customer
    ].tolist()

    if len(customer_indices) >= 3:

        selected_indices = customer_indices[:4]

        base_time = df.loc[
            selected_indices[0],
            "Timestamp"
        ]

        for j, idx in enumerate(selected_indices):

            df.loc[idx, "Customer_ID"] = customer

            df.loc[idx, "Timestamp"] = (
                base_time + timedelta(
                    hours=j * 2
                )
            )

            df.loc[idx, "Amount"] = round(
                np.random.uniform(
                    300001,
                    500000
                ),
                2
            )

            df.loc[
                idx,
                "Transaction_Count_24H"
            ] = 4

            df.loc[
                idx,
                "Total_Amount_24H"
            ] = round(
                df.loc[
                    selected_indices,
                    "Amount"
                ].sum(),
                2
            )

df["Timestamp"] = pd.to_datetime(
    df["Timestamp"]
)

df = df.sort_values(
    "Timestamp"
).reset_index(drop=True)


# ============================================================
# Save dataset
# ============================================================

output_file = "data/transactions.csv"

df.to_csv(
    output_file,
    index=False
)


# ============================================================
# Display information
# ============================================================

print("=" * 60)
print("FCCM TRANSACTION DATASET GENERATED")
print("=" * 60)

print(f"Total transactions : {len(df)}")
print(f"Fraud transactions  : {df['Is_Fraud'].sum()}")
print(
    f"Fraud percentage    : "
    f"{df['Is_Fraud'].mean() * 100:.2f}%"
)

print("\nDataset columns:")
print(df.columns.tolist())

print("\nFirst 5 transactions:")
print(df.head())

print("\nFraud distribution:")
print(df["Is_Fraud"].value_counts())

print("\nDataset saved to:")
print(output_file)

print("=" * 60)