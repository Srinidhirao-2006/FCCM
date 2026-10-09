import sqlite3
import time
import json
from pathlib import Path

import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "fccm.db"


# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FCCM Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )


# ============================================================
# DATABASE TABLE CHECK
# ============================================================

def table_exists(table_name):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    )

    exists = cursor.fetchone() is not None

    connection.close()

    return exists


# ============================================================
# SUMMARY
# ============================================================

def get_summary():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM transactions"
    )
    total_transactions = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE actual_fraud = 1
        """
    )
    confirmed_fraud = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE fraud_probability >= 50
        """
    )
    ml_predicted_fraud = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM alerts
        WHERE status = 'OPEN'
        """
    )
    open_alerts = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM alerts
        WHERE severity = 'CRITICAL'
          AND status = 'OPEN'
        """
    )
    critical_alerts = cursor.fetchone()[0]

    connection.close()

    return (
        total_transactions,
        confirmed_fraud,
        ml_predicted_fraud,
        open_alerts,
        critical_alerts,
    )


# ============================================================
# RISK DISTRIBUTION
# ============================================================

def get_risk_distribution():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT risk_level, COUNT(*)
        FROM transactions
        GROUP BY risk_level
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ============================================================
# ML DISTRIBUTION
# ============================================================

def get_ml_distribution():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            CASE
                WHEN fraud_probability >= 50
                    THEN 'ML FRAUD'
                ELSE 'ML NORMAL'
            END AS prediction,
            COUNT(*)
        FROM transactions
        GROUP BY prediction
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ============================================================
# RECENT ALERTS
# ============================================================

def get_recent_alerts(limit=10):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            alert_id,
            transaction_id,
            customer_id,
            alert_type,
            severity,
            risk_score,
            status,
            description,
            created_at
        FROM alerts
        ORDER BY
            CASE
                WHEN status = 'OPEN' THEN 0
                ELSE 1
            END,
            created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ============================================================
# RECENT TRANSACTIONS
# ============================================================

def get_recent_transactions(limit=20):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            transaction_id,
            customer_id,
            timestamp,
            amount,
            transaction_type,
            merchant_category,
            country,
            is_pep,
            transaction_count_24h,
            total_amount_24h,
            ip_risk_score,
            previous_fraud_count,
            risk_score,
            risk_level,
            fraud_probability,
            actual_fraud,
            created_at
        FROM transactions
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ============================================================
# STORED EXPLANATION
# ============================================================

def get_stored_explanation(transaction_id):

    if not table_exists("risk_explanations"):
        return None

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                transaction_id,
                customer_id,
                final_risk_level,
                combined_risk_score,
                explanation_count,
                explanation_json,
                created_at,
                updated_at
            FROM risk_explanations
            WHERE transaction_id = ?
            """,
            (transaction_id,),
        )

        row = cursor.fetchone()

    except sqlite3.Error:

        row = None

    connection.close()

    return row


# ============================================================
# BEHAVIORAL ANALYSIS
# ============================================================

def get_behavioral_analysis(customer_id):

    if not table_exists("behavioral_analysis"):
        return None

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                customer_id,
                transaction_count,
                behavioral_risk_score,
                behavioral_risk_level
            FROM behavioral_analysis
            WHERE customer_id = ?
            ORDER BY transaction_count DESC
            LIMIT 1
            """,
            (customer_id,),
        )

        row = cursor.fetchone()

    except sqlite3.Error:

        row = None

    connection.close()

    return row


# ============================================================
# FALLBACK RISK FACTORS
# ============================================================

