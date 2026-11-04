import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools.registry import TOOL_DECLARATIONS, run_tool

load_dotenv()

MAX_STEPS = 6  # cap on LLM <-> tool round trips, so the loop can never run forever

# Tries your configured model first, then fallbacks if Google is overloaded or the model is retired
MODELS = list(dict.fromkeys(
    m for m in [os.getenv("GEMINI_MODEL"), "gemini-flash-lite-latest",
                "gemini-3.7-flash", "gemini-flash-latest"] if m
))

SYSTEM_PROMPT = (
    "You are a helpful assistant. You have tools for math, weather and a NovaCRM FAQ. "
    "Use a tool only when it is needed. For greetings and general conversation, answer directly. "
    "For math, always use the calculate tool. If a question needs several steps "
    "(for example, a percentage of a temperature), call the tools one after another. "
    "Weather temperatures are in Celsius. If a tool returns an error, explain it simply to the user."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(http_options=types.HttpOptions(timeout=30000))
    return _client


def _config():
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )


def _generate(contents):
    """Call Gemini. Retries when busy (503/429/timeout) and falls back to other models."""
    last_error = "unknown error"
    for model in MODELS:
        for attempt in range(3):
            try:
                return _get_client().models.generate_content(
                    model=model, contents=contents, config=_config()
                )
            except Exception as e:
                last_error = str(e)[:200]
                busy = any(s in last_error for s in ("503", "429", "timed out", "Timeout"))
                if busy:
                    time.sleep(2 * (attempt + 1))
                    continue
                break  # 404 or bad request: try the next model
    raise RuntimeError(f"The AI service is unavailable right now. ({last_error})")


def run_agent(history: list, user_message: str):
    """
    history: this session's list of messages (updated in place on success).
    Returns (answer_text, tool_log), where tool_log lists every tool call made.
    """
    contents = list(history) + [types.Content(role="user", parts=[types.Part(text=user_message)])]
    tool_log = []

    for _ in range(MAX_STEPS):
        response = _generate(contents)
        if not response.candidates:
            raise RuntimeError("The AI returned no answer. Please rephrase and try again.")

        model_content = response.candidates[0].content
        contents.append(model_content)  # keep the model's turn exactly as returned
        calls = response.function_calls

        if not calls:  # no tool needed, or the final answer is ready
            history[:] = contents
            return (response.text or "I couldn't produce an answer."), tool_log

        result_parts = []
        for call in calls:
            args = dict(call.args or {})
            result = run_tool(call.name, args)
            tool_log.append({"name": call.name, "args": args, "result": result})
            result_parts.append(
                types.Part.from_function_response(name=call.name, response={"result": result})
            )
        contents.append(types.Content(role="user", parts=result_parts))

    history[:] = contents
    return "I couldn't finish within the step limit. Please try a simpler question.", tool_log