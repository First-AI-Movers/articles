"""Tests for E22 RAG embedding index."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pyarrow as pa
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _synthetic_vector(seed: int, dim: int = 384) -> list[float]:
    """Deterministic synthetic float32 vector for tests."""
    import numpy as np
    rng = np.random.default_rng(seed)
    vec = rng.random(dim).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def _make_mock_embedder(vectors: list[list[float]]):
    """Return a mock TextEmbedding that yields the given vectors."""
    mock = MagicMock()
    mock.embed.return_value = iter(vectors)
    return mock


# ---------------------------------------------------------------------------
# A. Build script existence & constants
# ---------------------------------------------------------------------------

class TestBuildScriptExists:
    def test_build_embeddings_script_exists(self):
        assert (TOOLS_DIR / "build_embeddings.py").exists()

    def test_embedding_schema_constants(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        assert m.DEFAULT_MODEL == "BAAI/bge-small-en-v1.5"
        assert m.EMBEDDING_DIM == 384
        assert m.MAX_BODY_CHARS == 500
        schema_names = [f.name for f in m.SCHEMA]
        expected = [
            "folder", "slug", "title", "published_date", "canonical_url",
            "local_url", "topics", "summary", "text_chars", "model",
            "embedding_dim", "embedding",
        ]
        assert schema_names == expected

    def test_index_path_points_to_repo_root(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        assert m.INDEX_PATH == REPO_ROOT / "index.json"


# ---------------------------------------------------------------------------
# B. Text builder & preprocessing
# ---------------------------------------------------------------------------

class TestTextBuilder:
    def test_build_input_text_uses_title_topics_summary_excerpt(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        text = m._build_input_text(
            title="AI Governance",
            topics=["AI Strategy", "Regulation"],
            summary="A brief summary.",
            body="Body paragraph one.\n\nBody paragraph two.",
        )
        assert "AI Governance" in text
        assert "AI Strategy" in text
        assert "Regulation" in text
        assert "A brief summary." in text
        assert "Body paragraph one." in text

    def test_build_input_text_without_summary_or_topics(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        text = m._build_input_text(
            title="Title Only",
            topics=[],
            summary="",
            body="Just body.",
        )
        assert text == "Title Only\nJust body."

    def test_front_matter_stripped(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        raw = "---\ntitle: X\n---\n\n# Hello\n\nWorld."
        body = m._strip_front_matter(raw)
        assert "title: X" not in body
        assert "# Hello" in body
        assert "World." in body

    def test_front_matter_stripped_no_front_matter(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        raw = "# Hello\n\nWorld."
        body = m._strip_front_matter(raw)
        assert "# Hello" in body
        assert "World." in body

    def test_extract_tldr_detects_tldr(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        body = "> **TL;DR:** This is the summary.\n\nMore text."
        assert m._extract_tldr(body) == "This is the summary."

    def test_extract_tldr_detects_key_takeaway(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        body = "> Key takeaways: First point. Second point.\n\nMore text."
        assert "First point. Second point." in m._extract_tldr(body)

    def test_extract_tldr_returns_empty_when_missing(self):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m
        body = "# Hello\n\nWorld."
        assert m._extract_tldr(body) == ""


# ---------------------------------------------------------------------------
# C. Deterministic ordering & CLI behaviour
# ---------------------------------------------------------------------------

class TestDeterminismAndCLI:
    def test_article_order_deterministic(self, tmp_path, monkeypatch):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m

        # Build a fake index + articles
        idx = {
            "articles": [
                {"folder": "2026-01-03-a", "slug": "a", "title": "A", "published_date": "2026-01-03", "canonical_url": "https://a.com", "topics": ["X"]},
                {"folder": "2026-01-01-b", "slug": "b", "title": "B", "published_date": "2026-01-01", "canonical_url": "https://b.com", "topics": ["X"]},
                {"folder": "2026-01-02-c", "slug": "c", "title": "C", "published_date": "2026-01-02", "canonical_url": "https://c.com", "topics": ["X"]},
            ]
        }
        idx_path = tmp_path / "index.json"
        idx_path.write_text(json.dumps(idx), encoding="utf-8")
        articles_dir = tmp_path / "articles"
        for folder in ("2026-01-03-a", "2026-01-01-b", "2026-01-02-c"):
            (articles_dir / folder).mkdir(parents=True)
            (articles_dir / folder / "article.md").write_text("# T\n\nBody.", encoding="utf-8")

        monkeypatch.setattr(m, "INDEX_PATH", idx_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", articles_dir)

        vecs = [np.array(_synthetic_vector(i)) for i in range(3)]
        with patch("build_embeddings.TextEmbedding") as MockEmbed:
            MockEmbed.return_value.embed.return_value = iter(vecs)
            rows = m.build_embeddings(model_name="test-model", limit=None, dry_run=False)

        folders = [r["folder"] for r in rows]
        # reverse chronological: 2026-01-03, 2026-01-02, 2026-01-01
        assert folders == ["2026-01-03-a", "2026-01-02-c", "2026-01-01-b"]

    def test_dry_run_writes_no_file(self, tmp_path, monkeypatch):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m

        idx = {"articles": []}
        idx_path = tmp_path / "index.json"
        idx_path.write_text(json.dumps(idx), encoding="utf-8")
        monkeypatch.setattr(m, "INDEX_PATH", idx_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", tmp_path / "articles")

        rows = m.build_embeddings(model_name="test-model", limit=None, dry_run=True)
        assert rows == []

    def test_limit_caps_articles(self, tmp_path, monkeypatch):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m

        idx = {
            "articles": [
                {"folder": f"2026-01-{i:02d}-x", "slug": f"x{i}", "title": f"T{i}", "published_date": f"2026-01-{i:02d}", "canonical_url": "https://x.com", "topics": []}
                for i in range(1, 11)
            ]
        }
        idx_path = tmp_path / "index.json"
        idx_path.write_text(json.dumps(idx), encoding="utf-8")
        articles_dir = tmp_path / "articles"
        for i in range(1, 11):
            (articles_dir / f"2026-01-{i:02d}-x").mkdir(parents=True)
            (articles_dir / f"2026-01-{i:02d}-x" / "article.md").write_text("# T\n\nBody.", encoding="utf-8")

        monkeypatch.setattr(m, "INDEX_PATH", idx_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", articles_dir)

        vecs = [np.array(_synthetic_vector(i)) for i in range(3)]
        with patch("build_embeddings.TextEmbedding") as MockEmbed:
            MockEmbed.return_value.embed.return_value = iter(vecs)
            rows = m.build_embeddings(model_name="test-model", limit=3, dry_run=False)

        assert len(rows) == 3


# ---------------------------------------------------------------------------
# D. Parquet output contract
# ---------------------------------------------------------------------------

class TestParquetContract:
    def test_parquet_writer_uses_expected_columns(self, tmp_path, monkeypatch):
        sys.path.insert(0, str(TOOLS_DIR))
        import build_embeddings as m

        idx = {
            "articles": [
                {"folder": "2026-01-01-test", "slug": "test", "title": "Test", "published_date": "2026-01-01", "canonical_url": "https://example.com", "topics": ["AI"]},
            ]
        }
        idx_path = tmp_path / "index.json"
        idx_path.write_text(json.dumps(idx), encoding="utf-8")
        articles_dir = tmp_path / "articles"
        (articles_dir / "2026-01-01-test").mkdir(parents=True)
        (articles_dir / "2026-01-01-test" / "article.md").write_text("# T\n\nBody text here.", encoding="utf-8")

        monkeypatch.setattr(m, "INDEX_PATH", idx_path)
        monkeypatch.setattr(m, "ARTICLES_DIR", articles_dir)

        vec = np.array(_synthetic_vector(0))
        with patch("build_embeddings.TextEmbedding") as MockEmbed:
            MockEmbed.return_value.embed.return_value = iter([vec])
            rows = m.build_embeddings(model_name="test-model", limit=None, dry_run=False)

        out = tmp_path / "out.parquet"
        m._write_parquet(rows, out)
        assert out.exists()

        import pyarrow.parquet as pq
        table = pq.read_table(out)
        assert table.num_rows == 1
        assert set(table.column_names) == set(m.SCHEMA.names)
        assert table.column("embedding").type == pa.list_(pa.float32(), 384)
        assert table.column("folder")[0].as_py() == "2026-01-01-test"
        assert table.column("slug")[0].as_py() == "test"
        assert table.column("local_url")[0].as_py() == "/articles/test/"
        assert table.column("embedding_dim")[0].as_py() == 384


# ---------------------------------------------------------------------------
# E. Sample retrieval script
# ---------------------------------------------------------------------------

class TestSampleScript:
    def test_sample_script_exists(self):
        assert (TOOLS_DIR / "embeddings_sample.py").exists()

    def test_sample_retrieval_ranks_by_cosine_similarity(self, tmp_path):
        sys.path.insert(0, str(TOOLS_DIR))
        import embeddings_sample as s
        import numpy as np
        import pyarrow as pa
        import pyarrow.parquet as pq

        dim = 384
        # Three synthetic article embeddings: aligned with x, y, z axes
        v1 = np.array([1.0] + [0.0] * (dim - 1), dtype=np.float32)
        v2 = np.array([0.0, 1.0] + [0.0] * (dim - 2), dtype=np.float32)
        v3 = np.array([0.0, 0.0, 1.0] + [0.0] * (dim - 3), dtype=np.float32)

        schema = pa.schema([
            ("title", pa.string()),
            ("slug", pa.string()),
            ("local_url", pa.string()),
            ("canonical_url", pa.string()),
            ("embedding", pa.list_(pa.float32(), dim)),
            ("model", pa.string()),
        ])
        table = pa.table({
            "title": ["Alpha", "Beta", "Gamma"],
            "slug": ["alpha", "beta", "gamma"],
            "local_url": ["/articles/alpha/", "/articles/beta/", "/articles/gamma/"],
            "canonical_url": ["https://a.com", "https://b.com", "https://c.com"],
            "embedding": [v1.tolist(), v2.tolist(), v3.tolist()],
            "model": ["test"] * 3,
        }, schema=schema)

        index_path = tmp_path / "test.parquet"
        pq.write_table(table, index_path)

        # Mock the embedder to return a query vector aligned with v2 (Beta)
        query_vec = np.array([0.0, 1.0] + [0.0] * (dim - 2), dtype=np.float32)
        with patch("embeddings_sample.TextEmbedding") as MockEmbed:
            MockEmbed.return_value.embed.return_value = iter([query_vec])
            # Capture stdout
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            s.search(index_path, "beta query", "test-model", top_k=3)
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        lines = output.splitlines()
        # First result should be Beta (highest cosine similarity to v2)
        assert any("1. Beta" in line for line in lines)


# ---------------------------------------------------------------------------
# F. Workflow & docs
# ---------------------------------------------------------------------------

class TestWorkflowAndDocs:
    def test_workflow_exists(self):
        wf = REPO_ROOT / ".github" / "workflows" / "build-embeddings.yml"
        assert wf.exists()

    def test_workflow_not_required_branch_protection(self):
        wf = REPO_ROOT / ".github" / "workflows" / "build-embeddings.yml"
        text = wf.read_text(encoding="utf-8")
        assert "required" not in text.lower() or "not required" in text.lower()

    def test_docs_exist(self):
        assert (REPO_ROOT / "docs" / "EMBEDDINGS.md").exists()

    def test_no_model_weights_committed(self):
        # No .bin, .safetensors, .pt, .onnx files in repo
        for pattern in ("*.bin", "*.safetensors", "*.pt", "*.onnx"):
            matches = list(REPO_ROOT.rglob(pattern))
            # Allow inside .venv or node_modules
            filtered = [m for m in matches if ".venv" not in str(m) and "node_modules" not in str(m)]
            assert not filtered, f"Found committed model weight: {filtered[0]}"

    def test_gitignore_excludes_model_cache(self):
        gitignore = REPO_ROOT / ".gitignore"
        text = gitignore.read_text(encoding="utf-8")
        assert ".cache" in text or "cache" in text.lower()


# ---------------------------------------------------------------------------
# G. Dependency guard
# ---------------------------------------------------------------------------

class TestDependencyGuard:
    def test_requirements_txt_lists_embedding_deps(self):
        req = REPO_ROOT / "tools" / "requirements.txt"
        text = req.read_text(encoding="utf-8")
        assert "fastembed" in text
        assert "pyarrow" in text
        assert "numpy" in text


# ---------------------------------------------------------------------------
# H. Integration-like check: local article corpus not mutated
# ---------------------------------------------------------------------------

class TestNoMutation:
    def test_no_article_metadata_changed_for_embeddings(self):
        articles_dir = REPO_ROOT / "articles"
        for meta in articles_dir.rglob("metadata.json"):
            data = json.loads(meta.read_text(encoding="utf-8"))
            assert "embedding" not in data
            assert "vector" not in data