def get_risk_factors(transaction):

    (
        transaction_id,
        customer_id,
        timestamp,
        amount,
        transaction_type,
        merchant_category,
        country,
        is_pep,
        transaction_count_24h,
        total_amount_24h,
        ip_risk_score,
        previous_fraud_count,
        risk_score,
        risk_level,
        fraud_probability,
        actual_fraud,
        created_at,
    ) = transaction

    factors = []

    if amount is not None and amount >= 1_000_000:

        factors.append(
            "💰 High-value transaction above ₹10 lakh"
        )

    if country in {
        "Iran",
        "Syria",
        "North Korea",
    }:

        factors.append(
            f"🌍 High-risk country: {country}"
        )

    if is_pep == 1:

        factors.append(
            "👤 Transaction associated with a Politically Exposed Person (PEP)"
        )

    if (
        transaction_count_24h is not None
        and transaction_count_24h > 10
    ):

        factors.append(
            "🔁 High transaction frequency in 24 hours"
        )

    if (
        total_amount_24h is not None
        and total_amount_24h > 1_500_000
    ):

        factors.append(
            "💸 High total transaction value in 24 hours"
        )

    if (
        ip_risk_score is not None
        and ip_risk_score >= 70
    ):

        factors.append(
            "🌐 High IP risk score"
        )

    if (
        previous_fraud_count is not None
        and previous_fraud_count > 0
    ):

        factors.append(
            "⚠️ Previous fraud history detected"
        )

    if (
        transaction_type == "Cash"
        and amount is not None
        and 300_000 <= amount <= 500_000
        and transaction_count_24h is not None
        and transaction_count_24h >= 3
    ):

        factors.append(
            "🏦 Possible cash structuring pattern"
        )

    if (
        fraud_probability is not None
        and fraud_probability >= 50
    ):

        factors.append(
            f"🤖 ML fraud probability: "
            f"{fraud_probability:.2f}%"
        )

    if not factors:

        factors.append(
            "No major risk factor identified from stored transaction fields."
        )

    return factors


# ============================================================
# PARSE EXPLANATION JSON
# ============================================================

