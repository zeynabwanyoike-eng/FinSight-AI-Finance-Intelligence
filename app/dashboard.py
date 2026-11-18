
import streamlit as st
import pandas as pd
import tempfile
from pathlib import Path
from html import escape
import sys

# Ensure the repository root is importable on Streamlit Cloud and locally.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.process_invoice import process_invoice_pdf
from app.financial_dashboard import get_dashboard_metrics
from app.invoice_manager import (
    get_all_invoices,
    search_invoices,
    filter_invoices
)
from app.supplier_analytics import get_supplier_analytics
from app.approval_manager import get_approval_history
from app.anomaly_detector import get_all_anomalies
from app.finance_assistant import answer_question
from app.payment_manager import get_payment_summary, record_payment
from app.payment_reconciliation import (
    reconcile_payments,
    get_reconciliation_summary
)
from database.invoice_database import get_connection


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FinSight | Finance Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --navy: #101B35;
    --navy-light: #1B2A49;
    --blue: #4263EB;
    --blue-light: #EEF2FF;
    --background: #F4F6FB;
    --white: #FFFFFF;
    --text: #17233D;
    --muted: #78849A;
    --border: #E7EAF1;
    --green: #14966B;
    --red: #D94B5B;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: var(--background);
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1600px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    letter-spacing: -0.5px;
}

h1 {
    font-size: 30px !important;
    font-weight: 800 !important;
}

h2 {
    font-size: 22px !important;
    font-weight: 750 !important;
}

h3 {
    font-size: 17px !important;
    font-weight: 700 !important;
}

p, label {
    color: var(--text);
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #101B35 0%,
        #172642 100%
    );
    border-right: none;
}

[data-testid="stSidebar"] * {
    color: #E5EAF5 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 10px 12px;
    border-radius: 9px;
    font-size: 13px;
    font-weight: 600;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #263755;
}

[data-testid="stSidebar"] hr {
    border-color: #33435F;
}

.sidebar-brand {
    font-size: 22px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.8px;
    padding: 10px 0 2px 0;
}

.sidebar-tagline {
    color: #AAB8D0;
    font-size: 11px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}

/* PAGE HEADER */

