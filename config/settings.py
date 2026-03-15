from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Anthropic
    anthropic_api_key: str = ""

    # 阿里云百炼平台
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/tender_integrity.db"

    # ChromaDB
    chroma_persist_dir: str = "./data/chromadb"

    # Embedding
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32
    embedding_api_batch_size: int = 10  # API 模式批次上限（百炼 text-embedding-v3 最大 10）
    embedding_use_api: bool = False   # True 时使用 API embedding，False 时使用本地模型

    # File storage
    upload_dir: str = "./data/uploads"
    report_dir: str = "./data/reports"

    # LLM
    llm_model: str = "claude-sonnet-4-6"
    llm_provider: str = "anthropic"   # "anthropic" | "dashscope"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # Chunking
    chunk_max_chars: int = 800
    chunk_min_chars: int = 20
    chunk_window_size: int = 600
    chunk_step_size: int = 300

    # Thresholds
    high_risk_threshold: float = 85.0
    medium_risk_threshold: float = 65.0
    low_risk_threshold: float = 45.0

    # Retrieval
    top_k_similar: int = 10
    vector_similarity_threshold: float = 0.55
    whitelist_similarity_threshold: float = 0.88

    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent

    @property
    def config_dir(self) -> Path:
        return self.base_dir / "config"

    @property
    def whitelist_dir(self) -> Path:
        return self.config_dir / "whitelist"


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
