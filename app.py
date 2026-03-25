import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="SDP Dashboard", layout="wide")

st.markdown(
    """
    <style>
    body {font-family: 'Segoe UI', sans-serif;}
    .title {
        text-align:center;
        font-size:36px;
        font-weight:600;
        margin-bottom:10px;
    }
    .card {
        border:1px solid #e6e6e6;
        border-radius:12px;
        padding:16px;
        text-align:center;
        box-shadow:0 2px 6px rgba(0,0,0,0.05);
    }
    .card-title {
        font-size:13px;
        color:#6c757d;
    }
    .card-value {
        font-size:26px;
        font-weight:600;
        margin-top:5px;
    }
    .card-sub {
        font-size:12px;
        color:#6c757d;
    }
    </style>
    <div class="title">SDP Chats Performance Dashboard</div>
    """,
    unsafe_allow_html=True
)

# ---------------- FILE UPLOAD ----------------
col1, col2 = st.columns(2)

with col1:
    c2p_file = st.file_uploader("Upload C2P File", type=["xlsx"])

with col2:
    n2p_file = st.file_uploader("Upload N2P File", type=["xlsx"])

if c2p_file is not None and n2p_file is not None:

    df_c2p = pd.read_excel(c2p_file)
    df_n2p = pd.read_excel(n2p_file)

    df_c2p["Queue"] = "C2P"
    df_n2p["Queue"] = "N2P"

    df = pd.concat([df_c2p, df_n2p], ignore_index=True)

    date_col = "start_time"
    aht_col = "handle_time"
    agent_col = "final_staffer"
    response_col = "response_time"
    claim_col = "claim_time"
    queue_col = "Queue"

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[aht_col] = pd.to_numeric(df[aht_col], errors="coerce")
    df[response_col] = pd.to_numeric(df[response_col], errors="coerce")
    df[claim_col] = pd.to_numeric(df[claim_col], errors="coerce")

    df = df.dropna(subset=[date_col, aht_col, agent_col])

    # ---------------- DATE FILTER ----------------
    st.markdown("### 📅 Select Date Range")

    d1, d2 = st.columns(2)

    min_date = df[date_col].min().date()
    max_date = df[date_col].max().date()

    with d1:
        start_date = st.date_input("Start Date", min_date)

    with d2:
        end_date = st.date_input("End Date", max_date)

    df = df[
        (df[date_col].dt.date >= start_date) &
        (df[date_col].dt.date <= end_date)
    ]

    # ---------------- HELPERS ----------------
    def format_time(seconds):
        if pd.isna(seconds):
            return "0m 0s"
        seconds = int(seconds)
        return f"{seconds//60}m {seconds%60}s"

    def get_color(seconds):
        if pd.isna(seconds):
            return "inherit"
        return "red" if seconds > 1050 else "green"

    def metric_card(title, value, color="black", subtitle=""):
        return f"""
        <div class="card">
            <div class="card-title">{title}</div>
            <div class="card-value" style="color:{color};">{value}</div>
            <div class="card-sub">{subtitle}</div>
        </div>
        """

    # ---------------- OVERALL PERFORMANCE ----------------
    st.markdown("## 📊 Overall Performance")

    total_c2p = len(df[df[queue_col] == "C2P"])
    total_n2p = len(df[df[queue_col] == "N2P"])
    total_chats = len(df)

    c2p_aht = df[df[queue_col] == "C2P"][aht_col].mean()
    n2p_aht = df[df[queue_col] == "N2P"][aht_col].mean()
    overall_aht = df[aht_col].mean()

    g1, g2, g3, g4, g5, g6 = st.columns(6)

    g1.markdown(metric_card("C2P Chats", total_c2p), unsafe_allow_html=True)
    g2.markdown(metric_card("C2P AHT", format_time(c2p_aht), get_color(c2p_aht)), unsafe_allow_html=True)
    g3.markdown(metric_card("N2P Chats", total_n2p), unsafe_allow_html=True)
    g4.markdown(metric_card("N2P AHT", format_time(n2p_aht), get_color(n2p_aht)), unsafe_allow_html=True)
    g5.markdown(metric_card("Total Chats", total_chats), unsafe_allow_html=True)
    g6.markdown(metric_card("Overall AHT", format_time(overall_aht), get_color(overall_aht)), unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- AGENT SUMMARY ----------------
    result = []
    agents = df[agent_col].dropna().unique()

    for agent in agents:
        agent_df = df[df[agent_col] == agent]

        c2p_df = agent_df[agent_df[queue_col] == "C2P"]
        n2p_df = agent_df[agent_df[queue_col] == "N2P"]

        total_aht_val = agent_df[aht_col].mean()

        result.append({
            "Agent": agent,
            "C2P Chats": len(c2p_df),
            "C2P AHT": format_time(c2p_df[aht_col].mean()),
            "N2P Chats": len(n2p_df),
            "N2P AHT": format_time(n2p_df[aht_col].mean()),
            "Total Chats": len(agent_df),
            "Total AHT": format_time(total_aht_val),
            "Total AHT Seconds": total_aht_val
        })

    result_df = pd.DataFrame(result)

    # Sort by highest AHT
    result_df = result_df.sort_values(by="Total AHT Seconds", ascending=False).reset_index(drop=True)

    st.subheader("👤 Agent Level Summary")

    # Highlight Total AHT column only
    def highlight_aht(val):
        if pd.isna(val):
            return ""
        return "background-color: #ffe6e6" if val > 1050 else "background-color: #e6ffe6"

    styled_df = result_df.style.applymap(highlight_aht, subset=["Total AHT Seconds"])

    styled_html = f"""
    <style>
    table {{
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', sans-serif;
    }}
    th, td {{
        border: 1px solid #e6e6e6;
        padding: 10px;
        text-align: center;
    }}
    th {{
        background-color: #f5f7fa;
        font-weight:600;
    }}
    tr:nth-child(even) {{
        background-color: #fafafa;
    }}
    </style>
    {styled_df.hide(axis="columns", subset=["Total AHT Seconds"]).to_html(index=False)}
    """

    components.html(styled_html, height=600, scrolling=True)

    # ---------------- KPI CARDS ----------------
    st.markdown("---")
    st.subheader("📈 KPI Performance")

    df_kpi = df.copy()
    df_kpi["actual_response_time"] = df_kpi[response_col] - df_kpi[claim_col]

    claim_45 = (df_kpi[claim_col] <= 45).mean() * 100
    claim_120 = (df_kpi[claim_col] <= 120).mean() * 100
    claim_300 = (df_kpi[claim_col] <= 300).mean() * 100
    response_60 = (df_kpi["actual_response_time"] <= 60).mean() * 100
    overall_time = overall_aht

    kpi_status = {
        "Claim ≤45s": claim_45 >= 80,
        "Claim ≤2m": claim_120 >= 80,
        "Claim ≤5m": claim_300 >= 100,
        "Response ≤60s": response_60 >= 99,
        "Handle Time": overall_time <= 1020
    }

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.markdown(metric_card("Claim ≤45s", f"{claim_45:.1f}%", "green" if kpi_status["Claim ≤45s"] else "red", "Target: 80%"), unsafe_allow_html=True)
    k2.markdown(metric_card("Claim ≤2m", f"{claim_120:.1f}%", "green" if kpi_status["Claim ≤2m"] else "red", "Target: 80%"), unsafe_allow_html=True)
    k3.markdown(metric_card("Claim ≤5m", f"{claim_300:.1f}%", "green" if kpi_status["Claim ≤5m"] else "red", "Target: 100%"), unsafe_allow_html=True)
    k4.markdown(metric_card("Response ≤60s", f"{response_60:.1f}%", "green" if kpi_status["Response ≤60s"] else "red", "Target: 99%"), unsafe_allow_html=True)
    k5.markdown(metric_card("Handle Time", format_time(overall_time), "green" if kpi_status["Handle Time"] else "red", "Target: 17m"), unsafe_allow_html=True)

    # ---------------- KPI NOTE ----------------
    st.markdown("<br>", unsafe_allow_html=True)

    missed_kpis = [k for k, v in kpi_status.items() if not v]

    if len(missed_kpis) == 0:
        st.success("✅ All KPIs are in Green. Team has met all the targets.")
    else:
        missed_text = ", ".join(missed_kpis)
        st.error(f"⚠️ The following KPIs were missed: {missed_text}")

else:
    st.info("Please upload both C2P and N2P files to proceed.")
