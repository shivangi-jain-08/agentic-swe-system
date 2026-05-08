from __future__ import annotations

import networkx as nx

from .call_graph import neighbors as graph_neighbors
from .chunker import Chunk
from .indexer import load_index


def _load_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def query(
    query_str: str,
    faiss_path: str,
    db_path: str,
    call_graph: nx.DiGraph,
    context_budget_tokens: int = 2000,
    top_k: int = 10,
) -> list[Chunk]:
    """Return relevant code chunks with a strict token budget."""

    model = _load_embedding_model()
    index, id_map = load_index(faiss_path)

    vec = model.encode([query_str]).astype("float32")
    _, indices = index.search(vec, top_k)

    hit_ids = [id_map[i] for i in indices[0] if 0 <= i < len(id_map)]

    import duckdb
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    con = duckdb.connect(db_path, read_only=True)

    all_ids: set[str] = set(hit_ids)
    for chunk_id in hit_ids:
        row = con.execute(
            "SELECT symbol_name FROM chunks WHERE chunk_id = ?",
            [chunk_id],
        ).fetchone()
        if not row:
            continue
        for nbr in graph_neighbors(call_graph, row[0], depth=1):
            nbr_row = con.execute(
                "SELECT chunk_id FROM chunks WHERE symbol_name = ?",
                [nbr],
            ).fetchone()
            if nbr_row:
                all_ids.add(nbr_row[0])

    if not all_ids:
        con.close()
        return []

    placeholders = ",".join(["?"] * len(all_ids))
    rows = con.execute(
        "SELECT chunk_id, symbol_name, file_path, start_line, end_line, raw_code, docstring, chunk_type "
        f"FROM chunks WHERE chunk_id IN ({placeholders})",
        list(all_ids),
    ).fetchall()
    con.close()

    chunks = [
        Chunk(
            chunk_id=r[0],
            symbol_name=r[1],
            file_path=r[2],
            start_line=int(r[3]),
            end_line=int(r[4]),
            raw_code=r[5],
            docstring=r[6],
            chunk_type=r[7] if r[7] in {"file", "class", "function"} else "function",
        )
        for r in rows
    ]

    # Enforce token budget.
    result: list[Chunk] = []
    total = 0
    for c in chunks:
        tokens = len(enc.encode(c.raw_code))
        if total + tokens > context_budget_tokens:
            continue
        result.append(c)
        total += tokens

    # Prefer semantic hits first (stable order).
    order = {cid: i for i, cid in enumerate(hit_ids)}
    result.sort(key=lambda c: order.get(c.chunk_id, len(order)))
    return result
