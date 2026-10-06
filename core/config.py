import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "NSUT AI-Powered University Student Services Assistant"
    VERSION: str = "1.0.0"
    
    # Storage paths
    SQLITE_PATH: str = str(BASE_DIR / "data" / "student_assistant.db")
    CHROMA_PATH: str = str(BASE_DIR / "data" / "chroma")
    DOCS_DIR: str = str(BASE_DIR / "data" / "university_docs")
    
    # LLM Settings
    HUGGINGFACE_ACCESS_TOKEN: str = os.getenv("HUGGINGFACE_ACCESS_TOKEN", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
    MOCK_LLM: bool = False
    
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # Fallback Cloud LLM (OpenAI / Gemini compatible if configured)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Embeddings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