.page-eyebrow {
    color: var(--blue);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.page-description {
    color: var(--muted);
    font-size: 13px;
    margin-top: -10px;
    margin-bottom: 25px;
}

/* HERO */

.hero-panel {
    background: linear-gradient(
        115deg,
        #142343 0%,
        #233D70 65%,
        #3557A5 100%
    );
    border-radius: 18px;
    padding: 26px 30px;
    margin: 8px 0 25px 0;
    color: white;
    box-shadow: 0 10px 25px rgba(16, 27, 53, 0.10);
}

.hero-label {
    color: #B9C9F1;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

.hero-title {
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 800;
    margin-top: 9px;
    letter-spacing: -0.7px;
}

.hero-description {
    color: #D2DCF2;
    font-size: 13px;
    margin-top: 7px;
}

/* KPI CARDS */

.kpi-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 20px;
    min-height: 145px;
    box-shadow: 0 4px 14px rgba(20, 35, 65, 0.035);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 9px 22px rgba(20, 35, 65, 0.08);
}

.kpi-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.kpi-label {
    color: #7B879B;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}

.kpi-icon {
    background: #EEF2FF;
    color: #4263EB;
    border-radius: 9px;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
}

.kpi-value {
    color: #14213D;
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -0.8px;
    margin-top: 15px;
    overflow-wrap: anywhere;
}

.kpi-detail {
    color: #929DB0;
    font-size: 11px;
    margin-top: 6px;
}

/* SECTION HEADERS */

.section-heading {
    font-size: 17px;
    color: #17233D;
    font-weight: 800;
    margin-top: 24px;
    margin-bottom: 4px;
}

.section-caption {
    color: #8994A8;
    font-size: 12px;
    margin-bottom: 15px;
}

/* PANELS */

.content-panel {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 4px 14px rgba(20, 35, 65, 0.025);
}

.metric-panel {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 17px;
    min-height: 100px;
}

.metric-panel-label {
    color: #8290A5;
    font-size: 11px;
    font-weight: 700;
}

.metric-panel-value {
    color: #17233D;
    font-size: 21px;
    font-weight: 800;
    margin-top: 8px;
}

/* STATUS */

.status-pill {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    background: #EEF2FF;
    color: #4263EB;
    font-size: 10px;
    font-weight: 800;
}

/* BUTTONS */

.stButton > button {
    border-radius: 9px;
    font-weight: 700;
    min-height: 42px;
    border: 1px solid #DCE2EF;
}

.stButton > button[kind="primary"] {
    background: #4263EB;
    border: none;
    color: white;
}

.stButton > button[kind="primary"]:hover {
    background: #304FC9;
    border: none;
    color: white;
}

/* INPUTS */

.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stTextArea textarea {
    border-radius: 9px;
}

/* DATAFRAMES */

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}

/* DIVIDERS */

hr {
    border-color: #E6EAF2;
    margin: 25px 0;
}

/* CAPTIONS */

.stCaption {
    color: var(--muted);
}

/* FILE UPLOADER */

[data-testid="stFileUploader"] {
    background: #FFFFFF;
    border: 1px dashed #B9C7E0;
    border-radius: 13px;
    padding: 12px;
}

/* PROGRESS */

.stProgress > div > div > div {
    background: #4263EB;
}

/* REMOVE EXTRA TOP SPACE */

[data-testid="stMainBlockContainer"] {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def money(value):
    try:
        return f"KES {float(value):,.2f}"
    except (TypeError, ValueError):
        return "KES 0.00"


def compact_money(value):
    try:
        value = float(value)

        if value >= 1_000_000:
            return f"KES {value / 1_000_000:.2f}M"

        if value >= 1_000:
            return f"KES {value / 1_000:.1f}K"

        return money(value)

    except (TypeError, ValueError):
        return "KES 0.00"


def render_page_header(eyebrow, title, description):
    st.markdown(
        f"""
        <div class="page-eyebrow">{escape(eyebrow)}</div>
        <h1>{escape(title)}</h1>
        <div class="page-description">
            {escape(description)}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_hero(title, description):
    st.markdown(
        f"""
        <div class="hero-panel">
            <div class="hero-label">
                FINANCE OPERATIONS INTELLIGENCE
            </div>
            <div class="hero-title">{escape(title)}</div>
            <div class="hero-description">
                {escape(description)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi(label, value, detail, icon):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">{escape(label)}</div>
                <div class="kpi-icon">{icon}</div>
            </div>
            <div class="kpi-value">{escape(str(value))}</div>
            <div class="kpi-detail">{escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metric_panel(label, value):
    st.markdown(
        f"""
        <div class="metric-panel">
            <div class="metric-panel-label">
                {escape(label)}
            </div>
            <div class="metric-panel-value">
                {escape(str(value))}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section_heading(title, caption=None):
    st.markdown(
        f"""
        <div class="section-heading">{escape(title)}</div>
        """,
        unsafe_allow_html=True
    )

    if caption:
        st.markdown(
            f'<div class="section-caption">{escape(caption)}</div>',
            unsafe_allow_html=True
        )


def load_invoice_data():
    invoices = get_all_invoices()

    if not invoices:
        return pd.DataFrame()

    return pd.DataFrame(invoices)



def add_payment_details(invoice_df):
    """Add payment status and balances without changing processing status."""
    if invoice_df.empty:
        return invoice_df

    result = invoice_df.copy()

    if "id" not in result.columns:
        result["payment_status"] = "UNAVAILABLE"
        result["amount_paid"] = 0.0
        result["outstanding_balance"] = pd.to_numeric(
            result.get("total", pd.Series(0, index=result.index)),
            errors="coerce"
        ).fillna(0)
        return result

    payment_statuses = []
    amounts_paid = []
    outstanding_balances = []

    for _, invoice_row in result.iterrows():
        invoice_id = invoice_row.get("id")
        try:
            summary = get_payment_summary(int(invoice_id))
        except (TypeError, ValueError, Exception):
            summary = None

        if summary is None:
            payment_statuses.append("UNAVAILABLE")
            amounts_paid.append(0.0)
            outstanding_balances.append(
                float(pd.to_numeric(invoice_row.get("total", 0), errors="coerce") or 0)
            )
            continue

        payment_statuses.append(summary.get("payment_status", "UNAVAILABLE"))
        amounts_paid.append(float(summary.get("amount_paid", 0) or 0))
        outstanding_balances.append(
            float(summary.get("outstanding_balance", 0) or 0)
        )

    result["payment_status"] = payment_statuses
    result["amount_paid"] = amounts_paid
    result["outstanding_balance"] = outstanding_balances
    return result


def show_dataframe(data):
    if isinstance(data, pd.DataFrame):
        if not data.empty:
            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No records available.")

    elif data:
        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No records available.")


def prepare_invoice_chart_data(invoices_df):
    if invoices_df.empty:
        return pd.DataFrame()

    if not {"invoice_date", "total"}.issubset(invoices_df.columns):
        return pd.DataFrame()

    chart_df = invoices_df.copy()

    chart_df["invoice_date"] = pd.to_datetime(
        chart_df["invoice_date"],
        errors="coerce",
        dayfirst=True
    )

    chart_df["total"] = pd.to_numeric(
        chart_df["total"],
        errors="coerce"
    )

    chart_df = chart_df.dropna(
        subset=["invoice_date", "total"]
    )

    if chart_df.empty:
        return pd.DataFrame()

    chart_df["month"] = (
        chart_df["invoice_date"]
        .dt.to_period("M")
        .astype(str)
    )

    return chart_df


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">FinSight</div>
        <div class="sidebar-tagline">
            AI Finance Intelligence
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.caption("WORKSPACE")

    page = st.radio(
        "NAVIGATION",
        [
            "Executive Overview",
            "Invoice Upload",
            "Invoice Register",
            "Record Payment",
            "Payment History",
            "Payment Reconciliation",
            "Supplier Analytics",
            "Approval Audit",
            "Anomaly Monitoring",
            "Finance Assistant"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.caption("FINANCE OPERATIONS")
    st.caption("Invoice Intelligence")
    st.caption("Financial Control")
    st.caption("Business Analytics")

    st.markdown("---")

    st.caption("FinSight | Finance Intelligence Platform")
    st.caption("Local finance operations workspace")


# =========================================================
# EXECUTIVE OVERVIEW
# =========================================================

if page == "Executive Overview":

    render_page_header(
        "Executive Dashboard",
        "Executive Overview",
        "Monitor financial performance, accounts payable and invoice operations."
    )

    metrics = get_dashboard_metrics()
    invoices_df = load_invoice_data()

    total_invoices = metrics.get("total_invoices", 0)
    total_suppliers = metrics.get("total_suppliers", 0)

    total_invoiced = float(
        metrics.get("total_invoiced", 0) or 0
    )

    total_paid = float(
        metrics.get("total_paid", 0) or 0
    )

    outstanding = float(
        metrics.get("outstanding_balance", 0) or 0
    )

    pending = metrics.get("pending_approval", 0)
    approved = metrics.get("approved", 0)
    rejected = metrics.get("rejected", 0)

    render_hero(
        "Your financial operations, at a glance.",
        "A central view of invoice activity, supplier spending, payment performance and financial exposure."
    )

    # KPI ROW ONE

    section_heading(
        "Financial Performance",
        "Key financial indicators across your invoice records."
    )

    columns = st.columns(4, gap="medium")

    kpis = [
        (
            "TOTAL INVOICES",
            f"{total_invoices:,}",
            "Invoices recorded",
            "▤"
        ),
        (
            "TOTAL SUPPLIERS",
            f"{total_suppliers:,}",
            "Suppliers in the system",
            "♙"
        ),
        (
            "TOTAL INVOICED",
            compact_money(total_invoiced),
            "Total invoice value",
            "↗"
        ),
        (
            "TOTAL PAID",
            compact_money(total_paid),
            "Payments recorded",
            "✓"
        )
    ]

    for column, item in zip(columns, kpis):
        with column:
            render_kpi(*item)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # KPI ROW TWO

    columns = st.columns(4, gap="medium")

    kpis = [
        (
            "OUTSTANDING BALANCE",
            compact_money(outstanding),
            "Unpaid invoice value",
            "◷"
        ),
        (
            "PENDING APPROVAL",
            f"{pending:,}",
            "Awaiting review",
            "⌛"
        ),
        (
            "APPROVED INVOICES",
            f"{approved:,}",
            "Approved for payment",
            "✓"
        ),
        (
            "REJECTED INVOICES",
            f"{rejected:,}",
            "Rejected during review",
            "!"
        )
    ]

    for column, item in zip(columns, kpis):
        with column:
            render_kpi(*item)

    st.markdown("---")

    # PAYMENT PERFORMANCE

    section_heading(
        "Payment Performance",
        "Understand how much of your recorded invoice value has been paid."
    )

    payment_columns = st.columns([1.4, 1, 1])

    payment_percentage = (
        (total_paid / total_invoiced) * 100
        if total_invoiced > 0
        else 0
    )

    with payment_columns[0]:

        st.markdown('<div class="content-panel">', unsafe_allow_html=True)

        st.markdown("**Payment completion**")

        st.markdown(
            f"""
            <div style="
                font-size:34px;
                font-weight:800;
                color:#17233D;
                margin:8px 0;
            ">
                {payment_percentage:.1f}%
            </div>
            """,
            unsafe_allow_html=True
        )

        st.progress(
            min(max(payment_percentage / 100, 0.0), 1.0)
        )

        st.caption(
            f"{money(total_paid)} paid out of {money(total_invoiced)} invoiced."
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with payment_columns[1]:
        render_metric_panel(
            "AVERAGE INVOICE VALUE",
            money(
                total_invoiced / total_invoices
                if total_invoices > 0
                else 0
            )
        )

    with payment_columns[2]:
        render_metric_panel(
            "OUTSTANDING BALANCE",
            money(outstanding)
        )

    st.markdown("---")

    # FINANCIAL CHARTS

    if not invoices_df.empty:

        section_heading(
            "Financial Analytics",
            "Visual insights into invoice activity and payment exposure."
        )

        chart_df = prepare_invoice_chart_data(invoices_df)

        chart_columns = st.columns([1.5, 1])

        with chart_columns[0]:

            st.markdown("**Monthly invoice spending**")

            if not chart_df.empty:

                monthly_data = (
                    chart_df.groupby("month")["total"]
                    .sum()
                    .sort_index()
                )

                st.line_chart(
                    monthly_data,
                    use_container_width=True,
                    height=300
                )

            else:
                st.info("No valid invoice dates available for this chart.")

        with chart_columns[1]:

            st.markdown("**Paid vs outstanding**")

            payment_chart = pd.DataFrame({
                "Amount": [total_paid, outstanding]
            }, index=["Paid", "Outstanding"])

            st.bar_chart(
                payment_chart,
                use_container_width=True,
                height=300
            )

        # STATUS DISTRIBUTION

        chart_columns = st.columns(2)

        with chart_columns[0]:

            st.markdown("**Invoice status distribution**")

            if "processing_status" in invoices_df.columns:

                status_data = (
                    invoices_df["processing_status"]
                    .fillna("UNKNOWN")
                    .value_counts()
                )

                st.bar_chart(
                    status_data,
                    use_container_width=True,
                    height=260
                )

        with chart_columns[1]:

            st.markdown("**Supplier spending**")

            supplier_data = get_supplier_analytics()

            if supplier_data:

                supplier_df = pd.DataFrame(supplier_data)

                if "total_invoiced" in supplier_df.columns:

                    supplier_df["total_invoiced"] = pd.to_numeric(
                        supplier_df["total_invoiced"],
                        errors="coerce"
                    )

                    supplier_chart = (
                        supplier_df
                        .dropna(subset=["total_invoiced"])
                        .set_index("supplier")["total_invoiced"]
                        .sort_values(ascending=False)
                    )

                    st.bar_chart(
                        supplier_chart,
                        use_container_width=True,
                        height=260
                    )

                else:
                    st.info("Supplier spending data is unavailable.")

            else:
                st.info("No supplier analytics available.")

        st.markdown("---")

        # SUPPLIER TABLE

        section_heading(
            "Supplier Performance",
            "Review invoice volumes and outstanding supplier balances."
        )

        supplier_data = get_supplier_analytics()

        if supplier_data:
            show_dataframe(pd.DataFrame(supplier_data))
        else:
            st.info("No supplier records available.")

        st.markdown("---")

        # RECENT INVOICES

        section_heading(
            "Recent Invoices",
            "The latest invoices recorded in the platform."
        )

        if "created_at" in invoices_df.columns:

            recent = invoices_df.sort_values(
                "created_at",
                ascending=False
            ).head(5)

        else:
            recent = invoices_df.head(5)

        show_dataframe(recent)

    else:
        st.info("No invoices have been recorded yet.")


# =========================================================
# INVOICE UPLOAD
# =========================================================

elif page == "Invoice Upload":

    render_page_header(
        "Invoice Processing",
        "Invoice Intelligence",
        "Upload supplier invoices for automatic extraction, validation and duplicate detection."
    )

    render_hero(
        "Turn supplier documents into structured financial data.",
        "Upload a PDF invoice and let the platform extract and validate its information."
    )

    section_heading(
        "Upload a supplier invoice",
        "Text-based and scanned PDF invoices are supported."
    )

    uploaded_file = st.file_uploader(
        "Choose an invoice PDF",
        type=["pdf"],
        help="Maximum file size: 10 MB. Scanned PDFs are processed using OCR."
    )

    if uploaded_file is not None:

        st.success(f"Selected file: {uploaded_file.name}")

        st.caption(
            f"File size: {uploaded_file.size / 1024:.1f} KB"
        )

        if uploaded_file.size > 10 * 1024 * 1024:

            st.error(
                "The file is too large. Maximum allowed size is 10 MB."
            )

        else:

            if st.button(
                "Process Invoice",
                type="primary",
                use_container_width=True
            ):

                temporary_path = None

                try:

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pdf"
                    ) as temporary_file:

                        temporary_file.write(
                            uploaded_file.getvalue()
                        )

                        temporary_path = Path(
                            temporary_file.name
                        )

                    with st.spinner(
                        "Extracting and validating invoice information..."
                    ):

                        result = process_invoice_pdf(
                            str(temporary_path)
                        )

                    st.markdown("---")

                    section_heading(
                        "Processing Results",
                        "Invoice extraction and validation report."
                    )

                    final_status = result.get(
                        "final_status",
                        "REQUIRES_REVIEW"
                    )

                    if final_status == "READY_FOR_APPROVAL":

                        st.success(
                            "Invoice processed successfully and saved for approval."
                        )

                    elif final_status == "DUPLICATE_FLAGGED":

                        st.warning(
                            "Duplicate invoice detected. It was not saved again."
                        )

                    else:

                        st.warning(
                            "This invoice requires manual review."
                        )

                    invoice = result.get("invoice")

                    if invoice:

                        section_heading("Extracted Invoice Details")

                        invoice_columns = st.columns(2)

                        with invoice_columns[0]:

                            render_metric_panel(
                                "SUPPLIER",
                                invoice.get("supplier") or "Not detected"
                            )

                            render_metric_panel(
                                "INVOICE NUMBER",
                                invoice.get("invoice_number") or "Not detected"
                            )

                        with invoice_columns[1]:

                            render_metric_panel(
                                "INVOICE DATE",
                                invoice.get("invoice_date") or "Not detected"
                            )

                            render_metric_panel(
                                "INVOICE TOTAL",
                                money(invoice.get("total") or 0)
                            )

                    validation = result.get("validation")

                    if validation:

                        section_heading("Validation Results")

                        if validation.get("valid"):
                            st.success("Invoice validation passed.")
                        else:
                            st.error("Invoice validation failed.")

                        errors = validation.get("errors", [])

                        for error in errors:
                            st.error(str(error))

                    duplicate = result.get("duplicate_check")

                    if duplicate:

                        section_heading("Duplicate Detection")

                        st.info(
                            duplicate.get(
                                "message",
                                duplicate.get(
                                    "status",
                                    "No details available."
                                )
                            )
                        )

                    if result.get("message"):
                        st.warning(result["message"])

                    with st.expander("View full processing report"):
                        st.json(result)

                except Exception as error:

                    st.error(
                        f"Invoice processing failed: {error}"
                    )

                finally:

                    if temporary_path and temporary_path.exists():
                        temporary_path.unlink(missing_ok=True)

    else:

        st.info(
            "Choose a PDF invoice above to begin processing."
        )

    st.markdown("---")

    section_heading(
        "How invoice processing works",
        "Four stages from supplier document to approval readiness."
    )

    workflow_columns = st.columns(4)

    workflow_steps = [
        ("01", "UPLOAD", "Select a supplier PDF invoice."),
        ("02", "EXTRACT", "Read text and scanned documents using OCR."),
        ("03", "VALIDATE", "Check invoice information and duplicates."),
        ("04", "REVIEW", "Send eligible invoices for approval.")
    ]

    for column, step in zip(workflow_columns, workflow_steps):

        with column:

            render_metric_panel(
                f"{step[0]} | {step[1]}",
                step[2]
            )


# =========================================================
# INVOICE REGISTER
# =========================================================

elif page == "Invoice Register":

    render_page_header(
        "Accounts Payable",
        "Invoice Register",
        "Search, filter and review invoices stored in the finance platform."
    )

    render_hero(
        "Every invoice. One central register.",
        "Monitor invoice records, supplier details, values and processing status."
    )

    filter_columns = st.columns([2, 1, 1])

    with filter_columns[0]:

        search_term = st.text_input(
            "Search invoices",
            placeholder="Search by supplier or invoice number..."
        )

    with filter_columns[1]:

        status_options = [
            "All",
            "READY_FOR_APPROVAL",
            "APPROVED",
            "REJECTED",
            "DUPLICATE_FLAGGED",
            "REQUIRES_REVIEW"
        ]

        selected_status = st.selectbox(
            "Processing status",
            status_options
        )

    with filter_columns[2]:

        payment_status_options = [
            "All",
            "UNPAID",
            "PARTIALLY_PAID",
            "PAID"
        ]

        selected_payment_status = st.selectbox(
            "Payment status",
            payment_status_options
        )

    if search_term.strip():

        invoices = search_invoices(search_term.strip())

        invoice_df = (
            pd.DataFrame(invoices)
            if invoices
            else pd.DataFrame()
        )

    elif selected_status != "All":

        invoices = filter_invoices(selected_status)

        invoice_df = (
            pd.DataFrame(invoices)
            if invoices
            else pd.DataFrame()
        )

    else:

        invoice_df = load_invoice_data()

    if (
        not invoice_df.empty
        and search_term.strip()
        and selected_status != "All"
        and "processing_status" in invoice_df.columns
    ):

        invoice_df = invoice_df[
            invoice_df["processing_status"] == selected_status
        ]

    if not invoice_df.empty:
        invoice_df = add_payment_details(invoice_df)

        if (
            selected_payment_status != "All"
            and "payment_status" in invoice_df.columns
        ):
            invoice_df = invoice_df[
                invoice_df["payment_status"] == selected_payment_status
            ]

    section_heading(
        "Invoice Records",
        "Processing status and payment status are tracked separately. Payment amounts are calculated from recorded payment transactions."
    )

    if not invoice_df.empty:

        summary_columns = st.columns(3)

        with summary_columns[0]:
            render_metric_panel(
                "INVOICES FOUND",
                f"{len(invoice_df):,}"
            )

        with summary_columns[1]:

            invoice_total = pd.to_numeric(
                invoice_df.get("total", pd.Series(dtype=float)),
                errors="coerce"
            ).sum()

            render_metric_panel(
                "TOTAL VALUE",
                compact_money(invoice_total)
            )

        with summary_columns[2]:

            unique_suppliers = (
                invoice_df["supplier"].nunique()
                if "supplier" in invoice_df.columns
                else 0
            )

            render_metric_panel(
                "SUPPLIERS",
                f"{unique_suppliers:,}"
            )

        st.markdown("")

        show_dataframe(invoice_df)

        csv_data = invoice_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download invoice register CSV",
            data=csv_data,
            file_name="finance_invoice_register.csv",
            mime="text/csv"
        )

    else:

        st.info("No matching invoices found.")


# =========================================================
# RECORD PAYMENT
# =========================================================

elif page == "Record Payment":

    render_page_header(
        "Accounts Payable",
        "Record Payment",
        "Record supplier invoice payments and keep outstanding balances up to date."
    )

    render_hero(
        "Keep every payment accountable.",
        "Select an approved invoice, confirm its outstanding balance and record the payment transaction."
    )

    invoices_df = load_invoice_data()

    if invoices_df.empty:
        st.info("There are no invoices available to review yet.")

    elif "processing_status" not in invoices_df.columns or "id" not in invoices_df.columns:
        st.error("The invoice records are missing the fields required to record a payment.")

    else:
        approved_invoices = invoices_df[
            invoices_df["processing_status"].astype(str).str.upper() == "APPROVED"
        ].copy()

        if approved_invoices.empty:
            st.info("There are no approved invoices available for payment.")

        else:
            approved_invoices["id"] = pd.to_numeric(
                approved_invoices["id"], errors="coerce"
            )
            approved_invoices = approved_invoices.dropna(subset=["id"])
            approved_invoices["id"] = approved_invoices["id"].astype(int)

            invoice_labels = {}
            for _, invoice_row in approved_invoices.iterrows():
                invoice_id = int(invoice_row["id"])
                supplier_name = str(invoice_row.get("supplier", "Unknown supplier"))
                invoice_number = str(invoice_row.get("invoice_number", "No invoice number"))
                invoice_total = money(invoice_row.get("total", 0))
                invoice_labels[invoice_id] = (
                    f"{invoice_number} | {supplier_name} | {invoice_total}"
                )

            selected_invoice_id = st.selectbox(
                "Select approved invoice",
                options=list(invoice_labels.keys()),
                format_func=lambda invoice_id: invoice_labels[invoice_id],
                key="payment_invoice_selector"
            )

            payment_summary = get_payment_summary(int(selected_invoice_id))

            if payment_summary is None:
                st.error("Payment information could not be retrieved for this invoice.")

            else:
                invoice_total = float(payment_summary.get("invoice_total", 0) or 0)
                amount_paid = float(payment_summary.get("amount_paid", 0) or 0)
                outstanding_balance = float(
                    payment_summary.get("outstanding_balance", 0) or 0
                )
                current_payment_status = payment_summary.get(
                    "payment_status", "UNAVAILABLE"
                )

                st.markdown("### Selected invoice payment position")
                payment_metrics = st.columns(3)

                with payment_metrics[0]:
                    render_metric_panel("INVOICE TOTAL", money(invoice_total))

                with payment_metrics[1]:
                    render_metric_panel("AMOUNT PAID", money(amount_paid))

                with payment_metrics[2]:
                    render_metric_panel(
                        "OUTSTANDING BALANCE", money(outstanding_balance)
                    )

                st.caption(f"Current payment status: {current_payment_status}")

                if outstanding_balance <= 0:
                    st.success("This invoice is fully paid. No further payment is due.")

                else:
                    st.markdown("### Payment details")

                    with st.form("record_invoice_payment_form"):
                        payment_amount = st.number_input(
                            "Payment amount",
                            min_value=0.01,
                            max_value=float(outstanding_balance),
                            value=float(min(outstanding_balance, 1000.0)),
                            step=100.0,
                            format="%.2f",
                            help="The amount cannot exceed the invoice's outstanding balance."
                        )

                        payment_reference = st.text_input(
                            "Payment reference",
                            placeholder="e.g. M-PESA code, bank reference or transaction ID"
                        )

                        recorded_by = st.text_input(
                            "Recorded by",
                            placeholder="Enter the finance officer's name"
                        )

                        payment_submitted = st.form_submit_button(
                            "Record Payment",
                            use_container_width=True
                        )

                    if payment_submitted:
                        if not payment_reference.strip():
                            st.error("Enter a payment reference before submitting.")
                        elif not recorded_by.strip():
                            st.error("Enter the name of the person recording this payment.")
                        else:
                            try:
                                payment_result = record_payment(
                                    int(selected_invoice_id),
                                    payment_amount,
                                    payment_reference.strip(),
                                    recorded_by.strip()
                                )

                                result_failed = False
                                result_message = "Payment recorded successfully."

                                if isinstance(payment_result, dict):
                                    result_status = str(
                                        payment_result.get("status", "")
                                    ).upper()
                                    result_failed = (
                                        payment_result.get("success") is False
                                        or bool(payment_result.get("error"))
                                        or bool(payment_result.get("errors"))
                                        or result_status in {"ERROR", "FAILED", "REJECTED"}
                                    )
                                    result_message = (
                                        payment_result.get("message")
                                        or payment_result.get("error")
                                        or result_message
                                    )

                                if result_failed:
                                    st.error(str(result_message))
                                else:
                                    st.success(str(result_message))
                                    updated_summary = get_payment_summary(
                                        int(selected_invoice_id)
                                    )

                                    if updated_summary:
                                        updated_columns = st.columns(3)
                                        with updated_columns[0]:
                                            render_metric_panel(
                                                "UPDATED AMOUNT PAID",
                                                money(updated_summary.get("amount_paid", 0))
                                            )
                                        with updated_columns[1]:
                                            render_metric_panel(
                                                "NEW OUTSTANDING BALANCE",
                                                money(updated_summary.get("outstanding_balance", 0))
                                            )
                                        with updated_columns[2]:
                                            render_metric_panel(
                                                "UPDATED PAYMENT STATUS",
                                                str(updated_summary.get("payment_status", "UNAVAILABLE"))
                                            )

                            except Exception as payment_error:
                                st.error(f"Payment could not be recorded: {payment_error}")


# =========================================================
# PAYMENT HISTORY
# =========================================================

elif page == "Payment History":

    render_page_header(
        "Accounts Payable",
        "Payment History",
        "Review, search and export every payment recorded in FinSight."
    )

    render_hero(
        "A complete record of supplier payments.",
        "Track payment references, invoice details, transaction amounts, recording officers and timestamps."
    )

    try:
        with get_connection() as conn:
            payment_cursor = conn.execute(
                """
                SELECT
                    p.id AS payment_id,
                    p.invoice_id,
                    i.invoice_number,
                    i.supplier,
                    p.amount,
                    p.payment_reference,
                    p.recorded_by,
                    p.created_at
                FROM invoice_payments AS p
                LEFT JOIN invoices AS i
                    ON i.id = p.invoice_id
                ORDER BY p.created_at DESC, p.id DESC
                """
            )
            payment_columns = [column[0] for column in payment_cursor.description]
            payment_rows = [
                dict(zip(payment_columns, row))
                for row in payment_cursor.fetchall()
            ]

        payment_history_df = pd.DataFrame(payment_rows)

        if payment_history_df.empty:
            st.info("No payment transactions have been recorded yet.")
        else:
            payment_history_df["amount"] = pd.to_numeric(
                payment_history_df["amount"], errors="coerce"
            ).fillna(0)
            payment_history_df["created_at"] = pd.to_datetime(
                payment_history_df["created_at"], errors="coerce"
            )
            payment_history_df["supplier"] = payment_history_df["supplier"].fillna(
                "Invoice record unavailable"
            )
            payment_history_df["invoice_number"] = payment_history_df[
                "invoice_number"
            ].fillna("Invoice #" + payment_history_df["invoice_id"].astype(str))

            total_payment_value = payment_history_df["amount"].sum()
            payment_count = len(payment_history_df)
            invoices_with_payments = payment_history_df["invoice_id"].nunique()

            section_heading(
                "Payment Activity Overview",
                "Summary of all payment transactions stored in the payment ledger."
            )

            payment_kpis = st.columns(3)
            with payment_kpis[0]:
                render_kpi(
                    "PAYMENT TRANSACTIONS",
                    f"{payment_count:,}",
                    "Recorded payment entries",
                    "▤"
                )
            with payment_kpis[1]:
                render_kpi(
                    "TOTAL PAYMENTS",
                    compact_money(total_payment_value),
                    "Sum of recorded transactions",
                    "✓"
                )
            with payment_kpis[2]:
                render_kpi(
                    "INVOICES WITH PAYMENTS",
                    f"{invoices_with_payments:,}",
                    "Distinct invoices paid in part or full",
                    "▣"
                )

            st.markdown("---")
            section_heading(
                "Search Payment Transactions",
                "Filter the ledger by invoice, supplier, payment reference or finance officer."
            )

            filter_columns = st.columns([1.5, 1, 1])
            with filter_columns[0]:
                payment_search = st.text_input(
                    "Search payments",
                    placeholder="Invoice, supplier, reference or officer",
                    key="payment_history_search"
                ).strip().lower()
            with filter_columns[1]:
                supplier_options = ["All suppliers"] + sorted(
                    payment_history_df["supplier"].astype(str).unique().tolist()
                )
                selected_supplier = st.selectbox(
                    "Supplier", supplier_options, key="payment_history_supplier"
                )
            with filter_columns[2]:
                officer_options = ["All officers"] + sorted(
                    payment_history_df["recorded_by"].fillna("Unknown").astype(str).unique().tolist()
                )
                selected_officer = st.selectbox(
                    "Recorded by", officer_options, key="payment_history_officer"
                )

            filtered_payments = payment_history_df.copy()

            if payment_search:
                searchable_columns = [
                    "invoice_number", "supplier", "payment_reference", "recorded_by"
                ]
                search_mask = pd.Series(False, index=filtered_payments.index)
                for search_column in searchable_columns:
                    search_mask = search_mask | filtered_payments[search_column].astype(
                        str
                    ).str.lower().str.contains(payment_search, na=False, regex=False)
                filtered_payments = filtered_payments[search_mask]

            if selected_supplier != "All suppliers":
                filtered_payments = filtered_payments[
                    filtered_payments["supplier"].astype(str) == selected_supplier
                ]

            if selected_officer != "All officers":
                filtered_payments = filtered_payments[
                    filtered_payments["recorded_by"].fillna("Unknown").astype(str)
                    == selected_officer
                ]

            display_columns = [
                "payment_id",
                "invoice_number",
                "supplier",
                "amount",
                "payment_reference",
                "recorded_by",
                "created_at"
            ]
            display_df = filtered_payments[display_columns].copy()
            display_df = display_df.rename(columns={
                "payment_id": "Payment ID",
                "invoice_number": "Invoice Number",
                "supplier": "Supplier",
                "amount": "Payment Amount",
                "payment_reference": "Payment Reference",
                "recorded_by": "Recorded By",
                "created_at": "Date Recorded"
            })
            display_df["Payment Amount"] = display_df["Payment Amount"].map(money)
            display_df["Date Recorded"] = display_df["Date Recorded"].dt.strftime(
                "%d %b %Y, %H:%M"
            ).fillna("Date unavailable")

            st.caption(
                f"Showing {len(filtered_payments):,} of {payment_count:,} payment transactions."
            )

            if filtered_payments.empty:
                st.warning("No payment transactions match the selected filters.")
            else:
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

                export_df = filtered_payments[display_columns].copy()
                export_df["created_at"] = export_df["created_at"].astype(str)
                csv_data = export_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download payment history CSV",
                    data=csv_data,
                    file_name="finsight_payment_history.csv",
                    mime="text/csv",
                    use_container_width=False
                )

    except Exception as payment_history_error:
        st.error(
            "Payment history could not be loaded. "
            f"Check the payment ledger and database connection. Details: {payment_history_error}"
        )



# =========================================================
# PAYMENT RECONCILIATION
# =========================================================

elif page == "Payment Reconciliation":

    render_page_header(
        "Financial Controls",
        "Payment Reconciliation",
        "Compare invoice values with recorded payment transactions and identify outstanding balances."
    )

    render_hero(
        "Know exactly where every invoice stands.",
        "Reconcile invoice totals against the payment ledger. This report is read-only and does not alter financial records."
    )

    try:
        reconciliation_records = reconcile_payments()
        reconciliation_summary = get_reconciliation_summary()

        if not reconciliation_records:
            st.info("No invoice records are available for reconciliation.")
        else:
            section_heading(
                "Reconciliation Overview",
                "Payment positions calculated from invoice totals and recorded payment transactions."
            )

            status_columns = st.columns(4)
            status_kpis = [
                ("TOTAL INVOICES", reconciliation_summary["total_invoices"], "Invoices reviewed", "▤"),
                ("FULLY PAID", reconciliation_summary["paid"], "No balance remaining", "✓"),
                ("PARTIALLY PAID", reconciliation_summary["partially_paid"], "Payment still outstanding", "◷"),
                ("UNPAID", reconciliation_summary["unpaid"], "No payments recorded", "!")
            ]

            for column, item in zip(status_columns, status_kpis):
                with column:
                    render_kpi(*item)

            financial_columns = st.columns(3)
            with financial_columns[0]:
                render_metric_panel(
                    "TOTAL INVOICED",
                    compact_money(reconciliation_summary["total_invoiced"])
                )
            with financial_columns[1]:
                render_metric_panel(
                    "TOTAL PAID",
                    compact_money(reconciliation_summary["total_paid"])
                )
            with financial_columns[2]:
                render_metric_panel(
                    "NET OUTSTANDING",
                    compact_money(reconciliation_summary["total_outstanding"])
                )

            if reconciliation_summary["overpaid"] > 0:
                st.warning(
                    f'{reconciliation_summary["overpaid"]} invoice(s) have recorded payments '
                    "greater than their invoice totals. Review these transactions."
                )
            else:
                st.success("No overpaid invoices were detected.")

            st.markdown("---")
            section_heading(
                "Invoice Reconciliation Records",
                "Filter the results, inspect individual invoice balances and export the reconciliation report."
            )

            reconciliation_df = pd.DataFrame(reconciliation_records)

            filter_columns = st.columns([1, 1.5, 1])
            with filter_columns[0]:
                reconciliation_status_options = [
                    "All",
                    "PAID",
                    "PARTIALLY_PAID",
                    "UNPAID",
                    "OVERPAID"
                ]
                selected_reconciliation_status = st.selectbox(
                    "Payment position",
                    reconciliation_status_options,
                    key="reconciliation_status_filter"
                )

            with filter_columns[1]:
                reconciliation_search = st.text_input(
                    "Search invoices",
                    placeholder="Supplier or invoice number",
                    key="reconciliation_search"
                ).strip().lower()

            with filter_columns[2]:
                processing_status_options = ["All"] + sorted(
                    reconciliation_df["processing_status"].fillna("UNKNOWN").astype(str).unique().tolist()
                )
                selected_processing_status = st.selectbox(
                    "Invoice workflow status",
                    processing_status_options,
                    key="reconciliation_processing_filter"
                )

            filtered_reconciliation = reconciliation_df.copy()

            if selected_reconciliation_status != "All":
                filtered_reconciliation = filtered_reconciliation[
                    filtered_reconciliation["reconciliation_status"]
                    == selected_reconciliation_status
                ]

            if reconciliation_search:
                search_mask = (
                    filtered_reconciliation["supplier"].astype(str).str.lower().str.contains(
                        reconciliation_search, na=False, regex=False
                    )
                    |
                    filtered_reconciliation["invoice_number"].astype(str).str.lower().str.contains(
                        reconciliation_search, na=False, regex=False
                    )
                )
                filtered_reconciliation = filtered_reconciliation[search_mask]

            if selected_processing_status != "All":
                filtered_reconciliation = filtered_reconciliation[
                    filtered_reconciliation["processing_status"].fillna("UNKNOWN").astype(str)
                    == selected_processing_status
                ]

            st.caption(
                f"Showing {len(filtered_reconciliation):,} of "
                f"{len(reconciliation_df):,} invoices."
            )

            display_columns = [
                "invoice_id",
                "supplier",
                "invoice_number",
                "invoice_total",
                "amount_paid",
                "outstanding_balance",
                "payment_count",
                "processing_status",
                "reconciliation_status"
            ]

            display_df = filtered_reconciliation[display_columns].copy()
            display_df = display_df.rename(columns={
                "invoice_id": "Invoice ID",
                "supplier": "Supplier",
                "invoice_number": "Invoice Number",
                "invoice_total": "Invoice Total",
                "amount_paid": "Amount Paid",
                "outstanding_balance": "Outstanding Balance",
                "payment_count": "Payment Count",
                "processing_status": "Approval Status",
                "reconciliation_status": "Reconciliation Status"
            })

            for column in ["Invoice Total", "Amount Paid", "Outstanding Balance"]:
                display_df[column] = display_df[column].map(money)

            if filtered_reconciliation.empty:
                st.warning("No invoices match the selected filters.")
            else:
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

                export_df = filtered_reconciliation.copy()
                csv_data = export_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download reconciliation report CSV",
                    data=csv_data,
                    file_name="finsight_payment_reconciliation.csv",
                    mime="text/csv",
                    use_container_width=False
                )

            st.caption(
                "Reconciliation status is calculated from recorded payments. "
                "It is separate from invoice approval status. An unpaid invoice is not "
                "necessarily overdue; due dates are not currently included in this report."
            )

    except Exception as reconciliation_error:
        st.error(
            "Payment reconciliation could not be loaded. "
            f"Details: {reconciliation_error}"
        )



# =========================================================
# SUPPLIER ANALYTICS
# =========================================================

elif page == "Supplier Analytics":

    render_page_header(
        "Vendor Intelligence",
        "Supplier Analytics",
        "Understand supplier spending, payment activity and outstanding balances."
    )

    render_hero(
        "Understand your supplier relationships.",
        "Review spending concentration, payment exposure and supplier financial activity."
    )

    supplier_data = get_supplier_analytics()

    if supplier_data:

        supplier_df = pd.DataFrame(supplier_data)

        numeric_columns = [
            "total_invoiced",
            "total_paid",
            "outstanding",
            "invoice_count"
        ]

        for column in numeric_columns:

            if column in supplier_df.columns:

                supplier_df[column] = pd.to_numeric(
                    supplier_df[column],
                    errors="coerce"
                ).fillna(0)

        total_supplier_invoiced = (
            supplier_df["total_invoiced"].sum()
            if "total_invoiced" in supplier_df.columns
            else 0
        )

        total_supplier_paid = (
            supplier_df["total_paid"].sum()
            if "total_paid" in supplier_df.columns
            else 0
        )

        total_supplier_outstanding = (
            supplier_df["outstanding"].sum()
            if "outstanding" in supplier_df.columns
            else 0
        )

        section_heading(
            "Supplier Financial Overview",
            "Aggregated supplier financial indicators."
        )

        supplier_columns = st.columns(3)

        with supplier_columns[0]:

            render_kpi(
                "TOTAL SUPPLIER SPENDING",
                compact_money(total_supplier_invoiced),
                "Recorded invoice value",
                "↗"
            )

        with supplier_columns[1]:

            render_kpi(
                "TOTAL SUPPLIER PAYMENTS",
                compact_money(total_supplier_paid),
                "Payments recorded",
                "✓"
            )

        with supplier_columns[2]:

            render_kpi(
                "SUPPLIER OUTSTANDING",
                compact_money(total_supplier_outstanding),
                "Unpaid supplier balances",
                "◷"
            )

        st.markdown("---")

        chart_columns = st.columns([1.2, 1])

        with chart_columns[0]:

            st.markdown("**Supplier spending comparison**")

            if "total_invoiced" in supplier_df.columns:

                spending_data = (
                    supplier_df
                    .set_index("supplier")["total_invoiced"]
                    .sort_values(ascending=False)
                )

                st.bar_chart(
                    spending_data,
                    use_container_width=True,
                    height=320
                )

        with chart_columns[1]:

            st.markdown("**Supplier payment exposure**")

            if "outstanding" in supplier_df.columns:

                outstanding_data = (
                    supplier_df
                    .set_index("supplier")["outstanding"]
                    .sort_values(ascending=False)
                )

                st.bar_chart(
                    outstanding_data,
                    use_container_width=True,
                    height=320
                )

        st.markdown("---")

        section_heading(
            "Supplier Records",
            "Detailed supplier invoice and payment information."
        )

        show_dataframe(supplier_df)

    else:

        st.info("No supplier analytics are available yet.")


# =========================================================
# APPROVAL AUDIT
# =========================================================

elif page == "Approval Audit":

    render_page_header(
        "Financial Controls",
        "Approval Audit Trail",
        "Review recorded invoice approval and rejection activities."
    )

    render_hero(
        "A clear record of financial decisions.",
        "Monitor approval actions and maintain visibility into invoice review activity."
    )

    audit_data = get_approval_history()

    if audit_data:

        audit_df = pd.DataFrame(audit_data)

        section_heading(
            "Approval Activity",
            "Recorded approval and rejection events."
        )

        summary_columns = st.columns(2)

        with summary_columns[0]:

            render_kpi(
                "AUDIT RECORDS",
                f"{len(audit_df):,}",
                "Recorded actions",
                "▤"
            )

        with summary_columns[1]:

            if "action" in audit_df.columns:

                action_count = audit_df["action"].nunique()

            else:

                action_count = 0

            render_kpi(
                "ACTION TYPES",
                f"{action_count:,}",
                "Distinct recorded actions",
                "✓"
            )

        st.markdown("---")

        show_dataframe(audit_df)

        csv_data = audit_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download approval audit CSV",
            data=csv_data,
            file_name="approval_audit.csv",
            mime="text/csv"
        )

    else:

        st.info(
            "No approval audit records are available yet."
        )


# =========================================================
# ANOMALY MONITORING
# =========================================================

elif page == "Anomaly Monitoring":

    render_page_header(
        "Risk Monitoring",
        "Anomaly Monitoring",
        "Identify unusual invoice patterns that may require finance team review."
    )

    render_hero(
        "Find unusual patterns before they become problems.",
        "Monitor high-value invoices and other unusual transaction patterns."
    )

    st.warning(
        "Anomaly indicators are review signals, not proof of fraud or misconduct."
    )

    if st.button(
        "Run Anomaly Detection",
        type="primary"
    ):

        from app.anomaly_detector import detect_invoice_anomalies

        with st.spinner("Analyzing invoice records..."):

            detected = detect_invoice_anomalies()

        st.success(
            f"Analysis completed. {len(detected)} findings returned."
        )

        st.rerun()

    anomaly_data = get_all_anomalies()

    if anomaly_data:

        anomaly_df = pd.DataFrame(anomaly_data)

        section_heading(
            "Recorded Anomalies",
            "Findings that may require manual review."
        )

        render_kpi(
            "RECORDED ANOMALIES",
            f"{len(anomaly_df):,}",
            "Stored anomaly findings",
            "!"
        )

        st.markdown("")

        show_dataframe(anomaly_df)

    else:

        st.success(
            "No recorded anomalies found."
        )


# =========================================================
# FINANCE ASSISTANT
# =========================================================

elif page == "Finance Assistant":

    render_page_header(
        "Financial Intelligence",
        "Finance Assistant",
        "Ask questions about invoices, supplier balances, payments and financial activity."
    )

    render_hero(
        "Ask questions. Get financial answers.",
        "Use the platform's stored financial records to answer operational finance questions."
    )

    section_heading(
        "Example questions",
        "Try one of these questions or enter your own."
    )

    examples = [
        "What is our total outstanding balance?",
        "How much have we paid?",
        "Which suppliers have outstanding balances?",
        "Show me flagged anomalies.",
        "How many invoices are pending approval?"
    ]

    example_columns = st.columns(2)

    for index, example in enumerate(examples):

        with example_columns[index % 2]:

            if st.button(
                example,
                key=f"example_question_{index}",
                use_container_width=True
            ):

                st.session_state["finance_question"] = example

    st.markdown("---")

    question = st.text_input(
        "Ask a finance question",
        key="finance_question",
        placeholder="For example: What is our total outstanding balance?"
    )

    if st.button(
        "Ask Finance Assistant",
        type="primary",
        use_container_width=True
    ):

        if question.strip():

            with st.spinner(
                "Analyzing financial records..."
            ):

                response = answer_question(
                    question.strip()
                )

            section_heading("Assistant Response")

            st.markdown(
                '<div class="content-panel">',
                unsafe_allow_html=True
            )

            if isinstance(response, (dict, list)):

                st.json(response)

            else:

                st.write(response)

            st.markdown("</div>", unsafe_allow_html=True)

        else:

            st.warning(
                "Please enter a question first."
            )

    st.markdown("---")

    st.caption(
        "Responses are generated from the platform's stored financial records. "
        "Verify important financial decisions against the underlying records."
    )
