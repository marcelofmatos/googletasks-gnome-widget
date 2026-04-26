"""load_credentials: sinaliza corretamente necessidade de auth e erro de libs."""
import pytest

import main
from main import NeedsAuthError, load_credentials


def test_raises_import_error_when_google_libs_missing(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_LIBS_OK", False)
    with pytest.raises(ImportError):
        load_credentials()


def test_raises_needs_auth_when_credentials_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "GOOGLE_LIBS_OK", True)
    monkeypatch.setattr(main, "CREDENTIALS_FILE", str(tmp_path / "missing.json"))
    with pytest.raises(NeedsAuthError) as exc:
        load_credentials()
    assert "no_credentials" in str(exc.value)


def test_raises_needs_auth_when_token_missing(monkeypatch, tmp_path):
    creds = tmp_path / "credentials.json"
    creds.write_text("{}")
    monkeypatch.setattr(main, "GOOGLE_LIBS_OK", True)
    monkeypatch.setattr(main, "CREDENTIALS_FILE", str(creds))
    monkeypatch.setattr(main, "TOKEN_FILE", str(tmp_path / "missing_token.json"))
    with pytest.raises(NeedsAuthError):
        load_credentials()
