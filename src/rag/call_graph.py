from __future__ import annotations

import ast
from pathlib import Path

import networkx as nx


class _CallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)
        self.generic_visit(node)


def build(repo_path: str) -> nx.DiGraph:
    """Build a caller→callee directed graph over top-level function defs."""

    graph = nx.DiGraph()
    for py_file in Path(repo_path).rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except SyntaxError:
            continue
        except OSError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            graph.add_node(node.name)
            visitor = _CallVisitor()
            visitor.visit(node)
            for callee in visitor.calls:
                graph.add_edge(node.name, callee)

    return graph


def neighbors(graph: nx.DiGraph, symbol: str, depth: int = 1) -> list[str]:
    """Return callers (predecessors) and callees (successors) up to a given depth."""

    result: set[str] = set()
    frontier: set[str] = {symbol}

    for _ in range(max(depth, 0)):
        next_frontier: set[str] = set()
        for s in frontier:
            for p in graph.predecessors(s):
                result.add(p)
                next_frontier.add(p)
            for c in graph.successors(s):
                result.add(c)
                next_frontier.add(c)
        frontier = next_frontier

    result.discard(symbol)
    return sorted(result)
