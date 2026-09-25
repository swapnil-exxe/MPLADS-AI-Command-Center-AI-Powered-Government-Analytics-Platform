# 12. Subho AI Governance Chatbot

## Subho AI Governance Chatbot (`api/routers/chat.py`)

Subho AI is an interactive conversational assistant for platform users:

### Architecture & LLM Integration
- **LLM Engine**: Groq API caller with model fallback chain (`llama-3.3-70b-versatile`, `groq/compound`, `qwen/qwen3.6-27b`).
- **Prompt Injection Defense (`check_prompt_injection`)**: Regex pattern matching against prompt override attempts (`ignore previous instructions`, `gsk_*`, `postgresql://`).
- **Output Redaction (`sanitize_chat_output`)**: Regex filter redacting API keys, database connection strings, and JWT secrets before returning responses.
- **Context Injection**: Server-side injection of authorized jurisdictional metrics into LLM system prompts based on user role (`PUBLIC`, `MP`, `PARLIAMENT`, `ORGANIZATION`, `AGENCY`).

