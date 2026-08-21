# Developer: Devvrat Welekar
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from database import get_db_connection, get_schema
from pipeline import TextToSQLPipeline
from narrator import generate_cfo_narrative

st.set_page_config(
    page_title="GenAI SQL Financial Analytics | Devvrat Welekar",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive Theme CSS (Matches Power BI Dark Slate / Beige Layout)
st.markdown("""
<style>
    .main { background-color: #F8F9FA; }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #2B2D42;
    }
    div[data-testid="stSidebarNav"] { font-weight: bold; }
    .cfo-card {
        background-color: #2B2D42;
        color: #F8F9FA;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_backend():
    # Use a private in-memory DuckDB instance so browser sessions do not lock the shared file.
    conn = get_db_connection(":memory:")
    schema = get_schema(conn)
    pipeline = TextToSQLPipeline(conn, schema)
    return conn, pipeline, schema

conn, pipeline, schema = init_backend()

# Load base dataset for live Plotly dashboards
@st.cache_data
def load_data():
    df = conn.execute("SELECT * FROM sales").fetchdf()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month_Name'] = df['Date'].dt.strftime('%b')
    df['Month_Num'] = df['Date'].dt.month
    return df

df_sales = load_data()

# Sidebar Interactive Filters
st.sidebar.title("🎛️ Executive Control Panel")
st.sidebar.caption("Architected by Devvrat Welekar")

selected_regions = st.sidebar.multiselect(
    "Filter by Region:",
    options=df_sales['Region'].unique().tolist(),
    default=df_sales['Region'].unique().tolist()
)

selected_depts = st.sidebar.multiselect(
    "Filter by Department:",
    options=df_sales['Department'].unique().tolist(),
    default=df_sales['Department'].unique().tolist()
)

# Apply global filters
filtered_df = df_sales[
    (df_sales['Region'].isin(selected_regions)) &
    (df_sales['Department'].isin(selected_depts))
]

# Dashboard Header Banner
st.title("⚡ GenAI-Powered SQL Analytics & Financial Reporting")
st.markdown("**Enterprise Business Intelligence Platform** | Python • DuckDB • LangChain • Plotly • Power BI")
st.divider()

# Tab Layout
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Power BI Mirror Dashboard",
    "💬 Text-to-SQL Workspace",
    "💼 Executive CFO Briefing",
    "🚨 Anomaly Radar"
])

# ==========================================
# TAB 1: POWER BI MIRROR DASHBOARD
# ==========================================
with tab1:
    # Top Metrics Bar
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    tot_net_rev = filtered_df['NetRevenue'].sum()
    tot_profit = filtered_df['ProfitMargin'].sum()
    tot_op_cost = filtered_df['OperatingCost'].sum()
    tot_txns = len(filtered_df)

    kpi1.metric("Total Net Revenue", f"₹ {tot_net_rev:,.2f}")
    kpi2.metric("Total Profit Margin", f"₹ {tot_profit:,.2f}")
    kpi3.metric("Total Operating Cost", f"₹ {tot_op_cost:,.2f}")
    kpi4.metric("Total Transactions", f"{tot_txns:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.8])

    with col_left:
        st.subheader("Revenue by Region & Product")
        sunburst_fig = px.sunburst(
            filtered_df,
            path=['Region', 'Product'],
            values='NetRevenue',
            color='NetRevenue',
            color_continuous_scale='YlOrBr',
            title="Net Revenue Distribution"
        )
        sunburst_fig.update_layout(height=450, margin=dict(t=30, l=0, r=0, b=0))
        st.plotly_chart(sunburst_fig, use_container_width=True)

    with col_right:
        st.subheader("Financial Performance Trends by Month")
        monthly_df = filtered_df.groupby(['Month_Num', 'Month_Name']).agg(
            Total_NetRevenue=('NetRevenue', 'sum'),
            Total_ProfitMargin=('ProfitMargin', 'sum'),
            Total_OperatingCost=('OperatingCost', 'sum')
        ).reset_index().sort_values('Month_Num')

        fig_combo = go.Figure()
        
        # Dual Bar + Line Chart (Matching Power BI Visual Layout)
        fig_combo.add_trace(go.Bar(
            x=monthly_df['Month_Name'],
            y=monthly_df['Total_ProfitMargin'],
            name='Total Profit Margin',
            marker_color='#C19A6B'
        ))
        fig_combo.add_trace(go.Bar(
            x=monthly_df['Month_Name'],
            y=monthly_df['Total_NetRevenue'],
            name='Total Net Revenue',
            marker_color='#2B2D42'
        ))
        fig_combo.add_trace(go.Scatter(
            x=monthly_df['Month_Name'],
            y=monthly_df['Total_OperatingCost'],
            name='Total Operating Cost',
            mode='lines+markers',
            line=dict(color='#D9534F', width=3)
        ))

        fig_combo.update_layout(
            barmode='group',
            height=450,
            xaxis_title="Month",
            yaxis_title="Amount (₹)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=30, l=0, r=0, b=0)
        )
        st.plotly_chart(fig_combo, use_container_width=True)

# ==========================================
# TAB 2: TEXT-TO-SQL WORKSPACE
# ==========================================
with tab2:
    st.header("Query Financial Database in Plain English")
    user_q = st.text_input(
        "Enter your query:",
        placeholder="What are the top 3 regions by net revenue?"
    )

    if st.button("Run Query", type="primary"):
        with st.spinner("Generating SQL query via LangChain & Ollama..."):
            sql, res = pipeline.execute_query(user_q)
            
            st.subheader("Generated DuckDB SQL")
            st.code(sql, language="sql")
            
            st.subheader("Execution Output")
            if isinstance(res, str):
                st.error(res)
            else:
                st.dataframe(res, use_container_width=True)
                if (
                    not res.empty
                    and len(res.columns) >= 2
                    and pd.api.types.is_numeric_dtype(res.iloc[:, 1])
                ):
                    fig_dynamic = px.bar(
                        res, 
                        x=res.columns[0], 
                        y=res.columns[1], 
                        title="Dynamic Query Visualization",
                        color_discrete_sequence=['#2B2D42']
                    )
                    st.plotly_chart(fig_dynamic, use_container_width=True)

# ==========================================
# TAB 3: EXECUTIVE CFO BRIEFING
# ==========================================
with tab3:
    st.header("Automated C-Suite Executive Summary")
    st.write("Generates board-ready briefing bullets dynamically from transactional data.")
    
    if st.button("Generate CFO Narrative"):
        with st.spinner("Synthesizing metrics via LLM..."):
            narrative = generate_cfo_narrative(conn)
            narrative_html = narrative.replace("\n", "<br>")
            st.markdown(f"""
            <div class="cfo-card">
                <h3>📋 Board Briefing Notes</h3>
                <p>{narrative_html}</p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# TAB 4: ANOMALY RADAR
# ==========================================
with tab4:
    st.header("Revenue Anomaly Radar (Z-Score Analysis)")
    st.write("Flags transactions exceeding 2.5 standard deviations from mean net revenue.")

    df_anom = filtered_df.copy()
    df_anom['Z_Score'] = stats.zscore(df_anom['NetRevenue'])
    anomalies = df_anom[df_anom['Z_Score'].abs() > 2.5].sort_values(by='NetRevenue', ascending=False)

    st.subheader(f"Flagged Outliers ({len(anomalies)} Transactions Found)")
    st.dataframe(anomalies[['TransactionID', 'Date', 'Product', 'Region', 'Department', 'NetRevenue', 'Z_Score']], use_container_width=True)

    fig_anom = px.scatter(
        anomalies,
        x="Date",
        y="NetRevenue",
        color="Product",
        size="NetRevenue",
        hover_data=['TransactionID', 'Region', 'Department'],
        title="Detected Outlier Revenue Events"
    )
    st.plotly_chart(fig_anom, use_container_width=True)