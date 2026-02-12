import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="BrineX Smart Brine Recovery & Economic Optimization Platform",
    layout="wide"
)

# HEADER
col1, col2 = st.columns([8, 2])

with col1:
    st.title("BrineX Smart Brine Recovery & Economic Optimization Platform")
    st.markdown("### AI-Driven Resource Recovery & Profit Optimization")

with col2:
    st.markdown("## 🔷 BrineX")

st.markdown("---")

# SIDEBAR
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
    "Upload Lab Data (CSV or Excel)",
    type=["csv", "xlsx"]
)

# --------------------------------------------------

if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")
    st.subheader("Raw Lab Data")
    st.dataframe(df)

    required_columns = [
        "Flow_m3_day",
        "Mg_concentration_kg_m3",
        "Ca_concentration_kg_m3"
    ]

    if not all(col in df.columns for col in required_columns):

        st.error("Uploaded file must contain these columns:")
        st.write(required_columns)

    else:

        df["Mg_recovered_ton_day"] = (
            df["Flow_m3_day"]
            * df["Mg_concentration_kg_m3"]
            * recovery_eff
            / 1000
        )

        df["Ca_recovered_ton_day"] = (
            df["Flow_m3_day"]
            * df["Ca_concentration_kg_m3"]
            * recovery_eff
            / 1000
        )

        df["Revenue_Mg"] = df["Mg_recovered_ton_day"] * mg_price
        df["Revenue_Ca"] = df["Ca_recovered_ton_day"] * ca_price

        df["Total_Revenue"] = df["Revenue_Mg"] + df["Revenue_Ca"]
        df["Net_Profit"] = df["Total_Revenue"] - operating_cost

        st.markdown("---")
        st.subheader("Performance Indicators")

        total_mg = df["Mg_recovered_ton_day"].sum()
        total_ca = df["Ca_recovered_ton_day"].sum()
        total_revenue = df["Total_Revenue"].sum()
        total_profit = df["Net_Profit"].sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Mg(OH)₂ (ton/day)", round(total_mg, 2))
        col2.metric("Total CaCO₃ (ton/day)", round(total_ca, 2))
        col3.metric("Total Revenue (OMR/day)", round(total_revenue, 2))
        col4.metric("Net Profit (OMR/day)", round(total_profit, 2))

        st.markdown("---")
        st.subheader("Revenue & Profit Trends")

        st.bar_chart(df[["Total_Revenue", "Net_Profit"]])

        st.markdown("---")
        st.subheader("Optimization Insight")

        if total_profit > 0:
            st.success("✅ Project is PROFITABLE under current assumptions.")
        else:
            st.error("❌ Project is NOT profitable. Adjust recovery or pricing.")

else:
    st.info("Please upload lab data file to begin analysis.")
