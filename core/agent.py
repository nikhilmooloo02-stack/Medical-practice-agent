import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from core.rag import load_client_config, query_knowledge
from urllib.parse import quote

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_whatsapp_link(whatsapp_number: str, practice_name: str) -> str:
    """Build a clickable wa.me link with a pre-filled message"""
    digits_only = "".join(ch for ch in whatsapp_number if ch.isdigit())
    message = f"Hi, I'd like some help from {practice_name}."
    return f"https://wa.me/{digits_only}?text={quote(message)}"


def check_escalation(question: str, config: dict) -> bool:
    keywords = config["escalation"]["escalation_trigger_keywords"]
    question_lower = question.lower()
    return any(keyword.lower() in question_lower for keyword in keywords)


def build_system_prompt(config: dict) -> str:
    contact = config["contact"]
    contact_line = (
        f"Phone: {contact['phone']}, WhatsApp: {contact['whatsapp']}, "
        f"Email: {contact['email']}, Address: {contact['address']}"
    )

    return f"""You are a virtual receptionist for {config['practice_name']}.

Tone: {config['ai_settings']['tone']}

The practice's contact details are: {contact_line}

Rules:
- You are in an ONGOING conversation. Only greet the patient ONCE, at the very start. Never repeat a greeting or re-introduce yourself in later replies.
- Only answer using the practice information provided to you in each message's context.
- If the provided context is marked as LOW CONFIDENCE or doesn't actually answer the question, do NOT guess or make something up. Instead, clearly say you don't have that specific information, and explicitly give the patient the phone number and/or WhatsApp number from the contact details above so they can follow up directly. Always include the actual number in your reply, don't just say "contact us."
- Never provide medical advice, diagnosis, or treatment recommendations.
- Keep responses under {config['ai_settings']['max_response_length']} words.
- Be warm, professional, and natural — like a real front-desk staff member, not a script.
- Do not repeat information you've already given earlier in this conversation unless asked again.
"""


def call_gemini_with_retry(chat, message: str, max_retries: int = 3) -> str:
    last_error = None
    for attempt in range(max_retries):
        try:
            response = chat.send_message(message)
            return response.text
        except errors.ServerError as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
    raise last_error


def get_or_create_chat(session_state, config: dict):
    """Reuse one chat session for the whole conversation, so the model remembers context"""
    if "gemini_chat" not in session_state or session_state.gemini_chat is None:
        chat = _client.chats.create(model=config["ai_settings"]["model"])
        call_gemini_with_retry(chat, build_system_prompt(config))
        session_state.gemini_chat = chat
    return session_state.gemini_chat


def get_response(client_id: str, question: str, session_state) -> dict:
    config = load_client_config(client_id)

    if check_escalation(question, config):
        whatsapp_number = config["escalation"]["whatsapp_number"]
        link = build_whatsapp_link(whatsapp_number, config["practice_name"])
        return {
            "response": (
                f"It sounds like you may need to speak with our team directly. "
                f"[Click here to chat with us on WhatsApp]({link})"
            ),
            "escalated": True,
            "whatsapp_link": link,
        }

    whatsapp_number = config["escalation"]["whatsapp_number"]
    link = build_whatsapp_link(whatsapp_number, config["practice_name"])

    try:
        retrieval = query_knowledge(client_id, question)

        if retrieval.get("index_error"):
            return {
                "response": (
                    f"Our knowledge base isn't set up correctly yet. "
                    f"[Click here to chat with us on WhatsApp]({link}) and our team will help you directly."
                ),
                "escalated": False,
                "whatsapp_link": link,
            }

        chunks = retrieval["chunks"]
        confident = retrieval["has_confident_match"]

        knowledge_text = "\n".join(f"- {chunk}" for chunk in chunks)
        confidence_note = (
            ""
            if confident
            else "\n(Note: LOW CONFIDENCE — this context may not actually answer the question. "
                 "If it doesn't, say you don't know and give the patient the phone/WhatsApp number instead of guessing.)"
        )

        chat = get_or_create_chat(session_state, config)

        message_with_context = (
            f"Relevant practice information for this question:\n{knowledge_text}{confidence_note}\n\n"
            f"Patient: {question}"
        )

        response_text = call_gemini_with_retry(chat, message_with_context)
        return {"response": response_text, "escalated": False, "whatsapp_link": None}

    except errors.ServerError:
        return {
            "response": (
                f"I'm having trouble responding right now due to high demand. "
                f"[Click here to chat with us on WhatsApp]({link}) or try again in a moment."
            ),
            "escalated": False,
            "whatsapp_link": link,
        }
    except Exception:
        return {
            "response": (
                f"Sorry, something went wrong on our end. "
                f"[Click here to chat with us on WhatsApp]({link}) and we'll help you directly."
            ),
            "escalated": False,
            "whatsapp_link": link,
        }