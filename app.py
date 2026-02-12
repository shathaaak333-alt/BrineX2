# ==========================================================
# BrineX Smart Brine Recovery Platform
# Full ML + Economic Dashboard Web App
# ==========================================================

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

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
# SIDEBAR INPUTS
# ----------------------------------------------------------
st.sidebar.header("Economic Assumptions")

eff = st.sidebar.slider("Recovery Efficiency", 0.5, 0.95, 0.75)
price_mgoh2 = st.sidebar.number_input("Mg(OH)₂ Price (OMR/ton)", value=150.0)
price_caco3 = st.sidebar.number_input("CaCO₃ Price (OMR/ton)", value=60.0)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Upload Lab Data (CSV or Excel)")

# ----------------------------------------------------------
# ML FUNCTIONS
# ----------------------------------------------------------
def standardize_fit(X):
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma = np.where(sigma == 0, 1.0, sigma)
    return (X - mu) / sigma, mu, sigma

def standardize_apply(X, mu, sigma):
    return (X - mu) / sigma

def softmax(z):
    z = z - np.max(z, axis=1, keepdims=True)
    e = np.exp(z)
    return e / np.sum(e, axis=1, keepdims=True)

def generate_synthetic_data(n=4000, seed=42):
    rng = np.random.default_rng(seed)
    mg = rng.uniform(400, 2600, n)
    ca = rng.uniform(150, 1400, n)
    sal = rng.uniform(45000, 95000, n)
    temp = rng.uniform(15, 42, n)
    flow = rng.uniform(2000, 60000, n)
    X = np.vstack([mg, ca, sal, temp, flow]).T

    y = np.zeros(n, dtype=int)
    for i in range(n):
        if mg[i] > 1800:
            y[i] = 1
        elif ca[i] > 900:
            y[i] = 2
        else:
            y[i] = 0

    cost = 0.035 * flow + 0.0008 * flow * (mg/1500) + 0.0006 * flow * (ca/800)
    cost += rng.normal(0, 20, n)
    return X, y, cost

def train_models():
    X_train, y_train, cost_train = generate_synthetic_data()
    Xs, mu_c, sig_c = standardize_fit(X_train)
    Xb = np.hstack([np.ones((Xs.shape[0],1)), Xs])
    k = 3
    W = np.zeros((Xs.shape[1]+1, k))
    Y = np.zeros((Xs.shape[0], k))
    Y[np.arange(len(y_train)), y_train] = 1

    for _ in range(600):
        P = softmax(Xb @ W)
        grad = (Xb.T @ (P - Y)) / len(Xb)
        W -= 0.1 * grad

    Xs_r, mu_r, sig_r = standardize_fit(X_train)
    Xb_r = np.hstack([np.ones((Xs_r.shape[0],1)), Xs_r])
    wR = np.linalg.solve(Xb_r.T @ Xb_r + 2*np.eye(Xb_r.shape[1]), Xb_r.T @ cost_train)

    return W, mu_c, sig_c, wR, mu_r, sig_r

W, mu_c, sig_c, wR, mu_r, sig_r = train_models()

LABELS = ["SKIP", "MAGNESIUM", "CALCIUM"]

# ----------------------------------------------------------
# MAIN LOGIC
# ----------------------------------------------------------
if uploaded_file:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    required = ["Mg_mgL", "Ca_mgL", "Salinity_mgL", "Temp_C", "Flow_m3_day"]
    if not all(col in df.columns for col in required):
        st.error(f"Missing required columns: {required}")
        st.stop()

    results = []

    for _, row in df.iterrows():
        x = np.array([[row[c] for c in required]])
        xs = standardize_apply(x, mu_c, sig_c)
        xb = np.hstack([np.ones((1,1)), xs])
        probs = softmax(xb @ W)[0]
        mode = LABELS[np.argmax(probs)]

        xs_r = standardize_apply(x, mu_r, sig_r)
        xb_r = np.hstack([np.ones((1,1)), xs_r])
        cost = float(xb_r @ wR)

        if mode == "MAGNESIUM":
            prod = ((row["Mg_mgL"]/1000) * row["Flow_m3_day"] * eff * 2.4)/1000
            revenue = prod * price_mgoh2
        elif mode == "CALCIUM":
            prod = ((row["Ca_mgL"]/1000) * row["Flow_m3_day"] * eff * 2.5)/1000
            revenue = prod * price_caco3
        else:
            prod = 0
            revenue = 0

        profit = revenue - cost

        results.append([mode, cost, prod, revenue, profit])

    df[["Mode","Cost_OMR_day","Product_ton_day",
        "Revenue_OMR_day","Profit_OMR_day"]] = results

    # ----------------------------------------------------------
    # DASHBOARD METRICS
    # ----------------------------------------------------------
    st.subheader("📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Profit (OMR)", round(df["Profit_OMR_day"].sum(),2))
    col2.metric("Total Revenue (OMR)", round(df["Revenue_OMR_day"].sum(),2))
    col3.metric("Total Cost (OMR)", round(df["Cost_OMR_day"].sum(),2))
    col4.metric("Avg Daily Production (ton)", round(df["Product_ton_day"].mean(),3))

    st.markdown("---")

    # ----------------------------------------------------------
    # MODE DISTRIBUTION
    # ----------------------------------------------------------
    st.subheader("Mode Distribution")
    fig1, ax1 = plt.subplots()
    df["Mode"].value_counts().plot(kind="bar", ax=ax1)
    st.pyplot(fig1)

    # ----------------------------------------------------------
    # PROFIT TREND (IF MONTH EXISTS)
    # ----------------------------------------------------------
    if "Month" in df.columns:
        st.subheader("Monthly Profit Analysis")
        monthly = df.groupby("Month")["Profit_OMR_day"].sum()
        fig2, ax2 = plt.subplots()
        monthly.plot(kind="bar", ax=ax2)
        st.pyplot(fig2)

    st.markdown("---")

    # ----------------------------------------------------------
    # DATA TABLE
    # ----------------------------------------------------------
    st.subheader("Processed Data")
    st.dataframe(df)

    # ----------------------------------------------------------
    # DOWNLOAD BUTTON
    # ----------------------------------------------------------
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Results CSV",
                       data=csv,
                       file_name="brinex_results.csv",
                       mime="text/csv")

else:
    st.info("Please upload lab data file to start analysis.")
