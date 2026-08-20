import os
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str) -> str:
    """Read a secret from Streamlit Cloud's st.secrets if available, else fall back to .env"""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)


def send_booking_notification(config: dict, booking: dict):
    """Send an email to the practice when a new booking comes in"""
    sender_email = get_secret("SENDER_EMAIL")
    sender_password = get_secret("SENDER_APP_PASSWORD")
    recipient_email = config["booking"].get("notify_email")

    if not sender_email or not sender_password or not recipient_email:
        print("Email notification skipped: missing sender or recipient config.")
        return False

    subject = f"New Booking Request - {config['practice_name']}"
    body = f"""A new booking request has come in via the chatbot:

Name: {booking.get('name')}
Phone: {booking.get('phone')}
Service: {booking.get('service')}
Preferred date: {booking.get('preferred_date')}
Preferred time: {booking.get('preferred_time')}
Notes: {booking.get('notes') or 'None'}

Please contact the patient to confirm the appointment.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email notification failed: {e}")
        return False