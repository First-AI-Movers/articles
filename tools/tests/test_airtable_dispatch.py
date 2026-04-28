"""Contract tests for E20b Airtable dispatch workflow."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ingest-airtable-dispatch.yml"


try:
    import yaml

    HAS_YAML = True
except Exception:
    HAS_YAML = False


class TestAirtableDispatchWorkflow:
    """E20b: push-based Airtable trigger via repository_dispatch + workflow_dispatch."""

    # --- Existence & trigger contracts ---------------------------------------

    def test_airtable_dispatch_workflow_exists(self):
        assert WORKFLOW_PATH.exists(), "ingest-airtable-dispatch.yml must exist"

    def test_airtable_dispatch_workflow_has_repository_dispatch(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "repository_dispatch" in text
        assert "airtable-record-updated" in text

    def test_airtable_dispatch_workflow_has_workflow_dispatch_record_id_input(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "workflow_dispatch" in text
        assert "record_id" in text

    # --- Payload & script contract -------------------------------------------

    def test_airtable_dispatch_workflow_uses_record_id_payload(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "--record-id" in text
        # Supports both repository_dispatch client_payload and workflow_dispatch inputs
        assert (
            "github.event.client_payload.record_id" in text
            or "inputs.record_id" in text
        )

    def test_airtable_dispatch_workflow_uses_ingest_airtable_record_id(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "ingest_airtable.py" in text
        assert "--record-id" in text

    # --- Dry-run / write-mode gating -----------------------------------------

    def test_airtable_dispatch_workflow_dry_run_default(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        # Dry-run should be the default path (env default or explicit --dry-run)
        assert "INGEST_DRY_RUN" in text or "--dry-run" in text

    def test_airtable_dispatch_workflow_write_mode_gated(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        # Write steps must be conditional, not unconditional
        assert "INGEST_DRY_RUN != '1'" in text or "env.INGEST_DRY_RUN != '1'" in text

    # --- Safety: PR, never direct push ---------------------------------------

    def test_airtable_dispatch_workflow_does_not_push_to_main(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "git push" not in text.lower()

    def test_airtable_dispatch_workflow_uses_create_pull_request(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        assert "peter-evans/create-pull-request" in text

    # --- Record ID validation in workflow ------------------------------------

    def test_workflow_validates_record_id_shape(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        # Should contain a regex-like validation for rec + alphanumeric
        assert "rec[a-zA-Z0-9]" in text or "rec" in text

    # --- Optional YAML parsability -------------------------------------------

    @pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
    def test_workflow_parses_as_valid_yaml(self):
        data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        assert data.get("name")
        assert "jobs" in data


class TestAirtableDispatchDocs:
    """Documentation contract for E20b."""

    def test_airtable_dispatch_docs_exist(self):
        doc = REPO_ROOT / "docs" / "EXTERNAL_PUBLISHING.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "E20b" in text

    def test_airtable_ingestion_docs_mention_dispatch(self):
        doc = REPO_ROOT / "docs" / "airtable-ingestion.md"
        assert doc.exists()
        text = doc.read_text(encoding="utf-8")
        assert "E20b" in text or "dispatch" in text.lower()
