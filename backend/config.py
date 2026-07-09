import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # LLM 配置
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    # Embedding 配置
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # 路径配置
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    KNOWLEDGE_FILE: str = "./data/knowledge_base.json"
    TEST_DATA_FILE: str = "./data/test_banners.json"

    # RAG 配置
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))
    RAG_DISTANCE_THRESHOLD: float = float(os.getenv("RAG_DISTANCE_THRESHOLD", "1.5"))
    RAG_FETCH_K: int = int(os.getenv("RAG_FETCH_K", "10"))


config = Config()
