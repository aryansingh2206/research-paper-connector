"""
Research Paper Idea Connector - Core Module
"""
from src.config import settings
from src.endee_client import EndeeClient
from src.embeddings import get_embedding_model
from src.document_processor import DocumentProcessor
from src.ingestion import IngestionPipeline
from src.search_engine import SearchEngine
from src.llm_summarizer import LLMSummarizer

__version__ = "1.0.0"
__all__ = [
    "settings",
    "EndeeClient",
    "get_embedding_model",
    "DocumentProcessor",
    "IngestionPipeline",
    "SearchEngine",
    "LLMSummarizer",
]
