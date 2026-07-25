# Power BI implementation guide

Import these outputs with **Get Data → Text/CSV**:

- `exceptions.csv` — exception-level fact table
- `reconciled_transactions.csv` — transaction-level fact table
- `reconciliation_summary.csv` — KPI support table
- `control_summary.csv` — control monitoring summary

## Suggested measures

```DAX
Total Exceptions = COUNTROWS(exceptions)
High Risk Breaks = CALCULATE([Total Exceptions], exceptions[risk_level] = "High")
Value at Risk = SUM(exceptions[amount_eur])
Unresolved Issues = CALCULATE([Total Exceptions], exceptions[status] <> "Resolved")
Control Pass Rate = 1 - DIVIDE([Total Exceptions], COUNTROWS(reconciled_transactions))
```

## Six report pages

1. **Executive Risk Overview:** KPI cards, risk donut, trend by date, priority exception table.
2. **Reconciliation Monitor:** matched/unmatched/mismatch bar chart; break drill-through table.
3. **Exception Explorer:** slicers for provider, risk, currency and type; detailed audit notes.
4. **Anomaly Detection:** amount versus settlement-days scatter; filter `is_anomaly = TRUE`.
5. **Regulatory Reporting Readiness:** missing classification card and control failure chart.
6. **AI Investigator:** embed a Power Automate visual or Copilot-enabled Q&A experience backed by `exceptions`.

Use `transaction_id` to relate `exceptions` (many) to `reconciled_transactions` (one). Keep the source tables unmodified and schedule the Python pipeline before Power BI refresh.
