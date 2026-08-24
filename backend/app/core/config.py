"""Application settings, loaded from environment variables (.env in local dev)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_port: int = 8000

    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Dev default points at the mailpit service in docker-compose.yml — no
    # auth, no TLS, nothing to configure to see emails locally. Set
    # smtp_username/smtp_password (e.g. a Gmail address + app password) to
    # switch to a real provider — see app/core/email.py for how that flips
    # on STARTTLS + login.
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "Marketplace Guinée <no-reply@marketplace-guinee.local>"
    smtp_username: str | None = None
    smtp_password: str | None = None

    # Stockage objet (MinIO en dev, S3-compatible) pour les images produit —
    # voir app/core/storage.py. Uniquement le réseau docker interne : l'API
    # est la seule à parler à MinIO directement, le navigateur passe par
    # GET /uploads/images/{key} (voir app/uploads/router.py) plutôt que par
    # une deuxième adresse publique à tenir à jour.
    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_bucket: str = "product-images"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (avoids re-parsing env on every call)."""
    return Settings()
