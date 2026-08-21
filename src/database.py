# Developer: Devvrat Welekar
import duckdb

def get_db_connection(db_path='finance_analytics.db'):
    conn = duckdb.connect(db_path)
    conn.execute("CREATE OR REPLACE TABLE sales AS SELECT * FROM read_csv_auto('data/financial_sales.csv')")
    return conn

def get_schema(conn):
    schema_info = conn.execute("PRAGMA table_info('sales')").fetchall()
    return ", ".join([f"{col[1]} ({col[2]})" for col in schema_info])