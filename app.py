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

# Custom CSS for Professional Styling
st.markdown("""
    <style>
    .big-font { font-size:24px !important; }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Explanation Box (Blue) */
    .explanation-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #1976d2;
        font-size: 14px;
        margin-top: 15px;
        color: #0d47a1;
    }
    
    /* Verdict Box (Dynamic Colors) */
    .verdict-box {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. BUSINESS LOGIC (CALCULATIONS)
# ==========================================
def calculate_metrics(tds, na, mg, ca, flow, location):
    # 1. Recovery Calculations (Mass Balance)
    # Formula: (mg/L * m3/day) / 1000 = kg/day
    mg_rec_kg = (mg * flow) / 1000.0
    na_rec_kg = (na * flow) / 1000.0
    ca_rec_kg = (ca * flow) / 1000.0

    # 2. Economic Value (Revenue)
    # Market Assumptions: Mg=$2.5/kg, Na=$0.12/kg, Ca=$0.08/kg
    val_mg = mg_rec_kg * 2.50
    val_na = na_rec_kg * 0.12
    val_ca = ca_rec_kg * 0.08
    total_revenue = val_mg + val_na + val_ca
    
    # 3. Profit Estimation
    # Engineering Assumption: OpEx is approx 60% of Revenue for this tech
    est_opex = total_revenue * 0.60
    est_profit = total_revenue - est_opex

    # 4. Sustainability Score Calculation
    # Baseline: 100
    # Salinity Penalty: -1 point per 1200 mg/L
    base_deduction = tds / 1200
    # Location Penalty: High(-15), Medium(-8), Low(0)
    loc_penalty = 15 if location == "High" else (8 if location == "Medium" else 0)
    
    raw_score = 100 - base_deduction - loc_penalty
    env_score = max(0, int(raw_score))

    # 5. Risk Level
    if env_score >= 75: risk_lvl = "Low Risk"
    elif env_score >= 45: risk_lvl = "Moderate Risk"
    else: risk_lvl = "High Risk"

    # 6. Salinity Reduction (Hypothetical 35% efficiency)
    sal_reduction = tds * 0.35 

    return {
        "mg_kg": mg_rec_kg, "na_kg": na_rec_kg, "ca_kg": ca_rec_kg,
        "val_mg": val_mg, "val_na": val_na, "val_ca": val_ca, 
        "total_revenue": total_revenue, "est_profit": est_profit,
        "env_score": env_score, "risk": risk_lvl, "sal_red": sal_reduction,
        "loc_penalty": loc_penalty
    }

def get_viability_verdict(score, profit):
    """
    Decides if the project is worth it based on Profit vs. Environment.
    Returns: (Title, Description, BackgroundColor, TextColor)
    """
    # Threshold: Minimum $500/day profit to be "Viable"
    PROFIT_THRESHOLD = 500 
    
    if score >= 75 and profit > PROFIT_THRESHOLD:
        return (
            "🌟 HIGHLY VIABLE", 
            "Excellent Balance: The project is **highly profitable** and **environmentally safe**. Highly recommended.", 
            "#d4edda", "#155724"  # Green
        )
    elif score < 45:
        return (
            "⛔ NOT RECOMMENDED", 
            "Critical Risk: The **environmental impact is too high** (Score < 45). Viability is rejected regardless of profit.", 
            "#f8d7da", "#721c24"  # Red
        )
    elif profit < PROFIT_THRESHOLD:
        return (
            "⚠️ MARGINAL VIABILITY", 
            "Financial Risk: Environmental score is good, but **profitability is low**. Requires subsidies or optimization.", 
            "#fff3cd", "#856404"  # Yellow
        )
    else:
        return (
            "⚖️ PROCEED WITH CAUTION", 
            "Mixed Outlook: Profitable, but **environmental risks exist** (Score 45-75). Strict monitoring required.", 
            "#e2e3e5", "#383d41"  # Grey
        )

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
    
    st.subheader("💧 Water Quality")
    in_tds = st.number_input("TDS (mg/L)", 0, 150000, 65000, step=500, help="Total Dissolved Solids")
    in_na = st.number_input("Sodium - Na⁺ (mg/L)", 0, 60000, 22000, step=100)
    in_mg = st.number_input("Magnesium - Mg²⁺ (mg/L)", 0, 10000, 1800, step=50)
    in_ca = st.number_input("Calcium - Ca²⁺ (mg/L)", 0, 10000, 900, step=50)
    
    st.subheader("⚙️ Operations")
    in_flow = st.number_input("Flow Rate (m³/day)", 0, 600000, 120000, step=1000)
    in_loc = st.selectbox("Environmental Sensitivity", ["Low", "Medium", "High"], help="Sensitivity of discharge location")
    
    st.markdown("---")
    st.caption("v3.0 | Developed by BrineX Engineering")

# ==========================================
# 4. MAIN DASHBOARD
# ==========================================

# Run Calculations
data = calculate_metrics(in_tds, in_na, in_mg, in_ca, in_flow, in_loc)
rec_strategy = get_recommendation(in_tds, in_mg, in_loc)
verdict_title, verdict_desc, bg_color, text_color = get_viability_verdict(data['env_score'], data['est_profit'])

# Header
st.title("Sustainable Brine Management System")
st.markdown("#### **Decision Support & Techno-Economic Analysis**")

# --- VIABILITY VERDICT SECTION ---
st.markdown(f"""
    <div class="verdict-box" style="background-color: {bg_color}; color: {text_color};">
        <h2 style="margin:0;">{verdict_title}</h2>
        <p style="margin-top:10px; font-size:18px; font-weight:500;">{verdict_desc}</p>
    </div>
""", unsafe_allow_html=True)

# KPI Row
st.markdown("### 📈 Economic Outlook (Daily Estimates)")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Revenue Potential", f"${data['total_revenue']:,.0f}")
k2.metric("OpEx Estimate (60%)", f"${data['total_revenue']*0.6:,.0f}", delta="-Cost", delta_color="inverse")
k3.metric("Net Profit", f"${data['est_profit']:,.0f}", help="Revenue - OpEx")
k4.metric("Strategy", rec_strategy.split(":")[0])

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Chemical Profile", "🌍 Environmental Impact", "📄 Report Generation"])

# --- TAB 1: CHEMICAL PROFILE ---
with tab1:
    col_t1_1, col_t1_2 = st.columns([1, 2])
    
    with col_t1_1:
        st.subheader("Mass Balance (kg/day)")
        st.markdown(f"""
        **Recovery Potential:**
        - 🔵 **Magnesium**: {data['mg_kg']:,.0f} kg
        - ⚪ **Sodium**: {data['na_kg']:,.0f} kg
        - 🟤 **Calcium**: {data['ca_kg']:,.0f} kg
        """)
        st.info("Calculated based on 100% theoretical recovery efficiency.")
    
    with col_t1_2:
        st.subheader("Ion Concentration")
        # Interactive Chart
        chart_df = pd.DataFrame({
            "Ion": ["Sodium (Na)", "Magnesium (Mg)", "Calcium (Ca)"],
            "Concentration (mg/L)": [in_na, in_mg, in_ca]
        }).set_index("Ion")
        st.bar_chart(chart_df, color="#0E5A8A", height=320)

# --- TAB 2: ENVIRONMENTAL IMPACT ---
with tab2:
    col_t2_1, col_t2_2 = st.columns(2)
    
    with col_t2_1:
        st.subheader("Sustainability Score")
        
        # Large Score Display
        score_color = "green" if data['env_score'] > 75 else ("orange" if data['env_score'] > 45 else "red")
        st.markdown(f"<h1 style='color:{score_color}; font-size: 48px; margin-bottom:0;'>{data['env_score']}/100</h1>", unsafe_allow_html=True)
        st.markdown(f"**Risk Level:** {data['risk']}")
        st.progress(data['env_score'] / 100)
        
        # Explanation Box
        st.markdown(f"""
        <div class="explanation-box">
        <b>ℹ️ How is this calculated?</b><br>
        This index represents the environmental safety of the brine discharge.<br>
        <ul style="margin-top:5px;">
            <li><b>Baseline:</b> 100 points (Perfect).</li>
            <li><b>Salinity Penalty:</b> -{int(in_tds/1200)} points (based on {in_tds} mg/L TDS).</li>
            <li><b>Location Penalty:</b> -{data['loc_penalty']} points (Location: {in_loc}).</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_t2_2:
        st.subheader("Salinity Reduction Impact")
        sal_df = pd.DataFrame({
            "Stage": ["Initial TDS", "Post-Treatment TDS"],
            "mg/L": [in_tds, in_tds - data['sal_red']]
        }).set_index("Stage")
        st.bar_chart(sal_df, color=["#FF4B4B", "#00CC96"][0])

# --- TAB 3: REPORT ---
with tab3:
    st.subheader("📝 Executive Report")
    
    report_text = f"""
    BRINEX DECISION SUPPORT REPORT
    ------------------------------------------------
    Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    1. VIABILITY VERDICT
    --------------------
    Status: {verdict_title.strip()}
    Reason: {verdict_desc}
    
    2. FINANCIAL PROJECTION (DAILY)
    --------------------
    - Total Revenue:    ${data['total_revenue']:,.2f}
    - Est. OpEx (60%):  ${data['total_revenue']*0.6:,.2f}
    - Est. Net Profit:  ${data['est_profit']:,.2f}
    
    3. ENVIRONMENTAL PROFILE
    --------------------
    - Sustainability Score: {data['env_score']}/100 ({data['risk']})
    - Discharge Location:   {in_loc} (-{data['loc_penalty']} pts)
    - TDS Level:            {in_tds} mg/L
    
    4. TECHNICAL PARAMETERS
    --------------------
    - Flow Rate: {in_flow:,.0f} m3/day
    - Recommended Strategy: {rec_strategy}
    
    ------------------------------------------------
    Generated by BrineX System
    """
    
    st.text_area("Report Preview", report_text, height=350)
    
    st.download_button(
        label="📥 Download Official Report (TXT)",
        data=report_text,
        file_name=f"BrineX_Report_{datetime.date.today()}.txt",
        mime="text/plain"
    )
