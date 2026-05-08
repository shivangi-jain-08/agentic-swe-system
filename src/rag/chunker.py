from __future__ import annotations

import ast
import hashlib
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    symbol_name: str
    file_path: str
    start_line: int
    end_line: int
    raw_code: str
    docstring: str | None
    chunk_type: Literal["file", "class", "function"]


class _ChunkVisitor(ast.NodeVisitor):
    """Collect top-level class and function definitions without descending."""

    def __init__(self, source: str, file_path: str):
        self._source = source
        self._file_path = file_path
        self.chunks: list[Chunk] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._add(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._add(node, "function")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._add(node, "class")

    def _add(self, node: ast.AST, chunk_type: Literal["class", "function"]) -> None:
        raw = ast.get_source_segment(self._source, node) or ""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)
        else:
            docstring = None
        symbol = getattr(node, "name", "<unknown>")
        chunk_id = hashlib.sha256(f"{self._file_path}:{symbol}".encode()).hexdigest()[:16]

        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)

        self.chunks.append(
            Chunk(
                chunk_id=chunk_id,
                symbol_name=symbol,
                file_path=self._file_path,
                start_line=int(start),
                end_line=int(end),
                raw_code=textwrap.dedent(raw),
                docstring=docstring,
                chunk_type=chunk_type,
            )
        )


def chunk_file(path: str) -> list[Chunk]:
    source = Path(path).read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(source)
    visitor = _ChunkVisitor(source, path)
    visitor.visit(tree)
    return visitor.chunks


def chunk_repo(repo_path: str) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for py_file in Path(repo_path).rglob("*.py"):
        try:
            all_chunks.extend(chunk_file(str(py_file)))
        except SyntaxError:
            continue
        except OSError:
            continue
    return all_chunks
