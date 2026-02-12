import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="BrineX – Smart Brine Management System",
    layout="wide"
)

st.title("🌊 BrineX – AI-Powered Sustainable Brine Management System")
st.markdown("Integrated ML + Economic + Environmental Decision Support Tool")
st.markdown("---")

# ---------------------------------------------------
# MACHINE LEARNING SECTION (From Code 1)
# ---------------------------------------------------

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
        if mg[i] > 1700:
            y[i] = 1
        elif ca[i] > 900:
            y[i] = 2
        else:
            y[i] = 0

    cost = 0.035 * flow + rng.normal(0, 20, n)
    cost = np.maximum(cost, 0)
    return X, y, cost

def train_models():
    X, y, cost = generate_synthetic_data()
    Xs, mu, sigma = standardize_fit(X)
    Xb = np.hstack([np.ones((Xs.shape[0],1)), Xs])

    k = 3
    W = np.zeros((Xs.shape[1]+1, k))
    Y = np.eye(k)[y]

    for _ in range(600):
        P = softmax(Xb @ W)
        grad = Xb.T @ (P - Y) / len(X)
        W -= 0.1 * grad

    wR = np.linalg.pinv(Xb) @ cost
    return W, mu, sigma, wR

W, mu, sigma, wR = train_models()
LABELS = ["SKIP", "MAGNESIUM", "CALCIUM"]

# ---------------------------------------------------
# SIDEBAR INPUT OPTIONS
# ---------------------------------------------------

mode_select = st.sidebar.radio("Choose Input Mode:",
                                ["Manual Input", "Upload Lab File"])

# ---------------------------------------------------
# MANUAL INPUT MODE
# ---------------------------------------------------

if mode_select == "Manual Input":

    Mg = st.sidebar.number_input("Mg (mg/L)", 0, 5000, 1800)
    Ca = st.sidebar.number_input("Ca (mg/L)", 0, 5000, 900)
    Sal = st.sidebar.number_input("Salinity (mg/L)", 0, 120000, 65000)
    Temp = st.sidebar.number_input("Temperature (°C)", 0, 60, 30)
    Flow = st.sidebar.number_input("Flow (m3/day)", 0, 500000, 100000)

    x = np.array([[Mg, Ca, Sal, Temp, Flow]])
    Xs = standardize_apply(x, mu, sigma)
    Xb = np.hstack([np.ones((1,1)), Xs])
    probs = softmax(Xb @ W)[0]
    mode = LABELS[np.argmax(probs)]

    cost = float(Xb @ wR)

    st.subheader("🤖 AI Treatment Recommendation")
    st.success(mode)

    st.write("Prediction Confidence:")
    st.write(f"Magnesium: {probs[1]:.2f}")
    st.write(f"Calcium: {probs[2]:.2f}")
    st.write(f"Skip: {probs[0]:.2f}")

    revenue = (Mg * Flow / 1_000_000) * 2.5
    profit = revenue - cost

    col1, col2, col3 = st.columns(3)
    col1.metric("Estimated Cost (OMR/day)", f"{cost:,.2f}")
    col2.metric("Estimated Revenue (OMR/day)", f"{revenue:,.2f}")
    col3.metric("Estimated Profit (OMR/day)", f"{profit:,.2f}")

# ---------------------------------------------------
# FILE UPLOAD MODE (From Code 1 Full Pipeline)
# ---------------------------------------------------

if mode_select == "Upload Lab File":

    uploaded_file = st.file_uploader("Upload CSV or Excel file")

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("Preview of Data:")
        st.dataframe(df.head())

        required = ["Mg_mgL","Ca_mgL","Salinity_mgL","Temp_C","Flow_m3_day"]

        if all(col in df.columns for col in required):

            results = []

            for _, row in df.iterrows():
                x = np.array([[row["Mg_mgL"], row["Ca_mgL"],
                               row["Salinity_mgL"],
                               row["Temp_C"],
                               row["Flow_m3_day"]]])

                Xs = standardize_apply(x, mu, sigma)
                Xb = np.hstack([np.ones((1,1)), Xs])
                probs = softmax(Xb @ W)[0]
                mode = LABELS[np.argmax(probs)]
                cost = float(Xb @ wR)

                revenue = (row["Mg_mgL"] *
                           row["Flow_m3_day"] / 1_000_000) * 2.5
                profit = revenue - cost

                results.append([mode, cost, revenue, profit])

            df["ML_Mode"] = [r[0] for r in results]
            df["Cost"] = [r[1] for r in results]
            df["Revenue"] = [r[2] for r in results]
            df["Profit"] = [r[3] for r in results]

            st.subheader("📊 Results")
            st.dataframe(df)

            st.subheader("Mode Distribution")
            st.bar_chart(df["ML_Mode"].value_counts())

            st.subheader("Total Profit")
            st.metric("Total Profit (OMR)",
                      f"{df['Profit'].sum():,.2f}")

            csv = df.to_csv(index=False).encode()
            st.download_button("Download Results",
                               csv,
                               "BrineX_ML_Results.csv")

        else:
            st.error("Missing required columns in uploaded file.")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.markdown("---")
st.markdown("Developed by BrineX | AI + Sustainability + Chemical Engineering 🌱")
