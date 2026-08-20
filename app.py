import streamlit as st
import time
from core.agent import get_response, build_whatsapp_link
from core.rag import load_client_config
from core.conversation_log import get_or_create_session_id, log_message
from core.retention import clean_old_records

CLIENT_ID = "_template"

config = load_client_config(CLIENT_ID)
clean_old_records(CLIENT_ID, config)

st.set_page_config(
    page_title=config["practice_name"],
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded",
)

primary = config["branding"]["primary_color"]
secondary = config["branding"]["secondary_color"]

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: #f5f8fc; }}
    .app-title {{
        color: {primary};
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0;
    }}
    .app-subtitle {{
        color: #777;
        font-size: 0.95rem;
        margin-top: 0;
        margin-bottom: 1rem;
    }}
    div[data-testid="stChatMessage"] {{
        background-color: #ffffff;
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border: 1px solid #e3ebf5;
    }}
    div[data-testid="stChatMessage"] p {{
        color: #1a1a1a !important;
        font-size: 0.95rem;
    }}
    div.stButton > button {{
        background-color: white;
        color: {primary};
        border: 1px solid {primary};
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 0.9rem;
        margin-bottom: 4px;
    }}
    div.stButton > button:hover {{
        background-color: {primary};
        color: white;
    }}
    .footer-note {{
        color: #aaa;
        font-size: 0.72rem;
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 0.75rem;
        border-top: 1px solid #e3ebf5;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = None
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

session_id = get_or_create_session_id(st.session_state)


def reset_conversation():
    st.session_state.messages = []
    st.session_state.gemini_chat = None
    st.session_state.pending_question = None
    st.session_state.conversation_id = None


def trigger_quick_action(query: str):
    st.session_state.pending_question = query


def stream_text(text: str, placeholder):
    """Simulate a natural typing effect by revealing text progressively"""
    displayed = ""
    for word in text.split(" "):
        displayed += word + " "
        placeholder.markdown(displayed)
        time.sleep(0.02)


# --- Sidebar: Quick Actions, Booking link, WhatsApp ---
with st.sidebar:
    st.subheader("Quick Actions")
    st.caption("Tap a topic for an instant answer")
    for i, action in enumerate(config["quick_actions"]):
        if st.button(action["label"], use_container_width=True, key=f"qa_{i}", on_click=trigger_quick_action, args=(action["query"],)):
            pass

    if config["booking"]["enabled"]:
        st.divider()
        st.subheader("Book an Appointment")
        st.page_link("pages/1_Book_Appointment.py", label="Go to Booking Page", icon="📅")

    st.divider()
    st.subheader("Need a human?")
    wa_link = build_whatsapp_link(config["escalation"]["whatsapp_number"], config["practice_name"])
    st.markdown(f"[💬 Chat on WhatsApp]({wa_link})")

    st.divider()
    if st.button("Start New Conversation", use_container_width=True, key="reset_btn"):
        reset_conversation()
        st.rerun()

# --- Header ---
st.markdown(f"<div class='app-title'>{config['practice_name']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='app-subtitle'>{config['tagline']}</div>", unsafe_allow_html=True)

# --- Chat history ---
if not st.session_state.messages:
    st.caption("Ask a question below, or use Quick Actions / Book Now in the sidebar.")
    st.caption("💡 For your privacy: please avoid sharing sensitive medical details in this chat. Conversations may be reviewed by staff.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Input handling ---
typed_question = st.chat_input("Ask a question...")

question = st.session_state.pending_question or typed_question
st.session_state.pending_question = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    log_message(CLIENT_ID, session_id, "user", question)
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                result = get_response(CLIENT_ID, question, st.session_state)
                answer = result["response"]
            except Exception as e:
                answer = f"Sorry, something went wrong: {e}"
        stream_text(answer, placeholder)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    log_message(CLIENT_ID, session_id, "assistant", answer)
    st.rerun()

# --- Disclaimer footer ---
if config["compliance"]["popia_notice_enabled"]:
    st.markdown(
        f"<div class='footer-note'>{config['compliance']['disclaimer_text']}</div>",
        unsafe_allow_html=True,
    )