from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):

    # ---------- FastAPI ----------
    api_base_url: str = "http://127.0.0.1:8000"

    # ---------- MCP ----------
    mcp_url: str = "http://127.0.0.1:8001/mcp"

    # ---------- Ollama ----------
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "qwen3:1.7b"
    ollama_embedding_model: str = "qwen3-embedding:0.6b"

    # ---------- Doris ----------
    doris_url: str = "http://127.0.0.1:8030"
    doris_database: str = "bus_agent"
    doris_user: str = "root"
    doris_password: str = ""

    # ---------- RAG ----------
    chroma_dir: str = str(
        BASE_DIR / "data" / "chroma"
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()