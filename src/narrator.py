import os

# Developer: Devvrat Welekar
from langchain_community.llms import Ollama

def generate_cfo_narrative(conn, model_name=None):
    llm = Ollama(
        model=model_name or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
        temperature=0.7,
    )
    
    metrics = conn.execute("SELECT SUM(NetRevenue), SUM(ProfitMargin) FROM sales").fetchone()
    top_product = conn.execute("SELECT Product FROM sales GROUP BY Product ORDER BY SUM(NetRevenue) DESC LIMIT 1").fetchone()[0]
    top_region = conn.execute("SELECT Region FROM sales GROUP BY Region ORDER BY SUM(NetRevenue) DESC LIMIT 1").fetchone()[0]

    prompt = f"""
    You are a Chief Financial Officer (CFO). Write an executive summary bulleted briefing for the Board of Directors using these real-time analytics:
    - Total Net Revenue: ${metrics[0]:,.2f}
    - Total Net Profit: ${metrics[1]:,.2f}
    - Top Product Driver: {top_product}
    - Leading Region: {top_region}

    Format: Provide 3 direct, high-impact bullet points focusing on financial health and revenue performance."""
    
    return llm.invoke(prompt).strip()