def parse_explanation_json(explanation_json):

    try:

        explanation_data = json.loads(
            explanation_json
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        return []

    if isinstance(
        explanation_data,
        list,
    ):

        return explanation_data

    if isinstance(
        explanation_data,
        dict,
    ):

        explanations = explanation_data.get(
            "explanations",
            [],
        )

        if isinstance(
            explanations,
            list,
        ):

            return explanations

    return []


# ============================================================
# DISPLAY STORED AI EXPLANATION
# ============================================================

def display_stored_explanation(
    transaction_id,
    customer_id,
    fraud_probability,
    risk_score,
):

    stored_explanation = get_stored_explanation(
        transaction_id
    )

    if stored_explanation is None:

        st.info(
            "ℹ️ Detailed AI risk explanation has not "
            "been stored for this transaction."
        )

        return False

    (
        explanation_transaction_id,
        explanation_customer_id,
        explanation_risk_level,
        explanation_combined_score,
        explanation_count,
        explanation_json,
        explanation_created_at,
        explanation_updated_at,
    ) = stored_explanation

    explanations = parse_explanation_json(
        explanation_json
    )

    st.success(
        f"🧠 AI Risk Explanation Available "
        f"({len(explanations)} factors)"
    )

    # ========================================================
    # EXPLANATION SUMMARY
    # ========================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write(
            f"**Final Risk Level:** "
            f"{explanation_risk_level}"
        )

    with col2:

        if explanation_combined_score is not None:

            st.write(
                f"**Combined Risk Score:** "
                f"{float(explanation_combined_score):.2f}"
            )

        else:

            st.write(
                "**Combined Risk Score:** N/A"
            )

    with col3:

        st.write(
            f"**Explanation Factors:** "
            f"{len(explanations)}"
        )

    # ========================================================
    # 4-MODEL RISK FUSION
    # ========================================================

    st.markdown(
        "### ⚖️ Multi-Model Risk Fusion"
    )

    # --------------------------------------------------------
    # FINAL 4-MODEL WEIGHTS
    # --------------------------------------------------------

    AML_WEIGHT = 0.35
    ML_WEIGHT = 0.30
    PCA_WEIGHT = 0.15
    BEHAVIOR_WEIGHT = 0.20

    # --------------------------------------------------------
    # DEFAULT VALUES
    # --------------------------------------------------------

    ml_risk = 0.0
    pca_risk = 0.0
    behavior_risk = 0.0

    # --------------------------------------------------------
    # READ ML / PCA CONTRIBUTIONS FROM EXPLANATION
    # --------------------------------------------------------

    for item in explanations:

        if not isinstance(
            item,
            dict,
        ):

            continue

        title = str(
            item.get(
                "title",
                "",
            )
        ).upper()

        category = str(
            item.get(
                "category",
                "",
            )
        ).upper()

        contribution = item.get(
            "contribution",
            0,
        )

        try:

            contribution = float(
                contribution
            )

        except (
            TypeError,
            ValueError,
        ):

            contribution = 0.0

        # ----------------------------------------------------
        # ML
        # ----------------------------------------------------

        if (
            "ML" in title
            or category == "ML"
        ):

            ml_risk = max(
                ml_risk,
                contribution,
            )

        # ----------------------------------------------------
        # PCA
        # ----------------------------------------------------

        if (
            "PCA" in title
            or category == "PCA"
        ):

            pca_risk = max(
                pca_risk,
                contribution,
            )

        # ----------------------------------------------------
        # BEHAVIOR
        # ----------------------------------------------------

        if (
            "BEHAVIOR" in title
            or "BEHAVIOURAL" in title
            or category in {
                "BEHAVIOR",
                "BEHAVIOUR",
                "BEHAVIORAL",
            }
        ):

            behavior_risk = max(
                behavior_risk,
                contribution,
            )

    # ========================================================
    # GET BEHAVIORAL SCORE FROM DATABASE
    # ========================================================

    behavioral_row = get_behavioral_analysis(
        customer_id
    )

    if behavioral_row is not None:

        try:

            database_behavior_score = float(
                behavioral_row[2]
            )

            # Use database behavioral score
            # if explanation did not contain one.

            if behavior_risk == 0:

                behavior_risk = (
                    database_behavior_score
                )

        except (
            TypeError,
            ValueError,
        ):

            pass

    # ========================================================
    # ML RISK
    # ========================================================

    if (
        ml_risk == 0
        and fraud_probability is not None
    ):

        try:

            ml_risk = float(
                fraud_probability
            )

        except (
            TypeError,
            ValueError,
        ):

            ml_risk = 0.0

    # ========================================================
    # WEIGHTED CONTRIBUTIONS
    # ========================================================

    ml_contribution = (
        ml_risk
        * ML_WEIGHT
    )

    pca_contribution = (
        pca_risk
        * PCA_WEIGHT
    )

    behavioral_contribution = (
        behavior_risk
        * BEHAVIOR_WEIGHT
    )

    # ========================================================
    # AML CONTRIBUTION
    # ========================================================

    if explanation_combined_score is not None:

        stored_score = float(
            explanation_combined_score
        )

        aml_contribution = (
            stored_score
            - ml_contribution
            - pca_contribution
            - behavioral_contribution
        )

        aml_contribution = max(
            0.0,
            aml_contribution,
        )

    else:

        aml_contribution = 0.0

    # ========================================================
    # DISPLAY 4 MODEL CONTRIBUTIONS
    # ========================================================

    fusion_col1, fusion_col2, fusion_col3, fusion_col4 = (
        st.columns(4)
    )

    with fusion_col1:

        st.metric(
            "AML Contribution",
            f"{aml_contribution:.2f}",
            "35% weight",
        )

    with fusion_col2:

        st.metric(
            "ML Contribution",
            f"{ml_contribution:.2f}",
            "30% weight",
        )

    with fusion_col3:

        st.metric(
            "PCA Contribution",
            f"{pca_contribution:.2f}",
            "15% weight",
        )

    with fusion_col4:

        st.metric(
            "Behavior Contribution",
            f"{behavioral_contribution:.2f}",
            "20% weight",
        )

    # ========================================================
    # FUSION FORMULA
    # ========================================================

    if explanation_combined_score is not None:

        final_score = float(
            explanation_combined_score
        )

        st.info(
            f"Fusion = "
            f"({aml_contribution:.2f}) + "
            f"({ml_contribution:.2f}) + "
            f"({pca_contribution:.2f}) + "
            f"({behavioral_contribution:.2f}) "
            f"= **{final_score:.2f}**"
        )

    # ========================================================
    # WHY WAS THIS TRANSACTION FLAGGED?
    # ========================================================

    st.markdown(
        "### 🔍 Why was this transaction flagged?"
    )

    if explanations:

        for index, item in enumerate(
            explanations,
            start=1,
        ):

            if isinstance(
                item,
                dict,
            ):

                category = item.get(
                    "category",
                    "",
                )

                rule = item.get(
                    "rule",
                    "",
                )

                title = item.get(
                    "title",
                    "",
                )

                description = item.get(
                    "description",
                    "",
                )

                reason = item.get(
                    "reason",
                    "",
                )

                contribution = item.get(
                    "contribution",
                    None,
                )

                # ------------------------------------------------
                # Heading
                # ------------------------------------------------

                if rule:

                    heading = (
                        rule
                        .replace(
                            "_",
                            " ",
                        )
                        .title()
                    )

                elif title:

                    heading = title

                else:

                    heading = "Risk Factor"

                if category:

                    heading = (
                        f"{category} — "
                        f"{heading}"
                    )

                st.markdown(
                    f"**{index}. {heading}**"
                )

                # ------------------------------------------------
                # Description
                # ------------------------------------------------

                explanation_text = (
                    description
                    or reason
                )

                if explanation_text:

                    st.write(
                        explanation_text
                    )

                # ------------------------------------------------
                # Contribution
                # ------------------------------------------------

                if contribution is not None:

                    try:

                        contribution_value = float(
                            contribution
                        )

                        st.caption(
                            f"Contribution: "
                            f"+{contribution_value:.2f}"
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        st.caption(
                            f"Contribution: "
                            f"{contribution}"
                        )

            else:

                st.markdown(
                    f"**{index}.** {item}"
                )

            st.divider()

    else:

        st.info(
            "The explanation was stored, but no "
            "individual explanation factors were returned."
        )

    # ========================================================
    # BEHAVIORAL ANALYSIS
    # ========================================================

    behavioral_row = get_behavioral_analysis(
        customer_id
    )

    if behavioral_row is not None:

        (
            behavioral_customer,
            behavioral_transaction_count,
            behavioral_score,
            behavioral_level,
        ) = behavioral_row

        st.markdown(
            "### 🧠 Behavioral Risk Analysis"
        )

        behavior_col1, behavior_col2, behavior_col3 = (
            st.columns(3)
        )

        with behavior_col1:

            st.metric(
                "Customer Transactions",
                f"{behavioral_transaction_count}",
            )

        with behavior_col2:

            st.metric(
                "Behavioral Risk Score",
                f"{float(behavioral_score):.2f}",
            )

        with behavior_col3:

            st.metric(
                "Behavioral Risk Level",
                str(behavioral_level),
            )

    # ========================================================
    # STORAGE DETAILS
    # ========================================================

    with st.expander(
        "🗄️ Explanation Storage Details"
    ):

        st.write(
            f"**Transaction ID:** "
            f"{explanation_transaction_id}"
        )

        st.write(
            f"**Customer ID:** "
            f"{explanation_customer_id}"
        )

        st.write(
            f"**Created:** "
            f"{explanation_created_at}"
        )

        st.write(
            f"**Updated:** "
            f"{explanation_updated_at}"
        )

    return True


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ Financial Crime & Compliance Management System"
)

