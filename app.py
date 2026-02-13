import streamlit as st
import pandas as pd
import datetime

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="BrineX Decision Support System",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Metrics
st.markdown("""
    <style>
    .big-font { font-size:24px !important; }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. BUSINESS LOGIC (CALCULATIONS)
# ==========================================
def calculate_metrics(tds, na, mg, ca, flow, location):
    # 1. Recovery Calculations (Mass Balance)
    # Conversion: mg/L * m3/day * (1000 L / 1 m3) * (1 kg / 1e6 mg) = kg/day
    # Simplified: (mg/L * m3/day) / 1000
    mg_rec_kg = (mg * flow) / 1000.0
    na_rec_kg = (na * flow) / 1000.0
    ca_rec_kg = (ca * flow) / 1000.0

    # 2. Economic Value (Estimated Market Rates)
    # Assumptions: Mg=$2.5/kg, Na=$0.12/kg, Ca=$0.08/kg
    val_mg = mg_rec_kg * 2.50
    val_na = na_rec_kg * 0.12
    val_ca = ca_rec_kg * 0.08
    total_val = val_mg + val_na + val_ca

    # 3. Environmental Score
    base_score = 100 - (tds / 1200)
    penalty = 15 if location == "High" else (8 if location == "Medium" else 0)
    env_score = max(0, int(base_score - penalty))

    # 4. Risk Level
    if env_score >= 75: risk_lvl = "Low Risk"
    elif env_score >= 45: risk_lvl = "Moderate Risk"
    else: risk_lvl = "High Risk"

    # 5. Salinity Reduction (Hypothetical Process Efficiency)
    sal_reduction = tds * 0.35  # 35% reduction assumption

    return {
        "mg_kg": mg_rec_kg, "na_kg": na_rec_kg, "ca_kg": ca_rec_kg,
        "val_mg": val_mg, "val_na": val_na, "val_ca": val_ca, "total_val": total_val,
        "env_score": env_score, "risk": risk_lvl, "sal_red": sal_reduction
    }

def get_recommendation(tds, mg, location):
    if tds > 80000:
        return "High Salinity: Evaporation & Salt Recovery System"
    elif mg > 1500:
        return "Magnesium Recovery via Chemical Precipitation"
    elif location == "High":
        return "Zero Liquid Discharge (ZLD)"
    else:
        return "Controlled Dilution with Diffuser System"

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/732/732205.png", width=50)
    st.title("BrineX Parameters")
    st.markdown("---")
    
    # Input Groups
    st.subheader("💧 Water Quality")
    in_tds = st.number_input("TDS (mg/L)", 0, 150000, 65000, step=500)
    in_na = st.number_input("Sodium - Na⁺ (mg/L)", 0, 60000, 22000, step=100)
    in_mg = st.number_input("Magnesium - Mg²⁺ (mg/L)", 0, 10000, 1800, step=50)
    in_ca = st.number_input("Calcium - Ca²⁺ (mg/L)", 0, 10000, 900, step=50)
    
    st.subheader("⚙️ Operations")
    in_flow = st.number_input("Flow Rate (m³/day)", 0, 600000, 120000, step=1000)
    in_loc = st.selectbox("Environmental Sensitivity", ["Low", "Medium", "High"])
    
    st.markdown("---")
    st.caption("v2.0 | Developed by BrineX Engineering")

# ==========================================
# 4. MAIN DASHBOARD
# ==========================================

# Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("Sustainable Brine Management System")
    st.markdown("#### **Decision Support & Techno-Economic Analysis**")
with col_h2:
    # Live Status Badge
    rec_strategy = get_recommendation(in_tds, in_mg, in_loc)
    st.info(f"**Strategy:**\n{rec_strategy}")

# Run Calculations
data = calculate_metrics(in_tds, in_na, in_mg, in_ca, in_flow, in_loc)

# Top Level KPI Row
st.markdown("### 📈 Daily Economic Performance")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Revenue Potential", f"${data['total_val']:,.0f}", delta="Daily")
kpi2.metric("Mg Recovery Value", f"${data['val_mg']:,.0f}", help="Based on $2.5/kg")
kpi3.metric("Na Recovery Value", f"${data['val_na']:,.0f}", help="Based on $0.12/kg")
kpi4.metric("Ca Recovery Value", f"${data['val_ca']:,.0f}", help="Based on $0.08/kg")

st.markdown("---")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["📊 Chemical Profile", "🌍 Environmental Impact", "📄 Report Generation"])

# --- TAB 1: CHEMICAL PROFILE ---
with tab1:
    col_t1_1, col_t1_2 = st.columns([1, 2])
    
    with col_t1_1:
        st.subheader("Mass Balance (kg/day)")
        st.markdown(f"""
        - **Magnesium**: {data['mg_kg']:,.0f} kg
        - **Sodium**: {data['na_kg']:,.0f} kg
        - **Calcium**: {data['ca_kg']:,.0f} kg
        """)
        st.caption("*Based on current flow rate and efficiency assumptions.*")
    
    with col_t1_2:
        st.subheader("Ion Concentration Analysis")
        # Native Streamlit Chart (Interactive)
        chart_df = pd.DataFrame({
            "Ion": ["Sodium (Na)", "Magnesium (Mg)", "Calcium (Ca)"],
            "Concentration (mg/L)": [in_na, in_mg, in_ca]
        }).set_index("Ion")
        
        st.bar_chart(chart_df, color="#0E5A8A", height=300)

# --- TAB 2: ENVIRONMENTAL IMPACT ---
with tab2:
    col_t2_1, col_t2_2 = st.columns(2)
    
    with col_t2_1:
        st.subheader("Sustainability Score")
        # Dynamic Color for Score
        score_color = "green" if data['env_score'] > 75 else ("orange" if data['env_score'] > 45 else "red")
        st.markdown(f"<h1 style='color:{score_color}'>{data['env_score']}/100</h1>", unsafe_allow_html=True)
        st.markdown(f"**Risk Level:** {data['risk']}")
        
        st.progress(data['env_score'] / 100)
    
    with col_t2_2:
        st.subheader("Salinity Reduction Impact")
        # Comparison Chart
        sal_df = pd.DataFrame({
            "Stage": ["Initial TDS", "Post-Treatment TDS"],
            "mg/L": [in_tds, in_tds - data['sal_red']]
        }).set_index("Stage")
        
        st.bar_chart(sal_df, color=["#FF4B4B", "#00CC96"][0]) # Uses default theme color

# --- TAB 3: REPORT ---
with tab3:
    st.subheader("📝 Project Executive Summary")
    
    report_text = f"""
    BRINEX SUSTAINABILITY REPORT
    ----------------------------
    Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    1. INPUT PARAMETERS
    - Flow Rate: {in_flow:,.0f} m3/day
    - Salinity (TDS): {in_tds} mg/L
    - Location Sensitivity: {in_loc}
    
    2. OPERATIONAL STRATEGY
    - Recommendation: {rec_strategy}
    - Risk Assessment: {data['risk']} (Score: {data['env_score']})
    
    3. ECONOMIC PROJECTION (DAILY)
    - Total Value: ${data['total_val']:,.2f}
    - Magnesium: ${data['val_mg']:,.2f} ({data['mg_kg']:,.0f} kg)
    - Sodium:    ${data['val_na']:,.2f} ({data['na_kg']:,.0f} kg)
    - Calcium:   ${data['val_ca']:,.2f} ({data['ca_kg']:,.0f} kg)
    
    ----------------------------
    Generated by BrineX Decision Support System
    """
    
    st.text_area("Preview", report_text, height=300)
    
    st.download_button(
        label="📥 Download Official Report",
        data=report_text,
        file_name=f"BrineX_Report_{datetime.date.today()}.txt",
        mime="text/plain"
    )
