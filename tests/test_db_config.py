from __future__ import annotations

import importlib

import pytest

import internal.db as db_module


def test_builds_mysql_url_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_BACKEND", raising=False)
    monkeypatch.setenv("DB_USER", "ocuwell_app")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_NAME", "ocuwell_gateway")

    assert db_module._build_database_url() == (
        "mysql+pymysql://ocuwell_app:secret@localhost:3306/ocuwell_gateway"
    )


def test_explicit_database_url_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./local_test.db")
    monkeypatch.setenv("DB_BACKEND", "azure_sql")

    assert db_module._build_database_url() == "sqlite:///./local_test.db"


def test_builds_azure_sql_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_BACKEND", "azure_sql")
    monkeypatch.setenv("AZURE_SQL_AUTH_MODE", "entra")
    monkeypatch.setenv("AZURE_SQL_SERVER", "ocuwell-gateway-dev.database.windows.net")
    monkeypatch.setenv("AZURE_SQL_PORT", "1433")
    monkeypatch.setenv("AZURE_SQL_DATABASE", "ocuwell_gateway")
    monkeypatch.setenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    monkeypatch.setenv("AZURE_SQL_ENCRYPT", "yes")
    monkeypatch.setenv("AZURE_SQL_TRUST_SERVER_CERTIFICATE", "no")

    url = db_module._build_database_url()

    assert url.startswith("mssql+pyodbc://@")
    assert "ocuwell-gateway-dev.database.windows.net:1433/ocuwell_gateway" in url
    assert "driver=ODBC+Driver+18+for+SQL+Server" in url
    assert "Encrypt=yes" in url
    assert "TrustServerCertificate=no" in url


def test_azure_sql_requires_all_core_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_BACKEND", "azure_sql")
    monkeypatch.setenv("AZURE_SQL_AUTH_MODE", "entra")
    monkeypatch.delenv("AZURE_SQL_SERVER", raising=False)
    monkeypatch.setenv("AZURE_SQL_DATABASE", "ocuwell_gateway")

    with pytest.raises(ValueError):
        db_module._build_database_url()


def test_builds_azure_sql_password_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_BACKEND", "azure_sql")
    monkeypatch.setenv("AZURE_SQL_AUTH_MODE", "sql_password")
    monkeypatch.setenv("AZURE_SQL_SERVER", "ocuwell-gateway-dev.database.windows.net")
    monkeypatch.setenv("AZURE_SQL_PORT", "1433")
    monkeypatch.setenv("AZURE_SQL_DATABASE", "ocuwell_gateway")
    monkeypatch.setenv("AZURE_SQL_USERNAME", "ocuwell_admin")
    monkeypatch.setenv("AZURE_SQL_PASSWORD", "s3cret!")

    url = db_module._build_database_url()

    assert url.startswith("mssql+pyodbc://ocuwell_admin:s3cret%21@")


def test_azure_sql_password_mode_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_BACKEND", "azure_sql")
    monkeypatch.setenv("AZURE_SQL_AUTH_MODE", "sql_password")
    monkeypatch.setenv("AZURE_SQL_SERVER", "ocuwell-gateway-dev.database.windows.net")
    monkeypatch.setenv("AZURE_SQL_DATABASE", "ocuwell_gateway")
    monkeypatch.delenv("AZURE_SQL_USERNAME", raising=False)
    monkeypatch.delenv("AZURE_SQL_PASSWORD", raising=False)

    with pytest.raises(ValueError):
        db_module._build_database_url()


def test_build_azure_sql_token_struct() -> None:
    token_struct = db_module._build_azure_sql_token_struct("abc")

    assert token_struct[:4] == b"\x06\x00\x00\x00"
    assert token_struct[4:] == "abc".encode("utf-16-le")


def test_sqlite_connect_args_applied_on_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./local_test.db")
    reloaded = importlib.reload(db_module)

    try:
        assert reloaded.DATABASE_URL == "sqlite:///./local_test.db"
        assert reloaded.connect_args == {"check_same_thread": False}
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        importlib.reload(db_module)
