import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

from utils.ml_model import train_model, predict
from utils.economics import calculate_revenue, calculate_profit
from utils.sustainability import environmental_score, risk_level

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="BrineX Professional Platform",
    layout="wide"
)

st.title("🌊 BrineX – AI Sustainable Brine Management Platform")
st.markdown("Advanced ML + Economic + Environmental Decision Support")
st.markdown("---")

# ---------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------
@st.cache_resource
def load_model():
    return train_model()

W, mu, sigma, wR = load_model()

# ---------------------------------------------------
# SIDEBAR INPUTS
# ---------------------------------------------------
st.sidebar.header("Plant Operating Conditions")

Mg = st.sidebar.number_input("Mg (mg/L)", 0, 5000, 1800)
Ca = st.sidebar.number_input("Ca (mg/L)", 0, 5000, 900)
TDS = st.sidebar.number_input("Salinity (mg/L)", 0, 120000, 65000)
Temp = st.sidebar.number_input("Temperature (°C)", 0, 60, 30)
Flow = st.sidebar.number_input("Flow (m³/day)", 0, 500000, 100000)

sensitivity = st.sidebar.selectbox(
    "Environmental Sensitivity",
    ["Low", "Medium", "High"]
)

# ---------------------------------------------------
# MODEL PREDICTION
# ---------------------------------------------------
x = np.array([[Mg, Ca, TDS, Temp, Flow]])
mode, probs, cost = predict(x, W, mu, sigma, wR)

revenue = calculate_revenue(Mg, Flow)
profit = calculate_profit(revenue, cost)

score = environmental_score(TDS, sensitivity)
risk = risk_level(score)

# ---------------------------------------------------
# EXECUTIVE DASHBOARD
# ---------------------------------------------------
st.subheader("Executive Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Recommended Strategy", mode)
col2.metric("Daily Cost (OMR)", f"{cost:,.2f}")
col3.metric("Daily Revenue (OMR)", f"{revenue:,.2f}")
col4.metric("Daily Profit (OMR)", f"{profit:,.2f}")

st.markdown("---")

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    ["📊 AI Confidence", "🌱 Sustainability", "📂 Batch Processing"]
)

# ---------------------------------------------------
# TAB 1 – AI CONFIDENCE (Plotly)
# ---------------------------------------------------
with tab1:
    df_probs = pd.DataFrame({
        "Mode": ["Skip", "Magnesium", "Calcium"],
        "Probability": probs
    })

    fig = px.bar(
        df_probs,
        x="Mode",
        y="Probability",
        color="Mode",
        title="AI Prediction Confidence",
        text_auto=True
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# TAB 2 – SUSTAINABILITY
# ---------------------------------------------------
with tab2:
    st.metric("Environmental Score", f"{score}/100")
    st.write(f"Risk Classification: **{risk}**")

    df_env = pd.DataFrame({
        "Category": ["Environmental Score"],
        "Value": [score]
    })

    fig2 = px.bar(
        df_env,
        x="Category",
        y="Value",
        text_auto=True,
        title="Sustainability Index"
    )

    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------
# TAB 3 – BATCH PROCESSING
# ---------------------------------------------------
with tab3:
    uploaded_file = st.file_uploader("Upload CSV for Batch Analysis")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        results = []

        for _, row in df.iterrows():
            x = np.array([[row["Mg_mgL"],
                           row["Ca_mgL"],
                           row["Salinity_mgL"],
                           row["Temp_C"],
                           row["Flow_m3_day"]]])

            mode, _, cost = predict(x, W, mu, sigma, wR)
            revenue = calculate_revenue(row["Mg_mgL"],
                                        row["Flow_m3_day"])
            profit = calculate_profit(revenue, cost)

            results.append([mode, cost, revenue, profit])

        df["Mode"] = [r[0] for r in results]
        df["Cost"] = [r[1] for r in results]
        df["Revenue"] = [r[2] for r in results]
        df["Profit"] = [r[3] for r in results]

        st.dataframe(df, use_container_width=True)

        fig_batch = px.histogram(
            df,
            x="Mode",
            title="Batch Mode Distribution"
        )

        st.plotly_chart(fig_batch, use_container_width=True)

        st.download_button(
            "Download Batch Results",
            df.to_csv(index=False),
            "BrineX_Batch_Results.csv"
        )

st.markdown("---")
st.markdown("BrineX Professional Platform | AI + Sustainability + Chemical Engineering 🌱")
