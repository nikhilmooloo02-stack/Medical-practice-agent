import streamlit as st
import time
from core.agent import get_response, build_whatsapp_link
from core.rag import load_client_config
from core.conversation_log import get_or_create_session_id, log_message
from core.retention import clean_old_records

CLIENT_ID = "_template"
MAX_MESSAGE_LENGTH = 500

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

# --- Theme state ---
if "theme" not in st.session_state:
    st.session_state.theme = "light"

is_dark = st.session_state.theme == "dark"

if is_dark:
    bg_color = "#0e1117"
    card_bg = "#1c1f26"
    card_border = "#2c2f38"
    text_color = "#f0f0f0"
    subtitle_color = "#aaa"
    footer_color = "#777"
    button_bg = "#1c1f26"
    button_text = secondary
    button_hover_bg = secondary
    button_hover_text = "#0e1117"
else:
    bg_color = "#f5f8fc"
    card_bg = "#ffffff"
    card_border = "#e3ebf5"
    text_color = "#1a1a1a"
    subtitle_color = "#777"
    footer_color = "#aaa"
    button_bg = "#ffffff"
    button_text = primary
    button_hover_bg = primary
    button_hover_text = "#ffffff"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .app-title {{
        color: {primary};
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0;
    }}
    .app-subtitle {{
        color: {subtitle_color};
        font-size: 0.95rem;
        margin-top: 0;
        margin-bottom: 1rem;
    }}
    div[data-testid="stChatMessage"] {{
        background-color: {card_bg};
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border: 1px solid {card_border};
    }}
    div[data-testid="stChatMessage"] p {{
        color: {text_color} !important;
        font-size: 0.95rem;
    }}
    div.stButton > button {{
        background-color: {button_bg};
        color: {button_text};
        border: 1px solid {primary if not is_dark else secondary};
        border-radius: 10px;
        padding: 8px 12px;
        font-size: 0.9rem;
        margin-bottom: 4px;
    }}
    div.stButton > button:hover {{
        background-color: {button_hover_bg};
        color: {button_hover_text};
    }}
    .footer-note {{
        color: {footer_color};
        font-size: 0.72rem;
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 0.75rem;
        border-top: 1px solid {card_border};
    }}
    div[data-testid="stChatInput"] {{
        position: sticky;
        bottom: 0;
        z-index: 999;
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


def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"


def stream_text(text: str, placeholder, batch_size: int = 3):
    """Reveal text in small batches of words instead of one at a time — smoother and lighter on mobile"""
    words = text.split(" ")
    displayed = ""
    for i in range(0, len(words), batch_size):
        chunk = " ".join(words[i:i + batch_size])
        displayed += chunk + " "
        placeholder.markdown(displayed)
        time.sleep(0.04)


# --- Sidebar: Theme toggle, Quick Actions, Booking link, WhatsApp ---
with st.sidebar:
    theme_label = "🌙 Switch to Dark Mode" if not is_dark else "☀️ Switch to Light Mode"
    st.button(theme_label, use_container_width=True, on_click=toggle_theme, key="theme_toggle")

    st.divider()
    st.subheader("Quick Actions")
    st.caption("Tap a topic for an instant answer")
    for i, action in enumerate(config["quick_actions"]):
        st.button(
            action["label"],
            use_container_width=True,
            key=f"qa_{i}",
            on_click=trigger_quick_action,
            args=(action["query"],),
        )

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

# --- Special notice banner ---
if config.get("special_notice"):
    st.warning(config["special_notice"])

# --- Chat history ---
if not st.session_state.messages:
    st.info(
        f"👋 Welcome! I'm the virtual