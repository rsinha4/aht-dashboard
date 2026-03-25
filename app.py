import streamlit as st
import pandas as pd

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="SDP Dashboard", layout="wide")

st.markdown(
    "<h1 style='text-align: center; font-size:36px;'>SDP Chats Performance Dashboard</h1>",
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

    # Use system/default color unless breached
    def get_color(seconds):
        if pd.isna(seconds):
            return "inherit"
        return "red" if seconds > 1050 else "inherit"

    def metric_card(title, value, seconds=None):
        color = get_color(seconds)
        return f"""
        <div style='border:1px solid #ddd; border-radius:10px; padding:15px; text-align:center;'>
            <div style='font-size:15px; color:gray;'>{title}</div>
            <div style='font-size:26px; font-weight:bold; color:{color};'>{value}</div>
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

    with g1:
        st.markdown(metric_card("C2P Chats", total_c2p), unsafe_allow_html=True)

    with g2:
        st.markdown(metric_card("C2P AHT (MM:SS)", format_time(c2p_aht), c2p_aht), unsafe_allow_html=True)

    with g3:
        st.markdown(metric_card("N2P Chats", total_n2p), unsafe_allow_html=True)

    with g4:
        st.markdown(metric_card("N2P AHT (MM:SS)", format_time(n2p_aht), n2p_aht), unsafe_allow_html=True)

    with g5:
        st.markdown(metric_card("Total Chats", total_chats), unsafe_allow_html=True)

    with g6:
        st.markdown(metric_card("Overall AHT (MM:SS)", format_time(overall_aht), overall_aht), unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- AGENT SUMMARY ----------------
    result = []
    agents = df[agent_col].dropna().unique()

    for agent in agents:
        agent_df = df[df[agent_col] == agent]

        c2p_df = agent_df[agent_df[queue_col] == "C2P"]
        n2p_df = agent_df[agent_df[queue_col] == "N2P"]

        c2p_aht = c2p_df[aht_col].mean()
        n2p_aht = n2p_df[aht_col].mean()
        total_aht = agent_df[aht_col].mean()

        result.append({
            "Agent": agent,
            "C2P Chats": len(c2p_df),
            "C2P AHT": format_time(c2p_aht),
            "N2P Chats": len(n2p_df),
            "N2P AHT": format_time(n2p_aht),
            "Total Chats": len(agent_df),
            "Total AHT": format_time(total_aht),
            "_c2p": c2p_aht,
            "_n2p": n2p_aht,
            "_total": total_aht
        })

    result_df = pd.DataFrame(result)

    # Keep original tabular display
    result_df_display = result_df.drop(columns=["_c2p", "_n2p", "_total"])

    st.subheader("👤 Agent Level Summary")
    st.dataframe(result_df_display, use_container_width=True)

    # ---------------- KPI SECTION ----------------
    st.markdown("---")
    st.subheader("📈 KPI Performance")

    df_kpi = df.copy()
    df_kpi["actual_response_time"] = df_kpi[response_col] - df_kpi[claim_col]

    total_kpi = len(df_kpi)

    claim_45 = (df_kpi[claim_col] <= 45).sum() / total_kpi * 100
    claim_120 = (df_kpi[claim_col] <= 120).sum() / total_kpi * 100
    claim_300 = (df_kpi[claim_col] <= 300).sum() / total_kpi * 100
    response_60 = (df_kpi["actual_response_time"] <= 60).sum() / total_kpi * 100

    # Handle Time KPI
    overall_time = overall_aht
    handle_status = "🟢 Met" if overall_time <= 1020 else "🔴 Missed"

    kpi_df = pd.DataFrame({
        "KPI": [
            "Claim Time ≤ 45 sec",
            "Claim Time ≤ 2 min",
            "Claim Time ≤ 5 min",
            "Response Time ≤ 60 sec",
            "Handle Time"
        ],
        "Actual": [
            f"{claim_45:.2f}%",
            f"{claim_120:.2f}%",
            f"{claim_300:.2f}%",
            f"{response_60:.2f}%",
            format_time(overall_time)
        ],
        "Target": ["80%", "80%", "100%", "99%", "17m 0s"],
        "Status": [
            "🟢 Met" if claim_45 >= 80 else "🔴 Missed",
            "🟢 Met" if claim_120 >= 80 else "🔴 Missed",
            "🟢 Met" if claim_300 >= 100 else "🔴 Missed",
            "🟢 Met" if response_60 >= 99 else "🔴 Missed",
            handle_status
        ]
    })

    st.dataframe(kpi_df, use_container_width=True)

else:
    st.info("Please upload both C2P and N2P files to proceed.")
