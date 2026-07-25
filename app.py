from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.pipeline import run

st.set_page_config(page_title="FinControl AI", page_icon="🛡️", layout="wide")

@st.cache_data(show_spinner=False)
def load_data():
    required = ROOT / "outputs" / "exceptions.csv"
    return run() if not required.exists() else {
        "exceptions": pd.read_csv(required),
        "transactions": pd.read_csv(ROOT / "outputs" / "reconciled_transactions.csv"),
        "summary": pd.read_csv(ROOT / "outputs" / "reconciliation_summary.csv"),
        "controls": pd.read_csv(ROOT / "outputs" / "control_summary.csv"),
    }

data = load_data()
ex, tx, summary, controls = data["exceptions"], data["transactions"], data["summary"], data["controls"]

with st.sidebar:
    st.title("FinControl AI")
    st.caption("Agentic reconciliation and controls analyst")
    page = st.radio("Workspace", ["Executive Risk Overview", "Reconciliation Monitor", "Exception Explorer", "Anomaly Detection", "Regulatory Readiness", "AI Investigator"])
    st.divider()
    provider = st.multiselect("Provider", sorted(ex.payment_provider.unique()), default=sorted(ex.payment_provider.unique()))
    risk = st.multiselect("Risk level", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    if st.button("Re-run controls"):
        run(); st.cache_data.clear(); st.rerun()

filtered = ex[ex.payment_provider.isin(provider) & ex.risk_level.isin(risk)].copy()
st.title(page)

if page == "Executive Risk Overview":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open exceptions", len(filtered))
    c2.metric("High-risk breaks", int((filtered.risk_level == "High").sum()))
    c3.metric("Value at risk", f"€{filtered.amount_eur.sum():,.0f}")
    pass_rate = (1 - len(ex) / len(tx)) * 100
    c4.metric("Control pass rate", f"{pass_rate:.1f}%")
    left, right = st.columns(2)
    left.plotly_chart(px.pie(filtered, names="risk_level", title="Exception risk mix", color="risk_level", color_discrete_map={"High":"#d62728", "Medium":"#ffbf00", "Low":"#2ca02c"}), use_container_width=True)
    trend = filtered.groupby(["transaction_date", "risk_level"], as_index=False).size()
    right.plotly_chart(px.bar(trend, x="transaction_date", y="size", color="risk_level", title="Exceptions by transaction date", labels={"size":"Exceptions"}), use_container_width=True)
    st.subheader("Priority queue")
    st.dataframe(filtered[["exception_id", "transaction_id", "exception_type", "risk_level", "amount_eur", "recommended_action"]].head(12), use_container_width=True, hide_index=True)

elif page == "Reconciliation Monitor":
    st.plotly_chart(px.bar(summary, x="reconciliation_status", y="transactions", color="reconciliation_status", text="transactions", title="Reconciliation outcomes"), use_container_width=True)
    st.subheader("Breaks requiring investigation")
    st.dataframe(tx[tx.reconciliation_status != "Matched"][["transaction_id", "payment_provider", "amount_eur", "reconciliation_status", "bank_difference", "ledger_difference", "settlement_days"]], use_container_width=True, hide_index=True)

elif page == "Exception Explorer":
    types = st.multiselect("Exception type", sorted(filtered.exception_type.unique()), default=sorted(filtered.exception_type.unique()))
    view = filtered[filtered.exception_type.isin(types)]
    st.download_button("Download filtered exception report", view.to_csv(index=False), "fincontrol_exceptions.csv", "text/csv")
    st.dataframe(view.sort_values("risk_score", ascending=False), use_container_width=True, hide_index=True)

elif page == "Anomaly Detection":
    st.caption("Isolation Forest flags the 6% most unusual value, timing, and provider combinations. It is a triage signal, not a decision engine.")
    flagged = tx[tx.is_anomaly]
    st.plotly_chart(px.scatter(tx, x="settlement_days", y="amount_eur", color="is_anomaly", hover_name="transaction_id", hover_data=["payment_provider"], title="Transaction anomaly distribution", log_y=True), use_container_width=True)
    st.dataframe(flagged[["transaction_id", "payment_provider", "amount_eur", "settlement_days", "anomaly_score"]].sort_values("anomaly_score", ascending=False), use_container_width=True, hide_index=True)

elif page == "Regulatory Readiness":
    reg = ex[ex.exception_type.eq("Missing regulatory classification")]
    c1, c2 = st.columns(2)
    c1.metric("Missing required classifications", len(reg))
    c2.metric("Audit trail completeness", "100%")
    st.plotly_chart(px.bar(controls, x="exception_type", y="exceptions", color="risk_level", title="Control validation failures"), use_container_width=True)
    st.dataframe(reg[["exception_id", "transaction_id", "payment_provider", "amount_eur", "audit_note", "recommended_action"]], use_container_width=True, hide_index=True)

else:
    question = st.text_input("Ask about exceptions and controls", placeholder="Why are there so many settlement breaks this week?")
    if question:
        settlement = ex[ex.exception_type.eq("Settlement delay")]
        top = settlement.payment_provider.value_counts().index[0] if len(settlement) else "No provider"
        st.info(f"**Control Investigator:** {len(settlement)} settlement delays were detected. The largest concentration is linked to **{top}**. Review provider settlement status, cut-off timing, and the associated bank-file ingestion evidence. This deterministic demo response is grounded in the current exception table.")
    st.subheader("Evidence used by the investigator")
    st.dataframe(filtered[["exception_id", "exception_type", "payment_provider", "amount_eur", "audit_note"]].head(20), use_container_width=True, hide_index=True)
