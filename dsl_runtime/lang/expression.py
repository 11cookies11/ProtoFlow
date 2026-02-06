from __future__ import annotations

import ast
import operator
import time
from typing import Any, Dict


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class SafeEvaluator(ast.NodeVisitor):
    """安全表达式求值器，支持算术/比较/逻辑/变量。"""

    def __init__(self, variables: Dict[str, Any]) -> None:
        self.variables = variables

    def eval(self, expr: str) -> Any:
        tree = ast.parse(expr, mode="eval")
        return self.visit(tree.body)

    # 访问节点
    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.variables:
            return self.variables[node.id]
        raise NameError(f"未知变量: {node.id}")

    def visit_Constant(self, node: ast.Constant) -> Any:  # type: ignore[override]
        return node.value

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:  # type: ignore[override]
        op = _OPS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的单目运算")
        return op(self.visit(node.operand))

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:  # type: ignore[override]
        op = _OPS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的布尔运算")
        values = [self.visit(v) for v in node.values]
        result = values[0]
        for v in values[1:]:
            result = op(result, v)
        return result

    def visit_BinOp(self, node: ast.BinOp) -> Any:  # type: ignore[override]
        op = _OPS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的运算符")
        return op(self.visit(node.left), self.visit(node.right))

    def visit_Compare(self, node: ast.Compare) -> Any:  # type: ignore[override]
        left = self.visit(node.left)
        for op_node, comparator in zip(node.ops, node.comparators):
            op = _OPS.get(type(op_node))
            if op is None:
                raise ValueError("不支持的比较运算")
            right = self.visit(comparator)
            if not op(left, right):
                return False
            left = right
        return True

    def visit_IfExp(self, node: ast.IfExp) -> Any:  # type: ignore[override]
        return self.visit(node.body) if self.visit(node.test) else self.visit(node.orelse)

    def visit_Attribute(self, node: ast.Attribute) -> Any:  # type: ignore[override]
        value = self.visit(node.value)
        return getattr(value, node.attr)

    def visit_Subscript(self, node: ast.Subscript) -> Any:  # type: ignore[override]
        value = self.visit(node.value)
        key = self.visit(node.slice)
        return value[key]

    def generic_visit(self, node: ast.AST) -> Any:  # pragma: no cover
        raise ValueError(f"不支持的表达式: {type(node).__name__}")


def _prepare_expr(expr: str) -> str:
    """将 $var 或 $a.b 转换为合法变量名格式。"""
    import re

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        return name.replace(".", "__")

    return re.sub(r"\$([A-Za-z_][\w\.]*)", repl, expr)


def _build_vars(env: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for k, v in env.items():
        result[k.replace(".", "__")] = v
    result["now"] = int(time.time() * 1000)
    return result


def eval_expr(expr: str, env: Dict[str, Any]) -> Any:
    prepared = _prepare_expr(expr)
    vars_map = _build_vars(env)
    evaluator = SafeEvaluator(vars_map)
    return evaluator.eval(prepared)
