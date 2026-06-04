"""Behavior + value-safety tests for tools/check_provider_keys_present.py.

Network-free. These assert both the exit-code contract (fail-closed on a missing
*required* key; DeepSeek optional) and the value-safety contract (no secret
value / prefix / suffix / hash is ever printed — only the key NAME and the
literal present/absent).
"""

from __future__ import annotations

import hashlib

import pytest

# tools/ is added to sys.path by tools/tests/conftest.py.
import check_provider_keys_present as cpk

REQUIRED = ["MINIMAX_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
OPTIONAL = ["DEEPSEEK_API_KEY"]
ALL_KEYS = REQUIRED + OPTIONAL

# A clearly-fake, low-entropy sentinel — deliberately NOT shaped like a real
# token (no `sk-`/`Bearer`/hex blob) so secret scanners never flag it — used to
# prove the helper never echoes a value in any form.
SENTINEL = "FAKE_PRESENCE_TEST_VALUE_do_not_flag"
SENTINEL_SHA = hashlib.sha256(SENTINEL.encode()).hexdigest()


def _clear(monkeypatch):
    for key in ALL_KEYS:
        monkeypatch.delenv(key, raising=False)


def _argv():
    return ["--required", *REQUIRED, "--optional", *OPTIONAL]


def _assert_value_safe(out: str):
    assert SENTINEL not in out, "helper leaked the raw secret value"
    assert SENTINEL[:8] not in out, "helper leaked a value prefix"
    assert SENTINEL[-8:] not in out, "helper leaked a value suffix"
    assert SENTINEL_SHA not in out, "helper leaked a value hash"
    assert SENTINEL_SHA[:8] not in out, "helper leaked a value-hash prefix"


def test_all_required_present_exits_zero(monkeypatch, capsys):
    _clear(monkeypatch)
    for key in REQUIRED:
        monkeypatch.setenv(key, SENTINEL)
    rc = cpk.main(_argv())
    out = capsys.readouterr().out
    assert rc == 0
    for key in REQUIRED:
        assert f"{key}: present" in out
    _assert_value_safe(out)


def test_required_present_with_deepseek_absent_exits_zero(monkeypatch, capsys):
    _clear(monkeypatch)
    for key in REQUIRED:
        monkeypatch.setenv(key, SENTINEL)
    # DEEPSEEK_API_KEY intentionally left unset.
    rc = cpk.main(_argv())
    out = capsys.readouterr().out
    assert rc == 0, "optional DeepSeek absent must NOT fail the smoke"
    assert "DEEPSEEK_API_KEY: absent" in out


def test_optional_deepseek_present_exits_zero(monkeypatch, capsys):
    _clear(monkeypatch)
    for key in ALL_KEYS:
        monkeypatch.setenv(key, SENTINEL)
    rc = cpk.main(_argv())
    out = capsys.readouterr().out
    assert rc == 0
    assert "DEEPSEEK_API_KEY: present" in out
    _assert_value_safe(out)


@pytest.mark.parametrize("missing", REQUIRED)
def test_one_required_missing_fails_closed(monkeypatch, capsys, missing):
    _clear(monkeypatch)
    for key in REQUIRED:
        if key != missing:
            monkeypatch.setenv(key, SENTINEL)
    rc = cpk.main(_argv())
    out = capsys.readouterr().out
    assert rc != 0, f"missing required {missing} must fail closed (non-zero exit)"
    assert f"{missing}: absent" in out
    assert missing in out  # the NAME is reported (key names are safe to print)
    _assert_value_safe(out)


def test_all_absent_fails_closed_and_value_safe(monkeypatch, capsys):
    _clear(monkeypatch)
    rc = cpk.main(_argv())
    out = capsys.readouterr().out
    assert rc != 0
    for key in REQUIRED:
        assert f"{key}: absent" in out
    _assert_value_safe(out)


def test_output_is_only_names_and_present_absent(monkeypatch, capsys):
    _clear(monkeypatch)
    for key in ALL_KEYS:
        monkeypatch.setenv(key, SENTINEL)
    cpk.main(_argv())
    out = capsys.readouterr().out
    key_lines = [ln for ln in out.splitlines() if ln.lstrip().startswith("- ")]
    assert len(key_lines) == len(ALL_KEYS)
    for line in key_lines:
        assert ("present" in line) or ("absent" in line)
    _assert_value_safe(out)


def test_defaults_match_d7_policy(monkeypatch, capsys):
    """With no CLI args, the helper's own defaults encode the D7 key policy."""
    _clear(monkeypatch)
    for key in REQUIRED:
        monkeypatch.setenv(key, SENTINEL)
    rc = cpk.main([])  # rely on DEFAULT_REQUIRED / DEFAULT_OPTIONAL
    out = capsys.readouterr().out
    assert rc == 0
    assert set(cpk.DEFAULT_REQUIRED) == set(REQUIRED)
    assert "DEEPSEEK_API_KEY" in cpk.DEFAULT_OPTIONAL
    assert "DEEPSEEK_API_KEY" not in cpk.DEFAULT_REQUIRED
    _assert_value_safe(out)
