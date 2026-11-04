# Ask-and-Act Mini Agent

A small full-stack app where an LLM decides which tools to call, runs them,
and returns a synthesized answer. The UI shows which tools were used for each reply.

## Features
- Chat UI (plain HTML/JS) with a badge per tool call and an expandable view of arguments and raw results
- Python backend (FastAPI) with an agent loop built on Gemini native function calling
- Three tools: calculator, weather (Open-Meteo, no API key), and a NovaCRM FAQ knowledge base (25 Q&A pairs)
- Multi-step chaining, for example "15% of today's high in Austin" uses weather, then the calculator
- Plain conversation gets a direct answer with no forced tool call
- Basic error handling for bad tool calls, failed API calls and malformed input

## Setup (Windows PowerShell)
Tested on Python 3.14.

```powershell
git clone https://github.com/Sreyaann06/ask-and-act.git
cd ask-and-act
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set your key. A free key is available at https://aistudio.google.com:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-flash-lite-latest
```

Run:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

On Mac/Linux, activate the environment with `source venv/bin/activate` and copy with `cp .env.example .env`.

## Project structure
```
app/main.py            API layer (FastAPI): validation, sessions, error responses
agent/agent.py         Orchestration: LLM loop, retries, model fallback
tools/registry.py      Tool schemas and a safe dispatcher
tools/calculator.py    Safe math evaluator (ast, no eval)
tools/weather.py       Open-Meteo geocoding + forecast
tools/knowledge_base.py  Keyword search over data/kb.json
data/kb.json           25 FAQ entries
frontend/index.html    Chat UI
```

## Architecture decisions
1. **Native function calling, no string parsing.** Tools are declared as JSON schemas and the model returns structured calls.
2. **Agent loop with a step cap.** The loop calls the LLM, runs any requested tools, feeds results back and repeats until the model answers in text. `MAX_STEPS = 6` stops runaway loops.
3. **Three separate layers.** The API layer knows nothing about tools, and tools know nothing about the LLM. The registry connects them, so adding a tool means one function plus one schema.
4. **Tools never raise.** Each returns `{"error": ...}` on failure, so the model can explain the problem to the user.
5. **Safe calculator.** Expressions are parsed with `ast` and only arithmetic nodes are allowed, so there is no `eval` and no code injection.
6. **Resilience to a busy LLM API.** The agent retries on 503/429/timeouts and falls back to other models if one is overloaded or retired.
7. **Transparency.** Every response includes `tools_used` (name, args, result), and the UI renders it.
8. **Provider isolation.** All LLM calls are in `agent/agent.py`, so switching providers means editing one file.

## What I'd do with more time
- Stream responses to the UI
- Automated tests, including mocked-LLM tests for the agent loop
- Embedding search for the knowledge base
- Per-session rate limiting and history summarization
- Docker setup, and a provider interface for OpenAI/Anthropic
- Evals to measure tool-selection accuracy

## AI tools used
- **Claude (claude.ai chat):** guided me through project setup, drafted the first version of the tools, agent loop, API and UI, and helped me debug errors (Git, venv, API errors).
- **VS Code:** editor and terminal.
- **My workflow:** I asked for one file at a time, ran each tool in isolation before wiring it in, and tested the agent with prompts that should and should not trigger tools. I fixed [describe what you changed or debugged yourself].
## Troubleshooting
- **Weather tool shows an SSL certificate error:** some networks and antivirus programs intercept HTTPS. The app uses `truststore` to read the system certificate store, which normally fixes this. Run `pip install -r requirements.txt` again if it is missing.
- **"AI service unavailable" / 503:** the Gemini model is overloaded. The app retries and falls back to other models automatically. Wait a minute and try again.
- **"API key not valid":** check that `.env` contains your real key, then restart the server, since `.env` is only read at startup.