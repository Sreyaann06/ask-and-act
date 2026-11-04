# Notes

## Tradeoffs made given the 2-day limit
- Keyword search instead of embeddings for the knowledge base (simple, no extra dependencies)
- In-memory sessions only: history is lost on restart, per the brief
- Plain HTML/JS frontend instead of a framework, since the focus is the agent logic
- No automated test suite; I tested manually with a fixed set of prompts
- Non-streaming responses, so the user waits for the full answer

## Trickiest part of reliable tool-calling
- Keeping the loop correct: the model's tool-call turn must be stored in the history exactly as returned, and each result sent back as a matching function response. Automatic function calling is disabled so the loop is explicit, and I can log every call.
- The LLM API itself was unreliable: models returned 503 "high demand", and some model names were retired (404). I added retries with backoff, a fallback list of models, and a model name in `.env`.
- Getting the model to skip tools for plain conversation and use the calculator for math came down to clear tool descriptions and a short system prompt.

## Scaling to 50 tools
- Don't send all 50 schemas on every call. Embed each tool's description and retrieve only the top 5-10 relevant tools per question.
- Group tools into namespaces or categories, with a first routing step (or sub-agents per domain)
- Auto-register tools from decorators or config files, instead of a hand-written registry
- Validate arguments with Pydantic, and add per-tool timeouts, retries and caching
- Run tool calls in parallel when independent
- Build an eval set (question → expected tools) to measure selection accuracy and catch regressions
- Add tracing and logging per tool call