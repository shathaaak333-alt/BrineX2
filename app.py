# ==========================================================
# BrineX Smart Brine Recovery Platform (Stable Version)
# ==========================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
# SIDEBAR
# ----------------------------------------------------------
st.sidebar.header("Economic Assumptions")

eff = st.sidebar.slider("Recovery Efficiency", 0.5, 0.95, 0.75)
price_mgoh2 = st.sidebar.number_input("Mg(OH)₂ Price (OMR/ton)", value=150.0)
price_caco3 = st.sidebar.number_input("CaCO₃ Price (OMR/ton)", value=60.0)

uploaded_file = st.sidebar.file_uploader("Upload Lab Data (CSV or Excel)")

# ----------------------------------------------------------
# SAFE ML MODEL (Pre-trained once)
# ----------------------------------------------------------
@st.cache_resource
def train_models():

    rng = np.random.default_rng(42)
    n = 3000

    mg = rng.uniform(400, 2600, n)
    ca = rng.uniform(150, 1400, n)
    sal = rng.uniform(45000, 95000, n)
    temp = rng.uniform(15, 42, n)
    flow = rng.uniform(2000, 60000, n)

    X = np.vstack([mg, ca, sal, temp, flow]).T

    # Mode rule (simple and stable)
    y = np.where(mg > 1800, 1,
        np.where(ca > 900, 2, 0))

    cost = 0.035 * flow + 0.0008 * flow*(mg/1500) + 0.0006 * flow*(ca/800)

    # Standardization
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma[sigma == 0] = 1
    Xs = (X - mu)/sigma

    # Add bias
    Xb = np.hstack([np.ones((n,1)), Xs])

    # Simple linear classifier (no softmax instability)
    W = np.linalg.pinv(Xb) @ pd.get_dummies(y).values

    # Ridge regression for cost
    I = np.eye(Xb.shape[1])
    I[0,0] = 0
    wR = np.linalg.solve(Xb.T@Xb + 1.5*I, Xb.T@cost)

    return W, wR, mu, sigma

W, wR, mu, sigma = train_models()

LABELS = ["SKIP", "MAGNESIUM", "CALCIUM"]

# ----------------------------------------------------------
# MAIN
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

    results = []

    for _, row in df.iterrows():

        x = np.array([[row[c] for c in required]])
        xs = (x - mu)/sigma
        xb = np.hstack([np.ones((1,1)), xs])

        probs = xb @ W
        mode_index = np.argmax(probs)
        mode = LABELS[mode_index]

        cost = float(xb @ wR)

        # Production
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

        results.append([mode, cost, prod, revenue, profit])

    df[["Mode","Cost_OMR_day","Product_ton_day",
        "Revenue_OMR_day","Profit_OMR_day"]] = results

    # ----------------------------------------------------------
    # DASHBOARD
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

    # Mode distribution
    st.subheader("Mode Distribution")

    fig, ax = plt.subplots()
    df["Mode"].value_counts().plot(kind="bar", ax=ax)
    st.pyplot(fig)

    # Monthly profit if exists
    if "Month" in df.columns:
        st.subheader("Monthly Profit")
        monthly = df.groupby("Month")["Profit_OMR_day"].sum()
        fig2, ax2 = plt.subplots()
        monthly.plot(kind="bar", ax=ax2)
        st.pyplot(fig2)

    st.markdown("---")

    st.subheader("Processed Data")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button("Download Results",
                       data=csv,
                       file_name="brinex_results.csv",
                       mime="text/csv")

else:
    st.info("Upload your lab data file to begin analysis.")

