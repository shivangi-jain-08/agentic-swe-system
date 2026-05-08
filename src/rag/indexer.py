from __future__ import annotations

import pickle
from pathlib import Path

from .chunker import chunk_repo


def _load_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def index_repo(repo_path: str, faiss_path: str, db_path: str) -> None:
    """Index a Python repo into (1) a FAISS index and (2) a DuckDB `chunks` table."""

    chunks = chunk_repo(repo_path)
    if not chunks:
        raise ValueError(f"No chunks found in {repo_path}")

    model = _load_embedding_model()
    texts = [c.raw_code for c in chunks]

    vectors = model.encode(texts, show_progress_bar=True)
    vectors = vectors.astype("float32")

    import faiss

    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    faiss.write_index(index, faiss_path)

    # Store chunk id order so FAISS index position -> chunk_id
    id_map = [c.chunk_id for c in chunks]
    with open(faiss_path + ".ids", "wb") as f:
        pickle.dump(id_map, f)

    import duckdb

    con = duckdb.connect(db_path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id VARCHAR PRIMARY KEY,
            symbol_name VARCHAR,
            file_path VARCHAR,
            start_line INTEGER,
            end_line INTEGER,
            raw_code TEXT,
            docstring TEXT,
            chunk_type VARCHAR
        )
        """
    )

    con.executemany(
        "INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                c.chunk_id,
                c.symbol_name,
                c.file_path,
                c.start_line,
                c.end_line,
                c.raw_code,
                c.docstring,
                c.chunk_type,
            )
            for c in chunks
        ],
    )
    con.close()


def load_index(faiss_path: str):
    import faiss

    index = faiss.read_index(faiss_path)
    with open(faiss_path + ".ids", "rb") as f:
        id_map = pickle.load(f)
    return index, id_map


def resolve_default_paths() -> tuple[str, str]:
    """Return `(faiss_path, chunks_db_path)` from env defaults or cwd."""

    import os

    faiss_path = os.getenv("FAISS_INDEX_PATH", "./chunks.index")
    chunks_db_path = os.getenv("CHUNKS_DB_PATH", "./chunks.db")
    return str(Path(faiss_path)), str(Path(chunks_db_path))
