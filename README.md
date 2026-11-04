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
- **Claude (claude.ai chat):** my main tool. I used it as a step-by-step guide for setting up the project (Python venv, Git, GitHub), and to draft the first version of each file: the tools, the tool registry, the Gemini agent loop, the FastAPI endpoint and the chat UI. I also pasted error messages and screenshots into it to debug.
- **VS Code:** editor and terminal.
- **Google AI Studio:** to create the Gemini API key.

**How I worked:**
- I built one file at a time and tested each tool on its own in the terminal before connecting it to the agent.
- I tested the agent with prompts that should use tools (math, weather, FAQ), chained tools (the Austin temperature question) and no tools (plain chat), and checked the badges and the "Tool calls" view each time.
- I ran a fresh-clone test in a separate folder to confirm the README setup steps work.

**Problems I debugged along the way:**
- `.gitignore` was not taking effect, so `.env` showed up in Git. I rewrote the file and confirmed with `git check-ignore`.
- PowerShell blocked the venv activation script, which I fixed with `Set-ExecutionPolicy`.
- Gemini returned 503 "high demand" errors, and some model names (such as `gemini-2.5-flash`) were retired (404). This led to retries, a fallback list of models, and a configurable model name in `.env`.
- The fresh clone gave "API key not valid" because `.env` still held the placeholder.
- The weather tool failed with an SSL certificate error on my machine. I fixed it with `truststore`, which uses the Windows certificate store.

## Troubleshooting
- **Weather tool shows an SSL certificate error:** some networks and antivirus programs intercept HTTPS. The app uses `truststore` to read the system certificate store, which normally fixes this. Run `pip install -r requirements.txt` again if it is missing.
- **"AI service unavailable" / 503:** the Gemini model is overloaded. The app retries and falls back to other models automatically. Wait a minute and try again.
- **"API key not valid":** check that `.env` contains your real key, then restart the server, since `.env` is only read at startup.
