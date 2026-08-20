import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from core.rag import load_client_config, query_knowledge

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def check_escalation(question: str, config: dict) -> bool:
    keywords = config["escalation"]["escalation_trigger_keywords"]
    question_lower = question.lower()
    return any(keyword.lower() in question_lower for keyword in keywords)


def build_system_prompt(config: dict) -> str:
    return f"""You are a virtual receptionist for {config['practice_name']}.

Tone: {config['ai_settings']['tone']}

Rules:
- You are in an ONGOING conversation. Only greet the patient ONCE, at the very start. Never repeat a greeting or re-introduce yourself in later replies.
- Only answer using the practice information provided to you in each message's context.
- If you don't know the answer, say so and suggest contacting the practice directly.
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
        # Prime the chat once with system instructions, not shown to the user
        chat.send_message(build_system_prompt(config))
        session_state.gemini_chat = chat
    return session_state.gemini_chat


def get_response(client_id: str, question: str, session_state) -> dict:
    config = load_client_config(client_id)

    if check_escalation(question, config):
        whatsapp = config["escalation"]["whatsapp_number"]
        return {
            "response": (
                f"It sounds like you may need to speak with our team directly. "
                f"Please reach out to us on WhatsApp at {whatsapp} and we'll assist you right away."
            ),
            "escalated": True,
        }

    retrieved_chunks = query_knowledge(client_id, question)
    knowledge_text = "\n".join(f"- {chunk}" for chunk in retrieved_chunks)

    chat = get_or_create_chat(session_state, config)

    message_with_context = (
        f"Relevant practice information for this question:\n{knowledge_text}\n\n"
        f"Patient: {question}"
    )

    try:
        response_text = call_gemini_with_retry(chat, message_with_context)
        return {"response": response_text, "escalated": False}
    except errors.ServerError:
        whatsapp = config["escalation"]["whatsapp_number"]
        return {
            "response": (
                f"I'm having trouble responding right now due to high demand. "
                f"Please try again in a moment, or contact us directly on WhatsApp at {whatsapp}."
            ),
            "escalated": False,
        }