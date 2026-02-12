# ==========================================================
# BrineX Smart Brine Recovery Platform (Simple & Stable)
# No matplotlib version – Streamlit native charts
# ==========================================================

import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="BrineX Platform", layout="wide")

# ----------------------------------------------------------
# HEADER
# ----------------------------------------------------------
col1, col2 = st.columns([8,1])
with col1:
    st.title("BrineX Smart Brine Recovery & Economic Optimization Platform")
with col2:
    st.markdown("### 🔷 BrineX")

st.markdown("---")

# ----------------------------------------------------------
# SIDEBAR SETTINGS
# ----------------------------------------------------------
st.sidebar.header("Economic Assumptions")

eff = st.sidebar.slider("Recovery Efficiency", 0.5, 0.95, 0.75)
price_mgoh2 = st.sidebar.number_input("Mg(OH)₂ Price (OMR/ton)", value=150.0)
price_caco3 = st.sidebar.number_input("CaCO₃ Price (OMR/ton)", value=60.0)

uploaded_file = st.sidebar.file_uploader("Upload Lab Data (CSV or Excel)")

# ----------------------------------------------------------
# SIMPLE ML MODEL (Stable & Cached)
# ----------------------------------------------------------
@st.cache_resource
def train_model():
    rng = np.random.default_rng(42)
    n = 2500

    mg = rng.uniform(400, 2600, n)
    ca = rng.uniform(150, 1400, n)
    sal = rng.uniform(45000, 95000, n)
    temp = rng.uniform(15, 42, n)
    flow = rng.uniform(2000, 60000, n)

    X = np.vstack([mg, ca, sal, temp, flow]).T

    # Simple rule-based labels
    y = np.where(mg > 1800, 1,
        np.where(ca > 900, 2, 0))

    # Standardization
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma[sigma == 0] = 1

    return mu, sigma

mu, sigma = train_model()

LABELS = ["SKIP", "MAGNESIUM", "CALCIUM"]

# ----------------------------------------------------------
# MAIN APP
# ----------------------------------------------------------
if uploaded_file:

    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error("File reading error: " + str(e))
        st.stop()

    required = ["Mg_mgL", "Ca_mgL", "Salinity_mgL", "Temp_C", "Flow_m3_day"]

    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    modes = []
    costs = []
    productions = []
    revenues = []
    profits = []

    for _, row in df.iterrows():

        # Simple decision logic
        if row["Mg_mgL"] > 1800:
            mode = "MAGNESIUM"
        elif row["Ca_mgL"] > 900:
            mode = "CALCIUM"
        else:
            mode = "SKIP"

        cost = 0.035 * row["Flow_m3_day"]

        if mode == "MAGNESIUM":
            prod = ((row["Mg_mgL"]/1000) *
                    row["Flow_m3_day"] * eff * 2.4)/1000
            revenue = prod * price_mgoh2

        elif mode == "CALCIUM":
            prod = ((row["Ca_mgL"]/1000) *
                    row["Flow_m3_day"] * eff * 2.5)/1000
            revenue = prod * price_caco3
        else:
            prod = 0
            revenue = 0

        profit = revenue - cost

        modes.append(mode)
        costs.append(cost)
        productions.append(prod)
        revenues.append(revenue)
        profits.append(profit)

    df["Mode"] = modes
    df["Cost_OMR_day"] = np.round(costs,2)
    df["Product_ton_day"] = np.round(productions,3)
    df["Revenue_OMR_day"] = np.round(revenues,2)
    df["Profit_OMR_day"] = np.round(profits,2)

    # ----------------------------------------------------------
    # KPI DASHBOARD
    # ----------------------------------------------------------
    st.subheader("📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Profit (OMR)",
                round(df["Profit_OMR_day"].sum(),2))
    col2.metric("Total Revenue (OMR)",
                round(df["Revenue_OMR_day"].sum(),2))
    col3.metric("Total Cost (OMR)",
                round(df["Cost_OMR_day"].sum(),2))
    col4.metric("Average Production (ton/day)",
                round(df["Product_ton_day"].mean(),3))

    st.markdown("---")

    # ----------------------------------------------------------
    # MODE DISTRIBUTION
    # ----------------------------------------------------------
    st.subheader("Mode Distribution")
    mode_counts = df["Mode"].value_counts()
    st.bar_chart(mode_counts)

    # ----------------------------------------------------------
    # MONTHLY PROFIT (IF EXISTS)
    # ----------------------------------------------------------
    if "Month" in df.columns:
        st.subheader("Monthly Profit")
        monthly = df.groupby("Month")["Profit_OMR_day"].sum()
        st.bar_chart(monthly)

    st.markdown("---")

    # ----------------------------------------------------------
    # DATA TABLE
    # ----------------------------------------------------------
    st.subheader("Processed Data")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button("Download Results",
                       data=csv,
                       file_name="brinex_results.csv",
                       mime="text/csv")

else:
    st.info("Upload your lab data file to begin analysis.")
