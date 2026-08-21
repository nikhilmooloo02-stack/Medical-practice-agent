import streamlit as st
import re
from core.rag import load_client_config
from core.bookings import save_booking
from core.notifications import send_booking_notification
from core.timezone_utils import now_sa

CLIENT_ID = "_template"

config = load_client_config(CLIENT_ID)

st.set_page_config(page_title="Book - " + config["practice_name"], page_icon="📅", layout="centered")

primary = config["branding"]["primary_color"]
secondary = config["branding"]["secondary_color"]

if "theme" not in st.session_state:
    st.session_state.theme = "light"

is_dark = st.session_state.theme == "dark"

if is_dark:
    bg_color = "#0e1117"
    card_bg = "#1c1f26"
    card_border = "#2c2f38"
    text_color = "#f0f0f0"
    subtitle_color = "#d0d0d0"
    accent_color = secondary
else:
    bg_color = "#f5f8fc"
    card_bg = "#ffffff"
    card_border = "#e3ebf5"
    text_color = "#1a1a1a"
    subtitle_color = "#555555"
    accent_color = primary

st.markdown(
    f"""
    <style>
    html, body {{ background-color: {bg_color} !important; }}
    .stApp {{ background-color: {bg_color} !important; }}
    .stApp, .stApp p, .stApp span, .stApp label {{
        color: {text_color};
    }}
    div[data-testid="stAppViewContainer"],
    div[data-testid="stMain"],
    div[data-testid="stMainBlockContainer"],
    div[data-testid="block-container"],
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stBottomBlockContainer"],
    div[data-testid="stBottom"] {{
        background-color: {bg_color} !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {card_bg} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}

    .book-title {{
        color: {accent_color} !important;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }}
    .book-subtitle {{
        color: {subtitle_color} !important;
        font-size: 1rem;
        font-weight: 500;
        background-color: {card_bg};
        border-left: 4px solid {accent_color};
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 1.2rem;
    }}

    div[data-testid="stForm"] {{
        background-color: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 1.2rem;
    }}

    div.stFormSubmitButton > button {{
        background-color: {accent_color};
        color: {bg_color if is_dark else "#ffffff"};
        border-radius: 10px;
        border: none;
        font-weight: 600;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def is_valid_sa_phone(phone):
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 9


practice_name = config["practice_name"]

st.markdown("<div class='book-title'>Book an Appointment</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='book-subtitle'>{practice_name} — fill in the details below and our team will confirm shortly.</div>",
    unsafe_allow_html=True,
)

if not config["booking"]["enabled"]:
    st.info("Online booking is currently unavailable. Please contact us directly.")
else:
    service_options = [s["name"] for s in config["services"]]
    sa_now = now_sa()

    with st.form("booking_form_page"):
        name = st.text_input(
            "Full name",
            placeholder="e.g. Jane Dlamini",
            help="Enter your first and last name so we know who's booking.",
        )
        phone = st.text_input(
            "Phone number",
            placeholder="e.g. 082 123 4567",
            help="We'll use this number to confirm your appointment. Include at least 9 digits.",
        )
        service = st.selectbox(
            "Which service would you like to book?",
            service_options,
            help="Select the service you're interested in.",
        )
        preferred_date = st.date_input(
            "Preferred date",
            value=sa_now.date(),
            help="Choose your preferred appointment date. This is a request, not a confirmed slot yet.",
        )
        preferred_time = st.time_input(
            "Preferred time",
            value=sa_now.time().replace(second=0, microsecond=0),
            help="Choose your preferred time (South African time). We'll confirm actual availability with you.",
        )
        notes = st.text_area(
            "Anything else we should know? (optional)",
            placeholder="e.g. first-time visit, specific concern, accessibility needs",
            help="Optional — add any extra info that would help the practice prepare for your visit.",
        )

        submitted = st.form_submit_button("Confirm Booking")
        if submitted:
            if not name.strip():
                st.error("Please enter your full name.")
            elif not is_valid_sa_phone(phone):
                st.error("Please enter a valid phone number (at least 9 digits).")
            else:
                booking_data = {
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "service": service,
                    "preferred_date": str(preferred_date),
                    "preferred_time": str(preferred_time),
                    "notes": notes.strip(),
                }

                save_ok = True
                notify_ok = True

                try:
                    save_booking(CLIENT_ID, booking_data)
                except Exception:
                    save_ok = False
                    st.error(
                        "We couldn't save your booking due to a technical issue. "
                        "Please try again, or contact us directly to book."
                    )

                if save_ok:
                    try:
                        send_booking_notification(config, booking_data)
                    except Exception:
                        notify_ok = False

                    st.success(
                        "Thanks " + name + "! Your request for " + service + " on " + str(preferred_date)
                        + " at " + str(preferred_time) + " has been received. Our team will confirm shortly."
                    )

                    if not notify_ok:
                        st.info(
                            "Note: your booking was saved successfully, though our notification system "
                            "had a hiccup — our team will still see your request when they next check."
                        )