st.markdown(
    """
    ### Real-Time Transaction Monitoring & AI-Based Fraud Detection

    **Kafka → AML Rules → ML Fraud Detection → PCA Anomaly Detection
    → Behavioral Analysis → Multi-Model Risk Fusion
    → Explainability → Alerts → SQLite**
    """
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🛡️ FCCM Control Panel"
)

st.sidebar.success(
    "System Connected"
)

st.sidebar.markdown(
    "### System Components"
)

st.sidebar.write(
    "🟢 Apache Kafka Streaming"
)

st.sidebar.write(
    "🟢 AML Rule Engine"
)

st.sidebar.write(
    "🟢 ML Fraud Detection"
)

st.sidebar.write(
    "🟢 PCA Anomaly Detection"
)

st.sidebar.write(
    "🟢 Behavioral Analysis"
)

st.sidebar.write(
    "🟢 Multi-Model Risk Fusion"
)

st.sidebar.write(
    "🟢 Risk Explainability"
)

st.sidebar.write(
    "🟢 Alert Management"
)

st.sidebar.write(
    "🟢 SQLite Database"
)

st.sidebar.divider()

st.sidebar.markdown(
    "### Risk Model Weights"
)

st.sidebar.write(
    "AML Rules: **35%**"
)

st.sidebar.write(
    "ML Fraud Model: **30%**"
)

st.sidebar.write(
    "PCA Anomaly: **15%**"
)

st.sidebar.write(
    "Behavioral Analysis: **20%**"
)

st.sidebar.divider()

if st.sidebar.button(
    "🔄 Refresh Dashboard",
    use_container_width=True,
):

    st.rerun()

