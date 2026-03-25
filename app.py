import streamlit as st
import pandas as pd

st.set_page_config(page_title="SDP Dashboard", layout="wide")
st.title("📊 SDP Chat Dashboard (C2P + N2P + KPI)")

c2p_file = st.file_uploader("Upload C2P File", type=["xlsx"])
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

    min_date = df[date_col].min().date()
    max_date = df[date_col].max().date()

    st.subheader("📅 Select Date Range")
    start_date = st.date_input("Start Date", min_date)
    end_date = st.date_input("End Date", max_date)

    df = df[
        (df[date_col].dt.date >= start_date) &
        (df[date_col].dt.date <= end_date)
    ]

    result = []
    agents = df[agent_col].dropna().unique()

    for agent in agents:
        agent_df = df[df[agent_col] == agent]

        c2p_df = agent_df[agent_df[queue_col] == "C2P"]
        n2p_df = agent_df[agent_df[queue_col] == "N2P"]

        c2p_count = len(c2p_df)
        n2p_count = len(n2p_df)

        c2p_aht = c2p_df[aht_col].mean() if c2p_count > 0 else 0
        n2p_aht = n2p_df[aht_col].mean() if n2p_count > 0 else 0

        total_count = c2p_count + n2p_count
        total_aht = agent_df[aht_col].mean() if total_count > 0 else 0

        result.append({
            "Agent": agent,
            "C2P Chats": c2p_count,
            "C2P AHT (sec)": round(c2p_aht, 2),
            "N2P Chats": n2p_count,
            "N2P AHT (sec)": round(n2p_aht, 2),
            "Total Chats": total_count,
            "Total AHT (sec)": round(total_aht, 2),
            "Total AHT (min)": round(total_aht / 60, 2)
        })

    result_df = pd.DataFrame(result)

    st.subheader("👤 Agent Level Summary")
    st.dataframe(result_df, use_container_width=True)

    st.subheader("📊 Grand Total")

    total_c2p = len(df[df[queue_col] == "C2P"])
    total_n2p = len(df[df[queue_col] == "N2P"])

    c2p_aht = df[df[queue_col] == "C2P"][aht_col].mean()
    n2p_aht = df[df[queue_col] == "N2P"][aht_col].mean()

    total_chats = len(df)
    overall_aht = df[aht_col].mean()

    col1, col2, col3 = st.columns(3)

    col1.metric("C2P Chats", total_c2p)
    col1.metric("C2P AHT (sec)", round(c2p_aht, 2) if pd.notna(c2p_aht) else 0)

    col2.metric("N2P Chats", total_n2p)
    col2.metric("N2P AHT (sec)", round(n2p_aht, 2) if pd.notna(n2p_aht) else 0)

    col3.metric("Total Chats", total_chats)
    col3.metric("Overall AHT (sec)", round(overall_aht, 2) if pd.notna(overall_aht) else 0)
    col3.metric("Overall AHT (min)", round(overall_aht / 60, 2) if pd.notna(overall_aht) else 0)

    # KPI SECTION
    st.subheader("📈 KPI Performance")

    df_kpi = df.copy()
    df_kpi[response_col] = pd.to_numeric(df_kpi[response_col], errors="coerce")
    df_kpi[claim_col] = pd.to_numeric(df_kpi[claim_col], errors="coerce")
    df_kpi[aht_col] = pd.to_numeric(df_kpi[aht_col], errors="coerce")

    df_kpi["actual_response_time"] = df_kpi[response_col] - df_kpi[claim_col]
    df_kpi = df_kpi.dropna(subset=[claim_col, response_col, aht_col, "actual_response_time"])

    total_kpi = len(df_kpi)

    if total_kpi > 0:
        claim_45 = (df_kpi[claim_col] <= 45).sum() / total_kpi * 100
        claim_120 = (df_kpi[claim_col] <= 120).sum() / total_kpi * 100
        claim_300 = (df_kpi[claim_col] <= 300).sum() / total_kpi * 100
        response_60 = (df_kpi["actual_response_time"] <= 60).sum() / total_kpi * 100
        handle_17 = (df_kpi[aht_col] <= 1020).sum() / total_kpi * 100

        kpi_table = pd.DataFrame({
            "KPI": [
                "Claim Time ≤ 45 sec",
                "Claim Time ≤ 2 min",
                "Claim Time ≤ 5 min",
                "Response Time ≤ 60 sec",
                "Handle Time ≤ 17 min"
            ],
            "Actual %": [
                f"{claim_45:.2f}%",
                f"{claim_120:.2f}%",
                f"{claim_300:.2f}%",
                f"{response_60:.2f}%",
                f"{handle_17:.2f}%"
            ],
            "Target %": [
                "80.00%",
                "80.00%",
                "100.00%",
                "99.00%",
                "100.00%"
            ],
            "Status": [
                "🟢 Met" if claim_45 >= 80 else "🔴 Missed",
                "🟢 Met" if claim_120 >= 80 else "🔴 Missed",
                "🟢 Met" if claim_300 >= 100 else "🔴 Missed",
                "🟢 Met" if response_60 >= 99 else "🔴 Missed",
                "🟢 Met" if handle_17 >= 100 else "🔴 Missed"
            ]
        })

        st.dataframe(kpi_table, use_container_width=True)

        with st.expander("See response time calculation sample"):
            st.dataframe(
                df_kpi[[claim_col, response_col, "actual_response_time"]].head(20),
                use_container_width=True
            )
    else:
        st.warning("No KPI data available after filtering.")

else:
    st.info("Please upload both C2P and N2P files to proceed.")