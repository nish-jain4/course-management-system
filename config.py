import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "black")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234")
    DB_NAME = os.environ.get("DB_NAME", "mydb")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@cms.demo")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
