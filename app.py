import streamlit as st
from core.agent import get_response, build_whatsapp_link
from core.rag import load_client_config
from core.bookings import save_booking
from core.notifications import send_booking_notification

CLIENT_ID = "_template"

config = load_client_config(CLIENT_ID)

st.set_page_config(page_title=config["practice_name"], layout="centered", initial_sidebar_state="expanded")

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
    div.stFormSubmitButton > button {{
        background-color: {primary};
        color: white;
        border-radius: 10px;
        border: none;
    }}
    .panel-box {{
        background-color: #ffffff;
        border: 1px solid #e3ebf5;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 1rem;
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
if "show_booking_form" not in st.session_state:
    st.session_state.show_booking_form = False


def reset_conversation():
    st.session_state.messages = []
    st.session_state.gemini_chat = None
    st.session_state.pending_question = None
    st.session_state.show_booking_form = False


# --- Sidebar: Quick Actions, Booking, WhatsApp ---
with st.sidebar:
    st.subheader("Quick Actions")
    st.caption("Tap a topic for an instant answer")
    for i, action in enumerate(config["quick_actions"]):
        if st.button(action["label"], use_container_width=True, key=f"qa_{i}"):
            st.session_state.pending_question = action["query"]

    if config["booking"]["enabled"]:
        st.divider()
        st.subheader("Book an Appointment")
        if st.button("Book Now", use_container_width=True, key="book_now_btn"):
            st.session_state.show_booking_form = True

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

# --- Booking form panel ---
if st.session_state.show_booking_form:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.write("### Book Your Appointment")
    st.caption("Fill in the details below and our team will confirm your booking shortly.")

    with st.form("booking_form"):
        name = st.text_input(
            "Full name",
            placeholder="e.g. Jane Dlamini",
            help="Enter your first and last name so we know who's booking.",
        )
        phone = st.text_input(
            "Phone number",
            placeholder="e.g. 082 123 4567",
            help="We'll use this number to confirm your appointment.",
        )
        service = st.selectbox(
            "Which service would you like to book?",
            config["booking"]["services_offered"],
            help="Select the service you're interested in.",
        )
        preferred_date = st.date_input(
            "Preferred date",
            help="Choose your preferred appointment date. This is a request, not a confirmed slot yet.",
        )
        preferred_time = st.time_input(
            "Preferred time",
            help="Choose your preferred time. We'll confirm actual availability with you.",
        )
        notes = st.text_area(
            "Anything else we should know? (optional)",
            placeholder="e.g. first-time visit, specific concern, accessibility needs",
            help="Optional — add any extra info that would help the practice prepare for your visit.",
        )

        submitted = st.form_submit_button("Confirm Booking")
        if submitted:
            if not name or not phone:
                st.error("Please provide at least your name and phone number.")
            else:
                booking_data = {
                    "name": name,
                    "phone": phone,
                    "service": service,
                    "preferred_date": str(preferred_date),
                    "preferred_time": str(preferred_time),
                    "notes": notes,
                }
                save_booking(CLIENT_ID, booking_data)
                send_booking_notification(config, booking_data)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Booking received for {name} — {service} on {preferred_date} at {preferred_time}. We'll confirm shortly!"
                })
                st.session_state.show_booking_form = False
                st.rerun()

    if st.button("Cancel", key="cancel_booking"):
        st.session_state.show_booking_form = False
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- Chat history ---
if not st.session_state.messages:
    st.caption("Ask a question below, or use Quick Actions / Book Now in the sidebar (top-left arrow).")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Input handling ---
typed_question = st.chat_input("Ask a question...")

question = st.session_state.pending_question or typed_question
st.session_state.pending_question = None

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = get_response(CLIENT_ID, question, st.session_state)
                answer = result["response"]
            except Exception as e:
                answer = f"Sorry, something went wrong: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# --- Disclaimer footer ---
if config["compliance"]["popia_notice_enabled"]:
    st.markdown(
        f"<div class='footer-note'>{config['compliance']['disclaimer_text']}</div>",
        unsafe_allow_html=True,
    )