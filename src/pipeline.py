"""Reconcile sources, detect controls and anomalies, and create curated outputs."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[1]
DATA, OUTPUTS = ROOT / "data", ROOT / "outputs"


def _risk(issue_types: list[str], amount_eur: float, anomaly: bool) -> tuple[str, int]:
    score = 0
    score += sum({"Missing bank settlement": 55, "Missing ledger posting": 45, "Amount mismatch": 45,
                  "Duplicate bank record": 50, "Settlement delay": 25, "Missing regulatory classification": 20}.get(x, 0) for x in issue_types)
    score += 20 if amount_eur >= 1000 else 8 if amount_eur >= 500 else 0
    score += 15 if anomaly else 0
    return ("High" if score >= 55 else "Medium" if score >= 25 else "Low"), min(score, 100)


def run() -> dict[str, pd.DataFrame]:
    OUTPUTS.mkdir(exist_ok=True)
    tx = pd.read_csv(DATA / "transactions.csv", parse_dates=["transaction_date", "settlement_date"])
    bank = pd.read_csv(DATA / "bank_statement.csv", parse_dates=["bank_settlement_date"])
    ledger = pd.read_csv(DATA / "general_ledger.csv", parse_dates=["posting_date"])
    fx = pd.read_csv(DATA / "fx_rates.csv")

    bank_count = bank.groupby("transaction_id").size().rename("bank_record_count")
    bank_unique = bank.drop_duplicates("transaction_id")
    ledger_unique = ledger.drop_duplicates("transaction_id")
    df = tx.merge(bank_unique[["transaction_id", "bank_amount", "bank_settlement_date"]], on="transaction_id", how="left") \
           .merge(ledger_unique[["transaction_id", "ledger_amount", "posting_date"]], on="transaction_id", how="left") \
           .merge(bank_count, on="transaction_id", how="left").merge(fx[["currency", "eur_rate"]], on="currency", how="left")
    df["bank_record_count"] = df["bank_record_count"].fillna(0).astype(int)
    df["amount_eur"] = (df.amount * df.eur_rate).round(2)
    df["bank_difference"] = (df.bank_amount - df.amount).round(2)
    df["ledger_difference"] = (df.ledger_amount - df.amount).round(2)
    df["settlement_days"] = (df.bank_settlement_date - df.transaction_date).dt.days
    features = df[["amount_eur"]].fillna(0).assign(settlement_days=df.settlement_days.fillna(5), provider=df.payment_provider.map({"P-01": 1, "P-02": 2, "P-03": 3}))
    model = IsolationForest(contamination=0.06, random_state=42)
    df["anomaly_score"] = (-model.fit(features).score_samples(features) * 100).round(1)
    df["is_anomaly"] = model.predict(features) == -1

    exceptions = []
    for _, r in df.iterrows():
        issues = []
        if pd.isna(r.bank_amount): issues.append("Missing bank settlement")
        if pd.isna(r.ledger_amount): issues.append("Missing ledger posting")
        if not pd.isna(r.bank_difference) and abs(r.bank_difference) > 0.01: issues.append("Amount mismatch")
        if not pd.isna(r.ledger_difference) and abs(r.ledger_difference) > 0.01 and "Amount mismatch" not in issues: issues.append("Amount mismatch")
        if r.bank_record_count > 1: issues.append("Duplicate bank record")
        if not pd.isna(r.settlement_days) and r.settlement_days > 2: issues.append("Settlement delay")
        if pd.isna(r.regulatory_classification) or not str(r.regulatory_classification).strip(): issues.append("Missing regulatory classification")
        if issues or r.is_anomaly:
            if r.is_anomaly and not issues: issues.append("Unusual transaction pattern")
            level, score = _risk(issues, r.amount_eur, r.is_anomaly)
            primary = issues[0]
            action = {"Missing bank settlement": "Check bank file ingestion and settlement batch.", "Missing ledger posting": "Review journal interface and posting queue.", "Amount mismatch": "Validate source amount, FX rate, and adjustment entries.", "Duplicate bank record": "Confirm reversal or duplicate bank-file ingestion.", "Settlement delay": "Check provider settlement status and cut-off timing.", "Missing regulatory classification": "Complete classification before regulatory reporting."}.get(primary, "Review the transaction pattern and supporting evidence.")
            exceptions.append({"exception_id": f"EX-{len(exceptions)+1001}", "transaction_id": r.transaction_id, "detected_date": "2026-07-24", "exception_type": primary, "all_issues": "; ".join(issues), "risk_level": level, "risk_score": score, "status": "Open" if level == "High" else "In review", "amount_eur": r.amount_eur, "payment_provider": r.payment_provider, "currency": r.currency, "transaction_date": r.transaction_date.date(), "recommended_action": action, "audit_note": f"Automated control detected {primary.lower()}. No manual override applied.", "anomaly_score": r.anomaly_score})
    ex = pd.DataFrame(exceptions).sort_values(["risk_score", "amount_eur"], ascending=False)
    reconciled = df.assign(reconciliation_status=df.apply(lambda r: "Unmatched" if pd.isna(r.bank_amount) or pd.isna(r.ledger_amount) else "Mismatch" if abs(r.bank_difference or 0) > .01 or abs(r.ledger_difference or 0) > .01 else "Matched", axis=1))
    summary = reconciled.groupby("reconciliation_status").agg(transactions=("transaction_id", "count"), value_eur=("amount_eur", "sum")).reset_index()
    controls = ex.groupby(["exception_type", "risk_level"]).agg(exceptions=("exception_id", "count"), value_at_risk_eur=("amount_eur", "sum")).reset_index()
    ex.to_csv(OUTPUTS / "exceptions.csv", index=False)
    reconciled.to_csv(OUTPUTS / "reconciled_transactions.csv", index=False)
    summary.to_csv(OUTPUTS / "reconciliation_summary.csv", index=False)
    controls.to_csv(OUTPUTS / "control_summary.csv", index=False)
    return {"exceptions": ex, "transactions": reconciled, "summary": summary, "controls": controls}


if __name__ == "__main__":
    results = run()
    print(f"Created {len(results['exceptions'])} exceptions in {OUTPUTS}")
