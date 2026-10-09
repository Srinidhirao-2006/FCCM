import sqlite3
from pathlib import Path
import uuid


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================================
# CREATE / UPDATE ALERT
# ============================================================

def create_alert(
    transaction_id,
    customer_id,
    alert_type,
    description,
    risk_score,
    severity,
    explanation=None
):
    """
    Create a new alert or update an existing OPEN alert
    for the same transaction.

    explanation:
        JSON string containing risk explanation details.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # CHECK FOR EXISTING OPEN ALERT
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT alert_id
            FROM alerts
            WHERE transaction_id = ?
            AND status = 'OPEN'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (transaction_id,)
        )

        existing_alert = cursor.fetchone()

        # ----------------------------------------------------
        # UPDATE EXISTING ALERT
        # ----------------------------------------------------

        if existing_alert:

            alert_id = existing_alert[0]

            cursor.execute(
                """
                UPDATE alerts
                SET
                    customer_id = ?,
                    alert_type = ?,
                    description = ?,
                    risk_score = ?,
                    severity = ?,
                    explanation = ?
                WHERE alert_id = ?
                """,
                (
                    customer_id,
                    alert_type,
                    description,
                    risk_score,
                    severity,
                    explanation,
                    alert_id
                )
            )

            connection.commit()

            print()
            print("=" * 70)
            print("⚠️ EXISTING ALERT UPDATED")
            print("=" * 70)
            print(f"Alert ID       : {alert_id}")
            print(f"Transaction ID : {transaction_id}")
            print(f"Risk Score     : {risk_score:.2f}")
            print(f"Severity       : {severity}")
            print("Explanation    : SAVED")
            print("=" * 70)

            return alert_id

        # ----------------------------------------------------
        # CREATE NEW ALERT
        # ----------------------------------------------------

        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"

        cursor.execute(
            """
            INSERT INTO alerts (
                alert_id,
                transaction_id,
                customer_id,
                alert_type,
                description,
                risk_score,
                severity,
                status,
                explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
            """,
            (
                alert_id,
                transaction_id,
                customer_id,
                alert_type,
                description,
                risk_score,
                severity,
                explanation
            )
        )

        connection.commit()

        print()
        print("=" * 70)
        print("🚨 ALERT CREATED")
        print("=" * 70)
        print(f"Alert ID       : {alert_id}")
        print(f"Transaction ID : {transaction_id}")
        print(f"Risk Score     : {risk_score:.2f}")
        print(f"Severity       : {severity}")
        print("Explanation    : SAVED")
        print("=" * 70)

        return alert_id

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# ============================================================
# GET OPEN ALERTS
# ============================================================

def get_open_alerts():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            alert_id,
            transaction_id,
            customer_id,
            alert_type,
            description,
            risk_score,
            severity,
            status,
            explanation,
            created_at
        FROM alerts
        WHERE status = 'OPEN'
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ============================================================
# CLOSE ALERT
# ============================================================

def close_alert(alert_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE alerts
        SET status = 'CLOSED'
        WHERE alert_id = ?
        """,
        (alert_id,)
    )

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    if updated:
        print(f"Alert closed : {alert_id}")
        return True

    print(f"Alert not found : {alert_id}")
    return False