import pathlib
from src.grounding_graph import _compute_graph_hash, build_grounding_graph


def test_graph_hash_matches_golden():
    golden_path = pathlib.Path(__file__).resolve().parent / "golden" / "graph_hash.txt"
    golden_hash = golden_path.read_text(encoding="utf-8").strip()
    assert _compute_graph_hash(build_grounding_graph()) == golden_hash
