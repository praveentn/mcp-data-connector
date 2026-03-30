"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """All settings are read from environment variables (case-insensitive)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Azure OpenAI — field names match env var names case-insensitively
    azure_openai_api_key: str
    azure_openai_endpoint: str
    azure_deployment: str = "gpt-4o-mini"
    api_version: str = "2024-05-01-preview"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "mcpdataconnector"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    # Service ports
    backend_port: int = 7790
    mcp_server_port: int = 7792
    frontend_port: int = 7791
    mcp_inspector_port: int = 6274

    # MCP server URL (where backend's MCP client connects)
    mcp_server_url: str = "http://localhost:7792/sse"

    # File tools base path
    files_base_path: str = "./data/files"

    @property
    def database_url(self) -> str:
        """Async database URL for SQLAlchemy + asyncpg."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
