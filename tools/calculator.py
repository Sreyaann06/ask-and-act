import ast
import operator

# Only these operations are allowed. No eval(), so no code can be injected.
_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left = _eval(node.left)
        right = _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def calculate(expression: str) -> dict:
    """Safely evaluate a math expression like '0.15 * 32'. Never raises."""
    try:
        if not isinstance(expression, str) or not expression.strip():
            return {"error": "Empty expression"}
        if len(expression) > 200:
            return {"error": "Expression too long"}
        tree = ast.parse(expression.strip(), mode="eval")
        return {"expression": expression, "result": _eval(tree.body)}
    except ZeroDivisionError:
        return {"error": "Division by zero"}
    except (ValueError, SyntaxError, OverflowError) as e:
        return {"error": f"Could not evaluate: {e}"}