auto_refresh = st.sidebar.checkbox(
    "⏱️ Auto Refresh",
    value=False,
)

if auto_refresh:

    refresh_seconds = st.sidebar.slider(
        "Refresh interval (seconds)",
        min_value=5,
        max_value=60,
        value=10,
    )

else:

    refresh_seconds = 10


# ============================================================
# DATABASE CHECK
# ============================================================

if not DB_PATH.exists():

    st.error(
        f"Database not found: {DB_PATH}"
    )

    st.stop()


try:

    (
        total_transactions,
        confirmed_fraud,
        ml_predicted_fraud,
        open_alerts,
        critical_alerts,
    ) = get_summary()

except Exception as e:

    st.error(
        f"Database connection error: {e}"
    )

    st.stop()


# ============================================================
# TOP METRICS
# ============================================================

st.subheader(
    "📊 System Overview"
)

col1, col2, col3, col4, col5 = (
    st.columns(5)
)

with col1:

    st.metric(
        "Total Transactions",
        f"{total_transactions:,}",
    )

with col2:

    st.metric(
        "Confirmed Fraud",
        f"{confirmed_fraud:,}",
    )

with col3:

    st.metric(
        "ML Predicted Fraud",
        f"{ml_predicted_fraud:,}",
    )

with col4:

    st.metric(
        "Open Alerts",
        f"{open_alerts:,}",
    )

with col5:

    st.metric(
        "Critical Alerts",
        f"{critical_alerts:,}",
    )

st.divider()


# ============================================================
# RISK ANALYTICS
# ============================================================

st.subheader(
    "📈 Risk Analytics"
)

risk_rows = get_risk_distribution()

risk_data = {}

for risk_level, count in risk_rows:

    risk_data[
        risk_level or "UNKNOWN"
    ] = count

low = risk_data.get(
    "LOW",
    0,
)

medium = risk_data.get(
    "MEDIUM",
    0,
)

high = risk_data.get(
    "HIGH",
    0,
)

critical = risk_data.get(
    "CRITICAL",
    0,
)

col1, col2 = st.columns(
    [1, 2]
)

with col1:

    st.markdown(
        "### Risk Distribution"
    )

    st.success(
        f"🟢 LOW: {low}"
    )

    st.info(
        f"🟡 MEDIUM: {medium}"
    )

    st.warning(
        f"🟠 HIGH: {high}"
    )

    st.error(
        f"🔴 CRITICAL: {critical}"
    )

with col2:

    st.markdown(
        "### Transaction Risk Distribution"
    )

    chart_data = {
        "LOW": low,
        "MEDIUM": medium,
        "HIGH": high,
        "CRITICAL": critical,
    }

    st.bar_chart(
        chart_data
    )

st.divider()


# ============================================================
# ML ANALYTICS
# ============================================================

st.subheader(
    "🤖 Machine Learning Fraud Analytics"
)

ml_rows = get_ml_distribution()

ml_data = {}

for prediction, count in ml_rows:

    ml_data[prediction] = count

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "ML Predicted Fraud",
        f"{ml_data.get('ML FRAUD', 0):,}",
    )

    st.metric(
        "ML Predicted Normal",
        f"{ml_data.get('ML NORMAL', 0):,}",
    )

with col2:

    st.markdown(
        "### ML Prediction Distribution"
    )

    st.bar_chart(
        ml_data
    )

st.info(
    """
    **ML Predicted Fraud** is calculated from the stored
    fraud probability using a 50% decision threshold.
    """
)

st.divider()


# ============================================================
# RECENT ALERTS
# ============================================================

st.subheader(
    "🚨 Recent Alerts"
)

alerts = get_recent_alerts(
    10
)

