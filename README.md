# Medical Practice AI Agent

A reusable AI-powered virtual receptionist for medical and wellness practices. Built as a config-driven core engine — one codebase, unlimited clients, onboarding a new practice takes minutes, not a rebuild.

Built for MarkeTan's wellness and healthcare clinic client base.

What it does:

- AI Chat Receptionist— answers patient questions about services, hours, pricing, and staff using a RAG-grounded knowledge base built from each practice's own data
- Conversation memory— maintains context across a full conversation instead of treating every message as new
- Smart escalation— automatically detects urgent/emergency language and hands off to a human via WhatsApp instead of letting the AI attempt a risky answer
- In-chat appointment booking— patients book directly in the chat window with a guided form, no phone call required
- Automatic notifications— practice staff get an instant email the moment a booking comes in
- POPIA-conscious by default— every client instance includes a configurable compliance disclaimer
- Fully branded per client— colours, logo, contact details, and tone all pull from a single config file

Architecture:

The core principle: (one engine, many clients.) Nothing client-specific is hardcoded — every practice is just a config folder.

Project Structure:

medical-practice-agent/
├── core/ # Shared logic — never touched per client
│ ├── agent.py # Gemini chat wrapper, conversation memory, escalation logic
│ ├── rag.py # Knowledge base ingestion + retrieval
│ ├── bookings.py # Booking storage
│ └── notifications.py # Email alerts for new bookings
├── clients/
│ └── _template/ # Copy this folder for every new client
│ ├── config.json # Practice name, branding, services, hours, booking settings
│ ├── knowledge/ # Practice-specific reference docs (optional, future use)
│ └── branding/ # Logo and brand assets
├── app.py # Streamlit entry point
├── requirements.txt
└── .env # API keys and secrets (never committed)


