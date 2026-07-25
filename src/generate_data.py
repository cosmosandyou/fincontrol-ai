"""Create deterministic, synthetic source-system data for FinControl AI."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import random

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RNG = random.Random(20260724)


def _transaction_rows(n: int = 650) -> pd.DataFrame:
    providers = ["P-01", "P-02", "P-03"]
    currencies = ["EUR", "GBP", "USD"]
    rows = []
    for i in range(n):
        booked = date(2026, 7, 1) + timedelta(days=RNG.randrange(23))
        currency = RNG.choices(currencies, weights=[0.68, 0.18, 0.14])[0]
        amount = round(RNG.lognormvariate(5.55, 0.7), 2)
        rows.append({
            "transaction_id": f"TX-{100000 + i}",
            "customer_id": f"C-{RNG.randrange(1001, 1121)}",
            "payment_provider": RNG.choices(providers, weights=[0.42, 0.33, 0.25])[0],
            "transaction_date": booked.isoformat(),
            "settlement_date": (booked + timedelta(days=RNG.choice([1, 1, 2, 2]))).isoformat(),
            "amount": amount,
            "currency": currency,
            "transaction_type": RNG.choice(["Card payment", "Transfer", "Refund"]),
            "regulatory_classification": RNG.choice(["PSD2", "EMIR", "Consumer", "Operational"]),
        })
    return pd.DataFrame(rows)


def build() -> None:
    DATA.mkdir(exist_ok=True)
    tx = _transaction_rows()
    customers = pd.DataFrame({
        "customer_id": [f"C-{i}" for i in range(1001, 1121)],
        "customer_segment": [RNG.choice(["Retail", "SME", "Enterprise"]) for _ in range(120)],
        "kyc_status": [RNG.choices(["Complete", "Pending"], [0.94, 0.06])[0] for _ in range(120)],
        "country": [RNG.choice(["Ireland", "United Kingdom", "Germany", "France"]) for _ in range(120)],
    })
    # Intentional breaks give every dashboard page meaningful scenarios.
    tx.loc[[18, 79, 238, 411], "regulatory_classification"] = ""
    tx.to_csv(DATA / "transactions.csv", index=False)
    customers.to_csv(DATA / "customer_accounts.csv", index=False)

    fx = pd.DataFrame({"currency": ["EUR", "GBP", "USD"], "eur_rate": [1.0, 1.18, 0.92], "rate_date": "2026-07-23"})
    fx.to_csv(DATA / "fx_rates.csv", index=False)

    bank = tx.copy()
    bank["bank_reference"] = [f"BNK-{i:06}" for i in range(len(bank))]
    bank["bank_amount"] = bank["amount"]
    bank["bank_settlement_date"] = bank["settlement_date"]
    # Missing settlement, amount mismatch, delayed settlement and a duplicate bank entry.
    bank = bank.drop(index=[12, 55, 101, 330, 501])
    bank.loc[bank.index.isin([34, 142, 275, 598]), "bank_amount"] += [15.25, -22.0, 110.0, -8.75]
    bank.loc[bank.index.isin([88, 189, 465]), "bank_settlement_date"] = "2026-07-28"
    bank = pd.concat([bank, bank.loc[[210]].assign(bank_reference="BNK-DUP-210")], ignore_index=True)
    bank[["transaction_id", "bank_reference", "bank_amount", "currency", "bank_settlement_date"]].to_csv(DATA / "bank_statement.csv", index=False)

    ledger = tx.copy()
    ledger["ledger_entry_id"] = [f"GL-{i:06}" for i in range(len(ledger))]
    ledger["ledger_amount"] = ledger["amount"]
    ledger["posting_date"] = ledger["settlement_date"]
    ledger = ledger.drop(index=[21, 312, 590])
    ledger.loc[ledger.index.isin([67, 366]), "ledger_amount"] += [44.5, -31.0]
    ledger.loc[ledger.index.isin([123, 444]), "posting_date"] = "2026-07-29"
    ledger[["transaction_id", "ledger_entry_id", "ledger_amount", "currency", "posting_date"]].to_csv(DATA / "general_ledger.csv", index=False)

    pd.DataFrame([
        ["R-01", "Missing bank settlement", "High", "Bank record absent after T+2"],
        ["R-02", "Amount mismatch", "High", "Bank or ledger amount differs by more than EUR 0.01"],
        ["R-03", "Settlement delay", "Medium", "Settlement occurs later than T+2"],
        ["R-04", "Missing regulatory classification", "Medium", "Classification is required"],
        ["R-05", "Duplicate bank record", "High", "More than one bank record for transaction"],
    ], columns=["rule_id", "rule_name", "severity", "description"]).to_csv(DATA / "control_rules.csv", index=False)


if __name__ == "__main__":
    build()
    print(f"Created synthetic source data in {DATA}")
