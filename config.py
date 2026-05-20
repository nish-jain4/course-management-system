import os
from urllib.parse import parse_qs, unquote, urlparse


SUPPORTED_DB_URL_SCHEMES = {
    "mysql",
    "mysql2",
    "mysql+pymysql",
    "mariadb",
    "mariadb+pymysql",
}


def parse_mysql_database_url(database_url: str | None) -> dict[str, object]:
    if not database_url:
        return {}

    parsed = urlparse(database_url)
    if parsed.scheme.lower() not in SUPPORTED_DB_URL_SCHEMES:
        return {}

    query_params = parse_qs(parsed.query)
    ssl_ca = query_params.get("ssl-ca", [None])[0]

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": unquote(parsed.path.lstrip("/")),
        "ssl_ca": unquote(ssl_ca) if ssl_ca else None,
    }


DATABASE_CONFIG = parse_mysql_database_url(
    os.environ.get("JAWSDB_URL")
    or os.environ.get("JAWSDB_MARIA_URL")
    or os.environ.get("CLEARDB_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "black")
    DB_HOST = str(DATABASE_CONFIG.get("host") or os.environ.get("DB_HOST", "localhost"))
    DB_PORT = int(DATABASE_CONFIG.get("port") or os.environ.get("DB_PORT", "3306"))
    DB_USER = str(DATABASE_CONFIG.get("user") or os.environ.get("DB_USER", "root"))
    DB_PASSWORD = str(DATABASE_CONFIG.get("password") or os.environ.get("DB_PASSWORD", "1234"))
    DB_NAME = str(DATABASE_CONFIG.get("database") or os.environ.get("DB_NAME", "mydb"))
    DB_SSL_CA = DATABASE_CONFIG.get("ssl_ca") or os.environ.get("DB_SSL_CA")
    DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "10"))
    PORT = int(os.environ.get("PORT", "5000"))
    DEBUG = os.environ.get("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@cms.demo")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
