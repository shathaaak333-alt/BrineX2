import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="BrineX Smart Brine Recovery & Economic Optimization Platform",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
col1, col2 = st.columns([8, 2])

with col1:
    st.title("BrineX Smart Brine Recovery & Economic Optimization Platform")
    st.markdown("### AI-Driven Resource Recovery & Profit Optimization")

with col2:
    st.markdown("## 🔷 BrineX")

st.markdown("---")

# --------------------------------------------------
# SIDEBAR – ECONOMIC ASSUMPTIONS
# --------------------------------------------------
st.sidebar.header("Economic Assumptions")

recovery_eff = st.sidebar.slider(
    "Recovery Efficiency",
    0.50, 0.95, 0.75, 0.01
)

mg_price = st.sidebar.number_input(
    "Mg(OH)₂ Price (OMR/ton)", value=150.0
)

ca_price = st.sidebar.number_input(
    "CaCO₃ Price (OMR/ton)", value=60.0
)

operating_cost = st.sidebar.number_input(
    "Operating Cost (OMR/day)", value=500.0
)

st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "Upload Lab Data (CSV or Excel) - Optional",
    type=["csv", "xlsx"]
)

# --------------------------------------------------
# DATA SECTION
# --------------------------------------------------

st.subheader("Input Data")

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")
    st.dataframe(df)

    st.markdown("### Select Relevant Columns")

    flow_col = st.selectbox("Flow (m3/day)", df.columns)
    mg_col = st.selectbox("Mg Concentration (kg/m3)", df.columns)
    ca_col = st.selectbox("Ca Concentration (kg/m3)", df.columns)

    flow = df[flow_col].mean()
    mg_conc = df[mg_col].mean()
    ca_conc = df[ca_col].mean()

else:
    st.info("No file uploaded. Please enter values manually.")

    flow = st.number_input("Flow (m3/day)", value=1000.0)
    mg_conc = st.number_input("Mg Concentration (kg/m3)", value=2.0)
    ca_conc = st.number_input("Ca Concentration (kg/m3)", value=1.5)

# --------------------------------------------------
# CALCULATIONS
# --------------------------------------------------

mg_recovered = flow * mg_conc * recovery_eff / 1000
ca_recovered = flow * ca_conc * recovery_eff / 1000

revenue_mg = mg_recovered * mg_price
revenue_ca = ca_recovered * ca_price

total_revenue = revenue_mg + revenue_ca
net_profit = total_revenue - operating_cost

# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------

st.markdown("---")
st.subheader("Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Mg(OH)₂ Recovered (ton/day)", round(mg_recovered, 2))
col2.metric("CaCO₃ Recovered (ton/day)", round(ca_recovered, 2))
col3.metric("Total Revenue (OMR/day)", round(total_revenue, 2))
col4.metric("Net Profit (OMR/day)", round(net_profit, 2))

# --------------------------------------------------
# CHART SECTION
# --------------------------------------------------

st.markdown("---")
st.subheader("Economic Breakdown")

chart_df = pd.DataFrame({
    "Value": [revenue_mg, revenue_ca, operating_cost]
}, index=["Revenue Mg", "Revenue Ca", "Operating Cost"])

st.bar_chart(chart_df)

# --------------------------------------------------
# OPTIMIZATION INSIGHT
# --------------------------------------------------

st.markdown("---")
st.subheader("Optimization Insight")

if net_profit > 0:
    st.success("✅ Project is PROFITABLE under current assumptions.")
else:
    st.error("❌ Project is NOT profitable. Adjust recovery, pricing, or cost.")
