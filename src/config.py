"""
Configuration management for Research Paper Connector
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Endee Configuration
    ENDEE_HOST: str = "localhost"
    ENDEE_PORT: int = 3000
    ENDEE_COLLECTION: str = "research_papers"
    ENDEE_DIMENSION: int = 384  # Matches all-MiniLM-L6-v2 output
    
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32
    
    # Document Processing
    CHUNK_SIZE: int = 500  # Characters per paragraph chunk
    CHUNK_OVERLAP: int = 50
    MAX_PARAGRAPHS_PER_PAPER: int = 500
    
    # Search Configuration
    TOP_K_RESULTS: int = 10
    SIMILARITY_THRESHOLD: float = 0.5
    
    # Optional LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    USE_LLM_SUMMARIZATION: bool = False
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    # Application Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def endee_base_url(self) -> str:
        """Construct Endee base URL"""
        return f"http://{self.ENDEE_HOST}:{self.ENDEE_PORT}"
    
    def validate_endee_config(self) -> bool:
        """Validate Endee configuration"""
        return bool(self.ENDEE_HOST and self.ENDEE_PORT > 0)


# Global settings instance
settings = Settings()
