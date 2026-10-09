import sqlite3
from pathlib import Path


# ============================================================
# FCCM Database Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "data"

DATABASE_DIR.mkdir(
    exist_ok=True
)

DATABASE_PATH = DATABASE_DIR / "fccm.db"


# ============================================================
# Database Connection
# ============================================================

def get_connection():
    """
    Create and return a SQLite database connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# Initialize Database
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Transactions table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transaction_id TEXT UNIQUE NOT NULL,

            customer_id TEXT NOT NULL,

            timestamp TEXT NOT NULL,

            amount REAL NOT NULL,

            transaction_type TEXT,

            merchant_category TEXT,

            country TEXT,

            is_pep INTEGER DEFAULT 0,

            account_age_days INTEGER,

            transaction_count_24h INTEGER,

            total_amount_24h REAL,

            device_id TEXT,

            ip_risk_score REAL,

            previous_fraud_count INTEGER,

            actual_fraud INTEGER,

            fraud_probability REAL,

            risk_score REAL,

            risk_level TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # Alerts table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            alert_id TEXT UNIQUE NOT NULL,

            transaction_id TEXT NOT NULL,

            customer_id TEXT NOT NULL,

            alert_type TEXT NOT NULL,

            description TEXT,

            risk_score REAL,

            severity TEXT,

            status TEXT DEFAULT 'OPEN',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (
                transaction_id
            )
            REFERENCES transactions (
                transaction_id
            )
        )
    """)

    # --------------------------------------------------------
    # Cases table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT UNIQUE NOT NULL,

            alert_id TEXT NOT NULL,

            customer_id TEXT NOT NULL,

            assigned_to TEXT,

            status TEXT DEFAULT 'OPEN',

            investigation_notes TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (
                alert_id
            )
            REFERENCES alerts (
                alert_id
            )
        )
    """)

    connection.commit()

    connection.close()

    print("FCCM database initialized successfully.")
    print(f"Database location: {DATABASE_PATH}")


# ============================================================
# Run directly
# ============================================================

if __name__ == "__main__":

    initialize_database()