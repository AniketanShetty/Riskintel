# Depth-4 Decision Tree Rules

```text
|--- cibil_score <= 549.50
|   |--- loan_term <= 5.00
|   |   |--- loan_amount <= 26250000.00
|   |   |   |--- annual_income <= 7050000.00
|   |   |   |   |--- class: 1
|   |   |   |--- annual_income >  7050000.00
|   |   |   |   |--- class: 0
|   |   |--- loan_amount >  26250000.00
|   |   |   |--- residential_assets_value <= 400000.00
|   |   |   |   |--- class: 0
|   |   |   |--- residential_assets_value >  400000.00
|   |   |   |   |--- class: 1
|   |--- loan_term >  5.00
|   |   |--- class: 0
|--- cibil_score >  549.50
|   |--- residential_assets_value <= 550000.00
|   |   |--- commercial_assets_value <= 50000.00
|   |   |   |--- luxury_assets_value <= 800000.00
|   |   |   |   |--- class: 0
|   |   |   |--- luxury_assets_value >  800000.00
|   |   |   |   |--- class: 1
|   |   |--- commercial_assets_value >  50000.00
|   |   |   |--- loan_amount <= 29850000.00
|   |   |   |   |--- class: 1
|   |   |   |--- loan_amount >  29850000.00
|   |   |   |   |--- class: 1
|   |--- residential_assets_value >  550000.00
|   |   |--- residential_assets_value <= 950000.00
|   |   |   |--- commercial_assets_value <= 450000.00
|   |   |   |   |--- class: 1
|   |   |   |--- commercial_assets_value >  450000.00
|   |   |   |   |--- class: 1
|   |   |--- residential_assets_value >  950000.00
|   |   |   |--- class: 1

```
