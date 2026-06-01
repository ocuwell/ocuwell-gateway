import os
import struct
from collections.abc import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

AZURE_SQL_TOKEN_SCOPE = "https://database.windows.net/.default"
SQL_COPT_SS_ACCESS_TOKEN = 1256


def _build_mysql_database_url() -> str:
    db_user = os.getenv("DB_USER", "ocuwell")
    db_password = os.getenv("DB_PASSWORD", "ocuwell")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "ocuwell_gateway")
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def _build_azure_sql_database_url() -> str:
    server = os.getenv("AZURE_SQL_SERVER", "")
    database = os.getenv("AZURE_SQL_DATABASE", "")
    auth_mode = os.getenv("AZURE_SQL_AUTH_MODE", "entra").lower()
    port = os.getenv("AZURE_SQL_PORT", "1433")
    driver = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    encrypt = os.getenv("AZURE_SQL_ENCRYPT", "yes")
    trust_server_certificate = os.getenv("AZURE_SQL_TRUST_SERVER_CERTIFICATE", "no")

    if not server or not database:
        raise ValueError(
            "AZURE_SQL_SERVER and AZURE_SQL_DATABASE must be set for Azure SQL.",
        )

    query_parts = [
        f"driver={quote_plus(driver)}",
        f"Encrypt={quote_plus(encrypt)}",
        f"TrustServerCertificate={quote_plus(trust_server_certificate)}",
    ]

    if auth_mode == "sql_password":
        username = os.getenv("AZURE_SQL_USERNAME", "")
        password = os.getenv("AZURE_SQL_PASSWORD", "")
        if not username or not password:
            raise ValueError(
                "AZURE_SQL_USERNAME and AZURE_SQL_PASSWORD must be set when "
                "AZURE_SQL_AUTH_MODE=sql_password.",
            )
        return (
            "mssql+pyodbc://"
            f"{quote_plus(username)}:{quote_plus(password)}@"
            f"{server}:{port}/{database}?{'&'.join(query_parts)}"
        )

    if auth_mode != "entra":
        raise ValueError("AZURE_SQL_AUTH_MODE must be either 'entra' or 'sql_password'.")

    return (
        "mssql+pyodbc://"
        f"@{server}:{port}/{database}?{'&'.join(query_parts)}"
    )


def _build_database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    db_backend = os.getenv("DB_BACKEND", "mysql").lower()
    if db_backend == "azure_sql":
        return _build_azure_sql_database_url()

    return _build_mysql_database_url()


DATABASE_URL = _build_database_url()
DB_BACKEND = os.getenv("DB_BACKEND", "mysql").lower()
AZURE_SQL_AUTH_MODE = os.getenv("AZURE_SQL_AUTH_MODE", "entra").lower()

connect_args: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif DATABASE_URL.startswith("mssql+pyodbc"):
    connect_args["timeout"] = int(os.getenv("AZURE_SQL_CONNECTION_TIMEOUT", "30"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)


def _build_azure_sql_token_struct(access_token: str) -> bytes:
    token_bytes = access_token.encode("utf-16-le")
    return struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)


def _get_default_azure_credential():
    credential_mode = os.getenv("AZURE_SQL_CREDENTIAL", "default").lower()
    if credential_mode == "azure_cli":
        from azure.identity import AzureCliCredential

        return AzureCliCredential()

    if credential_mode != "default":
        raise ValueError("AZURE_SQL_CREDENTIAL must be either 'default' or 'azure_cli'.")

    from azure.identity import DefaultAzureCredential

    exclude_interactive_browser = (
        os.getenv("AZURE_SQL_EXCLUDE_INTERACTIVE_BROWSER_CREDENTIAL", "true").lower()
        == "true"
    )
    return DefaultAzureCredential(
        exclude_interactive_browser_credential=exclude_interactive_browser,
    )


def _attach_azure_sql_entra_auth(sqlalchemy_engine) -> None:
    azure_credential = _get_default_azure_credential()

    @event.listens_for(sqlalchemy_engine, "do_connect")
    def provide_token(dialect, conn_rec, cargs, cparams) -> None:  # type: ignore[no-untyped-def]
        cargs[0] = cargs[0].replace(";Trusted_Connection=Yes", "")
        access_token = azure_credential.get_token(AZURE_SQL_TOKEN_SCOPE).token
        cparams["attrs_before"] = {
            SQL_COPT_SS_ACCESS_TOKEN: _build_azure_sql_token_struct(access_token),
        }


if DB_BACKEND == "azure_sql" and AZURE_SQL_AUTH_MODE == "entra":
    _attach_azure_sql_entra_auth(engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
