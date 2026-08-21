# Developer: Devvrat Welekar
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_data(rows=2500, output_path='data/financial_sales.csv'):
    np.random.seed(42)

    products = ['Cloud Server Tier-1', 'AI API Gateway', 'Enterprise DB Ingestion', 'BI Dashboard Portal']
    regions = ['North America', 'Europe', 'Asia-Pacific', 'Latin America']
    departments = ['Engineering', 'Sales', 'Marketing', 'Customer Success']

    data = {
        'TransactionID': [f"TXN-{10000+i}" for i in range(rows)],
        'Date': [datetime(2025, 1, 1) + timedelta(days=int(np.random.randint(0, 365))) for _ in range(rows)],
        'Product': np.random.choice(products, size=rows, p=[0.35, 0.30, 0.20, 0.15]),
        'Region': np.random.choice(regions, size=rows),
        'Department': np.random.choice(departments, size=rows),
        'Quantity': np.random.randint(1, 12, size=rows),
        'UnitPrice': np.random.choice([200, 500, 1200, 2500], size=rows),
        'Discount': np.random.choice([0.0, 0.05, 0.10], size=rows)
    }

    df = pd.DataFrame(data)

    # Margin & Financial Calculations
    df['GrossRevenue'] = df['Quantity'] * df['UnitPrice']
    df['NetRevenue'] = df['GrossRevenue'] * (1 - df['Discount'])
    df['OperatingCost'] = df['NetRevenue'] * np.random.uniform(0.40, 0.60, size=rows)
    df['ProfitMargin'] = df['NetRevenue'] - df['OperatingCost']

    # Inject 15 Revenue Anomalies for Analytics Detection
    anom_indices = np.random.choice(rows, size=15, replace=False)
    df.loc[anom_indices, 'NetRevenue'] = df.loc[anom_indices, 'NetRevenue'] * np.random.uniform(4.0, 6.0)

    df.to_csv(output_path, index=False)
    print(f"Data generation complete: {output_path} ({rows} records generated with injected anomalies)")

if __name__ == "__main__":
    generate_synthetic_data()