if alerts:

    for alert in alerts:

        (
            alert_id,
            transaction_id,
            customer_id,
            alert_type,
            severity,
            risk_score,
            status,
            description,
            created_at,
        ) = alert

        if severity == "CRITICAL":

            container = st.error

        elif severity == "HIGH":

            container = st.warning

        else:

            container = st.info

        safe_risk_score = (
            float(risk_score)
            if risk_score is not None
            else 0.0
        )

        container(
            f"**{severity}** | "
            f"Transaction: `{transaction_id}` | "
            f"Risk Score: **{safe_risk_score:.2f}** | "
            f"Status: **{status}**"
        )

        with st.expander(
            f"🔍 View alert details — {alert_id}"
        ):

            st.write(
                f"**Alert ID:** {alert_id}"
            )

            st.write(
                f"**Transaction ID:** "
                f"{transaction_id}"
            )

            st.write(
                f"**Customer ID:** "
                f"{customer_id}"
            )

            st.write(
                f"**Alert Type:** "
                f"{alert_type}"
            )

            st.write(
                f"**Severity:** "
                f"{severity}"
            )

            st.write(
                f"**Risk Score:** "
                f"{safe_risk_score:.2f}"
            )

            st.write(
                f"**Status:** "
                f"{status}"
            )

            st.write(
                f"**Created:** "
                f"{created_at}"
            )

            if description:

                st.write(
                    f"**Description:** "
                    f"{description}"
                )

else:

    st.success(
        "No alerts found."
    )

st.divider()


# ============================================================
# RECENT TRANSACTIONS
# ============================================================

st.subheader(
    "💳 Recent Transactions"
)

transactions = get_recent_transactions(
    20
)

if transactions:

    for transaction in transactions:

        (
            transaction_id,
            customer_id,
            timestamp,
            amount,
            transaction_type,
            merchant_category,
            country,
            is_pep,
            transaction_count_24h,
            total_amount_24h,
            ip_risk_score,
            previous_fraud_count,
            risk_score,
            risk_level,
            fraud_probability,
            actual_fraud,
            created_at,
        ) = transaction

        # ----------------------------------------------------
        # Risk icon
        # ----------------------------------------------------

        if risk_level == "CRITICAL":

            icon = "🔴"

        elif risk_level == "HIGH":

            icon = "🟠"

        elif risk_level == "MEDIUM":

            icon = "🟡"

        else:

            icon = "🟢"

        safe_amount = (
            float(amount)
            if amount is not None
            else 0.0
        )

        safe_risk_score = (
            float(risk_score)
            if risk_score is not None
            else 0.0
        )

        # ----------------------------------------------------
        # Transaction Expander
        # ----------------------------------------------------

        with st.expander(
            f"{icon} {transaction_id} | "
            f"₹{safe_amount:,.2f} | "
            f"{risk_level} | "
            f"Risk: {safe_risk_score:.2f}"
        ):

            # =================================================
            # TRANSACTION INFORMATION
            # =================================================

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    f"**Customer:** "
                    f"{customer_id}"
                )

                st.write(
                    f"**Timestamp:** "
                    f"{timestamp}"
                )

                st.write(
                    f"**Country:** "
                    f"{country}"
                )

                st.write(
                    f"**Type:** "
                    f"{transaction_type}"
                )

                st.write(
                    f"**Merchant:** "
                    f"{merchant_category}"
                )

            # =================================================
            # RISK INFORMATION
            # =================================================

            with col2:

                st.write(
                    f"**Risk Score:** "
                    f"{safe_risk_score:.2f}"
                )

                st.write(
                    f"**Risk Level:** "
                    f"{risk_level}"
                )

                if fraud_probability is not None:

                    st.write(
                        f"**ML Fraud Probability:** "
                        f"{float(fraud_probability):.2f}%"
                    )

                else:

                    st.write(
                        "**ML Fraud Probability:** N/A"
                    )

                st.write(
                    f"**Actual Fraud:** "
                    f"{'YES' if actual_fraud else 'NO'}"
                )

            # =================================================
            # BEHAVIOR INFORMATION
            # =================================================

            with col3:

                st.write(
                    f"**PEP:** "
                    f"{'YES' if is_pep else 'NO'}"
                )

                st.write(
                    f"**IP Risk:** "
                    f"{ip_risk_score}"
                )

                st.write(
                    f"**Transactions in 24H:** "
                    f"{transaction_count_24h}"
                )

                if total_amount_24h is not None:

                    st.write(
                        f"**Total Amount in 24H:** "
                        f"₹{float(total_amount_24h):,.2f}"
                    )

                else:

                    st.write(
                        "**Total Amount in 24H:** N/A"
                    )

                st.write(
                    f"**Previous Fraud Count:** "
                    f"{previous_fraud_count}"
                )

            st.divider()

            # =================================================
            # AI RISK EXPLANATION
            # =================================================

            st.markdown(
                "### 🧠 AI Risk Explanation"
            )

            explanation_found = (
                display_stored_explanation(
                    transaction_id,
                    customer_id,
                    fraud_probability,
                    safe_risk_score,
                )
            )

            # =================================================
            # FALLBACK EXPLANATION
            # =================================================

            if not explanation_found:

                st.markdown(
                    "#### 🔍 Transaction Risk Factors"
                )

                factors = get_risk_factors(
                    transaction
                )

                for factor in factors:

                    st.write(
                        f"• {factor}"
                    )

            st.caption(
                f"Transaction created: "
                f"{created_at}"
            )

