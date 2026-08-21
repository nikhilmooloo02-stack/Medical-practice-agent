Medical Practice AI Agent:

A reusable AI-powered virtual receptionist for medical and wellness practices. Built as a config-driven core engine — onboarding a new client is a matter of swapping a config file, not rewriting code.

Built for MarkeTan's wellness and healthcare clinic client base.

What it does:

- AI Chat Receptionist — answers patient questions about services, hours, pricing, and staff using a RAG-grounded knowledge base built from each practice's own data
- Conversation memory — maintains context across a full conversation instead of treating every message as new
- Smart escalation — automatically detects urgent/emergency language and hands off to a human via a one-click WhatsApp link, instead of letting the AI attempt a risky answer
- Honest fallback — when the knowledge base doesn't confidently answer a question, the assistant says so and provides real contact details rather than guessing
- In-chat appointment booking — patients book on a dedicated page with a guided, validated form — no phone call required
- Automatic notifications — practice staff get an instant email the moment a booking comes in
- Conversation logging — every conversation is logged per client, with a password-protected internal staff page to review, filter, and export logs
- Data retention policy — old bookings and conversation logs are automatically purged based on a configurable retention period
- POPIA-conscious by default — every client instance includes a configurable compliance disclaimer, shown to patients before they chat
- Light and dark mode — patients can toggle their preferred theme
- Fully branded per client — colours, logo, contact details, services, and tone all pull from a single config file
- Resilient by design — handles Gemini API overload, missing knowledge bases, and other failures gracefully with friendly fallbacks instead of crashes

Tech Stack:

- Frontend: Streamlit (multi-page app)
- AI: Google Gemini API (`google-genai` SDK)
- Knowledge retrieval: ChromaDB (RAG)
- Storage: CSV (prototype stage — designed to migrate to Supabase/Postgres for production use)
- Notifications: SMTP email via Gmail
- Deployment: Streamlit Community Cloud

Architecture:

The core principle: (one engine, many clients.) Nothing client-specific is hardcoded — every practice is just a config folder.

Project Structure:
medical-practice-agent/
├── core/ # Shared logic — never touched per client
│ ├── agent.py # Gemini chat wrapper, conversation memory, escalation logic
│ ├── rag.py # Knowledge base ingestion + retrieval, auto-recovery if missing
│ ├── bookings.py # Booking storage
│ ├── notifications.py # Email alerts for new bookings
│ ├── conversation_log.py # Per-session conversation logging
│ ├── retention.py # Automatic data retention/cleanup
│ └── timezone_utils.py # South African timezone handling
├── pages/
│ ├── 1_Book_Appointment.py # Dedicated booking page
│ └── 2_Conversation_Logs.py # Password-protected staff view of conversation logs
├── clients/
│ └── _template/ # Copy this folder for every new client
│ ├── config.json # Practice name, branding, services, hours, booking settings
│ ├── knowledge/ # Practice-specific reference docs (optional, future use)
│ ├── branding/ # Logo and brand assets
│ └── chroma_db/ # Auto-generated RAG index (not committed to git)
├── app.py # Streamlit entry point (main chat)
├── requirements.txt
├── .streamlit/
│ └── secrets.toml # Local secrets for testing (never committed)
└── .env # API keys and secrets (never committed)


Getting Started:

1. Clone and set up the environment:

```bash
git clone https://github.com/nikhilmooloo02-stack/Medical-practice-agent.git
cd Medical-practice-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

2. Add your API keys:

For local development, create a `.streamlit/secrets.toml` file:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
SENDER_EMAIL = "your_sender_gmail@gmail.com"
SENDER_APP_PASSWORD = "your_gmail_app_password"
STAFF_LOGS_PASSWORD = "your_chosen_staff_password"
```

3. Run the app

```bash
streamlit run app.py
```

Onboarding a New Client:

1. Copy `clients/_template/` to `clients/{new_client_name}/`
2. Edit `config.json` with the new practice's details (name, branding, services, hours, escalation contact, booking notification email)
3. Update `CLIENT_ID` in `app.py` and both files in `pages/` to match the new client's folder name
4. Run the app — the knowledge base rebuilds automatically from the new config the first time it's queried

Deployment:

Deployed on Streamlit Community Cloud. Secrets (`GEMINI_API_KEY`, `SENDER_EMAIL`, `SENDER_APP_PASSWORD`, `STAFF_LOGS_PASSWORD`) are configured in the app's Secrets manager, not in the repo.

Known Limitations (Prototype Stage):

- Booking and conversation data stored in CSV files — fine for a single client at low volume, should migrate to a real database (Supabase/Postgres) before scaling to multiple live clients
- No access control on the main patient-facing chat link — anyone with the URL can use it
- Running on Gemini's free tier — subject to occasional rate limiting during high demand

Roadmap:

- [ ] Migrate booking and conversation storage to Supabase
- [ ] Google Calendar / practice management system integrations
- [ ] Multi-client analytics dashboard
- [ ] SMS booking confirmations
- [ ] Custom document ingestion for knowledge base (upload a brochure/PDF, auto-index it)
- [ ] Access control on the main chat link

Author:

Built by Nikhil Mooloo for MarkeTan — AI automation tools for wellness and healthcare practices.
