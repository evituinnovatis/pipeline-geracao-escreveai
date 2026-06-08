from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    database_url: str
    groq_generation_model: str = "openai/gpt-oss-120b"
    aws_region: str = "us-east-1"
    aws_profile: Optional[str] = None
    embedding_model_name: str = "BAAI/bge-m3"
    embedding_use_fp16: bool = True
    embedding_batch_size: int = 12
    embedding_max_length: int = 8192
    embedding_dimensions: int = 1024
    retrieval_top_k: int = 6
    references_dir: str = "referencias_projeto_doc"


def _get_bool(name: str) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "sim"}


def _get_int(name: str) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def load_settings(env_path: str | Path | None = None) -> Settings:
    load_dotenv(dotenv_path=env_path)

    groq_api_key = os.getenv("API_KEY_GROQ_ESCREVEAI_VICTOR")
    database_url = os.getenv("DATABASE_URL")

    missing = [
        name
        for name, value in {
            "API_KEY_GROQ_ESCREVEAI_VICTOR": groq_api_key,
            "DATABASE_URL": database_url,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Variaveis de ambiente ausentes: {missing}")

    return Settings(
        groq_api_key=groq_api_key,
        database_url=database_url,
        groq_generation_model=os.getenv("GROQ_GENERATION_MODEL"),
        aws_region=os.getenv("AWS_REGION"),
        aws_profile=os.getenv("AWS_PROFILE"),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME"),
        embedding_use_fp16=_get_bool("EMBEDDING_USE_FP16"),
        embedding_batch_size=_get_int("EMBEDDING_BATCH_SIZE"),
        embedding_max_length=_get_int("EMBEDDING_MAX_LENGTH"),
        embedding_dimensions=_get_int("EMBEDDING_DIMENSIONS"),
        retrieval_top_k=_get_int("RAG_TOP_K"),
        references_dir=os.getenv("REFERENCES_DIR", "referencias_projeto_doc"),
    )

