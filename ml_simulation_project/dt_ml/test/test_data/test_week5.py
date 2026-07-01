# run this once to create test CSVs
import pandas as pd
import numpy as np
import os

os.makedirs("dt_ml/test_data", exist_ok=True)

clean_df = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=36, freq='M'),
    'revenue': np.linspace(100000, 250000, 36),
    'price': 50,
    'units_sold': np.linspace(2000, 1500, 36),
    'marketing_spend': 5000,
    'headcount': 50 + np.arange(36) // 6,
    'churn': 0.02
})
clean_df.to_csv("dt_ml/test_data/sales_clean.csv", index=False)

messy_df = pd.DataFrame({
    'date': ['2023-01', '2023-02', 'invalid', '2023-04', '2023-05'],
    'revenue': [100000, '150k', 200000, None, 250000],
    'price': [50, 50, 'fifty', 50, 50],
    'units_sold': [2000, 1900, 1800, 1700, None],
    'marketing_spend': [5000, 5200, 5100, None, 5300]
})
messy_df.to_csv("dt_ml/test_data/sales_messy.csv", index=False)

seasonal_df = pd.DataFrame({
    'date': pd.date_range('2022-01-01', periods=36, freq='M'),
    'revenue': [100000 + (i % 12) * 30000 for i in range(36)],
    'price': 50,
    'units_sold': [2000 - (i % 12) * 100 for i in range(36)],
    'marketing_spend': [5000 + (i % 12) * 500 for i in range(36)],
    'headcount': 50,
    'churn': 0.02
})
seasonal_df.to_csv("dt_ml/test_data/sales_seasonal.csv", index=False)

hr_df = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=24, freq='M'),
    'revenue': 100000 * (1 + np.arange(24) * 0.05),
    'headcount': 50 + np.arange(24) * 2,
    'salary': 95000,
    'churn': 0.02
})
hr_df.to_csv("dt_ml/test_data/hr_growing.csv", index=False)

marketing_df = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=24, freq='M'),
    'revenue': 100000 + np.random.normal(0, 20000, 24).cumsum(),
    'marketing_spend': 5000 + np.random.normal(0, 1500, 24),
    'new_customers': np.random.poisson(100, 24),
    'churn': 0.02 + np.random.normal(0, 0.005, 24)
})
marketing_df.to_csv("dt_ml/test_data/marketing_volatile.csv", index=False)

print("All test CSVs created in dt_ml/test_data/")