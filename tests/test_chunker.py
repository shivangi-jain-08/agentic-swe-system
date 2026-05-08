from pathlib import Path

from src.rag.chunker import chunk_file


def test_chunker_does_not_descend_into_nested_defs(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text(
        """

def outer():
    def inner():
        return 1
    return inner()

class C:
    def method(self):
        return 2
""".lstrip(),
        encoding="utf-8",
    )

    chunks = chunk_file(str(sample))
    names = {c.symbol_name for c in chunks}

    # We only chunk top-level definitions.
    assert "outer" in names
    assert "C" in names
    assert "inner" not in names
    assert "method" not in names
