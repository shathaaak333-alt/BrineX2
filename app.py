import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="BrineX – Smart Brine Management",
    layout="wide"
)

st.title("🌊 BrineX – AI Sustainable Brine Management System")
st.markdown("ML + Economic + Environmental Decision Support Tool")
st.markdown("---")

# ---------------------------------------------------
# ML CORE
# ---------------------------------------------------
@st.cache_resource
def train_models():

    def standardize_fit(X):
        mu = X.mean(axis=0)
        sigma = X.std(axis=0)
        sigma = np.where(sigma == 0, 1.0, sigma)
        return (X - mu) / sigma, mu, sigma

    def softmax(z):
        z = z - np.max(z, axis=1, keepdims=True)
        e = np.exp(z)
        return e / np.sum(e, axis=1, keepdims=True)

    # synthetic training data
    rng = np.random.default_rng(42)
    n = 4000
    mg = rng.uniform(400, 2600, n)
    ca = rng.uniform(150, 1400, n)
    sal = rng.uniform(45000, 95000, n)
    temp = rng.uniform(15, 42, n)
    flow = rng.uniform(2000, 60000, n)

    X = np.vstack([mg, ca, sal, temp, flow]).T

    y = np.zeros(n, dtype=int)
    y[mg > 1700] = 1
    y[ca > 900] = 2

    Xs, mu, sigma = standardize_fit(X)
    Xb = np.hstack([np.ones((Xs.shape[0],1)), Xs])

    k = 3
    W = np.zeros((Xs.shape[1]+1, k))
    Y = np.eye(k)[y]

    for _ in range(500):
        P = softmax(Xb @ W)
        grad = Xb.T @ (P - Y) / len(X)
        W -= 0.1 * grad

    wR = np.linalg.pinv(Xb) @ (0.035 * flow)

    return W, mu, sigma, wR

W, mu, sigma, wR = train_models()
LABELS = ["SKIP", "MAGNESIUM", "CALCIUM"]

def predict(x):
    def standardize_apply(X, mu, sigma):
        return (X - mu) / sigma

    def softmax(z):
        z = z - np.max(z, axis=1, keepdims=True)
        e = np.exp(z)
        return e / np.sum(e, axis=1, keepdims=True)

    Xs = standardize_apply(x, mu, sigma)
    Xb = np.hstack([np.ones((1,1)), Xs])
    probs = softmax(Xb @ W)[0]
    mode = LABELS[np.argmax(probs)]
    cost = float(Xb @ wR)
    return mode, probs, cost

# ---------------------------------------------------
# SIDEBAR INPUT
# ---------------------------------------------------
st.sidebar.header("🔬 Brine Input Parameters")

Mg = st.sidebar.number_input("Mg (mg/L)", 0, 5000, 1800)
Ca = st.sidebar.number_input("Ca (mg/L)", 0, 5000, 900)
Sal = st.sidebar.number_input("Salinity (mg/L)", 0, 120000, 65000)
Temp = st.sidebar.number_input("Temperature (°C)", 0, 60, 30)
Flow = st.sidebar.number_input("Flow (m³/day)", 0, 500000, 100000)

x = np.array([[Mg, Ca, Sal, Temp, Flow]])

mode, probs, cost = predict(x)

# ---------------------------------------------------
# RESULTS
# ---------------------------------------------------
st.subheader("🤖 AI Recommendation")
st.success(mode)

col1, col2, col3 = st.columns(3)

revenue = (Mg * Flow / 1_000_000) * 2.5
profit = revenue - cost

col1.metric("Estimated Cost (OMR/day)", f"{cost:,.2f}")
col2.metric("Estimated Revenue (OMR/day)", f"{revenue:,.2f}")
col3.metric("Estimated Profit (OMR/day)", f"{profit:,.2f}")

# Probability Chart
st.subheader("Prediction Confidence")
fig, ax = plt.subplots()
ax.bar(["Skip","Magnesium","Calcium"], probs)
st.pyplot(fig)

st.markdown("---")
st.markdown("Developed by BrineX | Sustainable Engineering Solutions 🌱")
