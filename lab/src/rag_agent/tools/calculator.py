"""Safe arithmetic calculator tool — no eval of arbitrary Python."""

from __future__ import annotations

import ast
import operator as op
from typing import Any

from langchain_core.tools import tool

# Allowed AST node operators only.
_BIN_OPS: dict[type, Any] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}
_UNARY_OPS: dict[type, Any] = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    # Python 3.10 still may emit Num in some paths; be defensive.
    if isinstance(node, ast.Num):  # type: ignore[attr-defined]
        return float(node.n)  # type: ignore[attr-defined]
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        fn = _BIN_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Operator not allowed: {type(node.op).__name__}")
        if isinstance(node.op, ast.Pow) and (abs(left) > 1e6 or abs(right) > 10):
            raise ValueError("Exponentiation too large for lab calculator")
        return float(fn(left, right))
    if isinstance(node, ast.UnaryOp):
        fn = _UNARY_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Unary op not allowed: {type(node.op).__name__}")
        return float(fn(_eval_node(node.operand)))
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def safe_calculate(expression: str) -> str:
    expr = expression.strip()
    if not expr:
        return "Error: empty expression"
    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval_node(tree)
        # Pretty int when exact.
        if result.is_integer():
            return str(int(result))
        return f"{result:.10g}"
    except Exception as exc:  # noqa: BLE001 — tool surface returns string errors
        return f"Error: {exc}"


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression (+ - * / // % ** and parentheses).

    Use this for numeric questions. Do NOT use for knowledge / document questions.
    Example expressions: "(128 + 64) * 0.15", "2 ** 10".
    """
    return safe_calculate(expression)
