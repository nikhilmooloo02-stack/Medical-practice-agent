import streamlit as st
import pandas as pd
from pathlib import Path
from core.rag import load_client_config

CLIENT_ID = "_template"

config = load_client_config(CLIENT_ID)

st.set_page_config(page_title=f"Logs - {config['practice_name']}", layout="wide")

st.title("Conversation Logs")
st.caption(f"Internal view for {config['practice_name']} staff — not visible to patients.")

log_path = Path(f"clients/{CLIENT_ID}/conversation_log.csv")

if not log_path.exists():
    st.info("No conversations logged yet.")
else:
    df = pd.read_csv(log_path)
    st.write(f"Total messages logged: {len(df)}")
    st.write(f"Unique conversations: {df['conversation_id'].nunique()}")

    conversation_ids = df["conversation_id"].unique().tolist()
    selected = st.selectbox("View a specific conversation", ["All"] + conversation_ids)

    if selected != "All":
        df = df[df["conversation_id"] == selected]

    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download as CSV",
        data=df.to_csv(index=False),
        file_name=f"{CLIENT_ID}_conversation_log.csv",
        mime="text/csv",
    )