else:

    st.info(
        "No transactions found."
    )

st.divider()


# ============================================================
# AI / ML PIPELINE ARCHITECTURE
# ============================================================

st.subheader(
    "🧠 AI/ML Risk Detection Architecture"
)

architecture_col1, architecture_col2 = (
    st.columns([1, 1])
)


# ============================================================
# REAL-TIME PROCESSING
# ============================================================

with architecture_col1:

    st.markdown(
        """
        ### Real-Time Processing

        **1️⃣ Transaction Source**

        ↓

        **2️⃣ Apache Kafka**

        Topic: `transactions`

        ↓

        **3️⃣ Kafka Consumer**

        ↓

        **4️⃣ AML Rule Engine**

        Detects:

        - High-value transactions
        - High-risk countries
        - PEP transactions
        - High transaction frequency
        - High 24-hour transaction value
        - Previous fraud history
        - High IP risk
        - Cash structuring

        ↓

        **5️⃣ ML Fraud Detection**

        Random Forest based supervised learning

        ↓

        **6️⃣ PCA Anomaly Detection**

        Unsupervised detection of unusual transaction behaviour

        ↓

        **7️⃣ Behavioral Analysis**

        Customer-level transaction behaviour analysis
        """
    )


# ============================================================
# RISK FUSION
# ============================================================

with architecture_col2:

    st.markdown(
        """
        ### Multi-Model Risk Fusion

        **AML Risk → 35%**

        **ML Fraud Probability → 30%**

        **PCA Anomaly Risk → 15%**

        **Behavioral Risk → 20%**

        ↓

        ### Combined Risk Score

        ↓

        **Risk Explanation**

        Identifies the major factors responsible for the
        transaction's risk classification.

        ↓

        **Alert Management**

        HIGH / CRITICAL transactions generate alerts.

        ↓

        **SQLite Database**

        Stores transactions, risk scores, alerts,
        behavioral analysis and stored risk explanations.

        ↓

        **Streamlit Dashboard**

        Provides real-time monitoring and investigation support.
        """
    )


st.divider()


# ============================================================
# MODEL WEIGHT SUMMARY
# ============================================================

st.subheader(
    "⚖️ 4-Model Risk Fusion"
)

weight_col1, weight_col2, weight_col3, weight_col4 = (
    st.columns(4)
)

with weight_col1:

    st.metric(
        "AML Rules",
        "35%",
    )

with weight_col2:

    st.metric(
        "ML Fraud",
        "30%",
    )

with weight_col3:

    st.metric(
        "PCA Anomaly",
        "15%",
    )

with weight_col4:

    st.metric(
        "Behavioral",
        "20%",
    )

st.info(
    """
    Final Risk Score =
    **(AML × 0.35) + (ML × 0.30) +
    (PCA × 0.15) + (Behavioral × 0.20)**
    """
)

st.divider()


# ============================================================
# PROJECT STATUS
# ============================================================

st.subheader(
    "⚙️ System Status"
)

status_col1, status_col2, status_col3, status_col4 = (
    st.columns(4)
)

with status_col1:

    st.success(
        "🟢 Kafka Pipeline"
    )

with status_col2:

    st.success(
        "🟢 AML Detection"
    )

with status_col3:

    st.success(
        "🟢 ML + PCA Detection"
    )

with status_col4:

    st.success(
        "🟢 Explainability + Alerts"
    )

st.divider()


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "FCCM | Financial Crime & Compliance Management System | "
    "Real-Time AI-Based Transaction Monitoring"
)


# ============================================================
# AUTO REFRESH
# ============================================================

if auto_refresh:

    time.sleep(
        refresh_seconds
    )

    st.rerun()