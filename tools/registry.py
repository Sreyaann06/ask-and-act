from tools.calculator import calculate
from tools.weather import get_weather
from tools.knowledge_base import search_knowledge_base

# Descriptions the LLM reads to decide which tool to call
TOOL_DECLARATIONS = [
    {
        "name": "calculate",
        "description": "Evaluate a math expression such as '0.15 * 32' or '(5 + 3) ** 2'. "
                       "Use this for any arithmetic instead of computing in your head.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "The math expression to evaluate"}
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get today's current temperature, high and low (in Celsius) for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, for example 'Austin'"}
            },
            "required": ["city"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the NovaCRM product FAQ (pricing, setup, features, security, support). "
                       "Use this for any question about NovaCRM.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keywords describing what to look up"}
            },
            "required": ["query"],
        },
    },
]

TOOL_FUNCTIONS = {
    "calculate": calculate,
    "get_weather": get_weather,
    "search_knowledge_base": search_knowledge_base,
}


def run_tool(name: str, args: dict) -> dict:
    """Run a tool by name. Always returns a dict and never raises."""
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return func(**(args or {}))
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
    except Exception as e:
        return {"error": f"Tool {name} failed: {e}"}