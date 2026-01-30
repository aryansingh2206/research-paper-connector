"""
Document processing: PDF parsing, text extraction, and chunking
"""
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document"""
    text: str
    chunk_index: int
    metadata: Dict[str, Any]


class DocumentProcessor:
    """
    Processes research papers (PDF/TXT) into semantic chunks.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Extracted text content
        """
        if PdfReader is None:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")
        
        try:
            reader = PdfReader(pdf_path)
            text = ""
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            
            logger.info(f"Extracted {len(text)} characters from {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """
        Read text from TXT file.
        
        Args:
            txt_path: Path to text file
        
        Returns:
            File content
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            logger.info(f"Read {len(text)} characters from {txt_path}")
            return text
            
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from file (auto-detect format).
        
        Args:
            file_path: Path to document
        
        Returns:
            Extracted text
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return ""
        
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif suffix in ['.txt', '.md']:
            return self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file format: {suffix}")
            # Try reading as text anyway
            return self.extract_text_from_txt(file_path)
    
    def clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw text
        
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers (common patterns)
        text = re.sub(r'\n\d+\n', '\n', text)
        
        # Remove non-ASCII characters (optional)
        # text = text.encode('ascii', 'ignore').decode('ascii')
        
        return text.strip()
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraph-level chunks.
        
        Uses multiple newlines as paragraph delimiters.
        
        Args:
            text: Document text
        
        Returns:
            List of paragraph strings
        """
        # Split on multiple newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out very short paragraphs
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]
        
        return paragraphs
    
    def split_into_chunks(
        self,
        text: str,
        use_paragraphs: bool = True
    ) -> List[str]:
        """
        Split text into semantic chunks with overlap.
        
        Args:
            text: Document text
            use_paragraphs: If True, split by paragraphs first
        
        Returns:
            List of text chunks
        """
        if use_paragraphs:
            # Split into paragraphs first
            paragraphs = self.split_into_paragraphs(text)
            
            # Each paragraph becomes a chunk (or combine small ones)
            chunks = []
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) < self.chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            return chunks
        
        else:
            # Simple character-based chunking with overlap
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + self.chunk_size
                chunk = text[start:end]
                
                if chunk:
                    chunks.append(chunk)
                
                start += self.chunk_size - self.chunk_overlap
            
            return chunks
    
    def process_document(
        self,
        file_path: str,
        paper_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Full pipeline: extract, clean, chunk document.
        
        Args:
            file_path: Path to document file
            paper_id: Unique identifier for the paper
            metadata: Additional metadata (title, authors, etc.)
        
        Returns:
            List of DocumentChunk objects
        """
        logger.info(f"Processing document: {file_path}")
        
        # Extract text
        raw_text = self.extract_text(file_path)
        
        if not raw_text:
            logger.warning(f"No text extracted from {file_path}")
            return []
        
        # Clean text
        clean_text = self.clean_text(raw_text)
        
        # Split into chunks
        chunks = self.split_into_chunks(clean_text, use_paragraphs=True)
        
        # Create DocumentChunk objects
        document_chunks = []
        base_metadata = metadata or {}
        
        for idx, chunk_text in enumerate(chunks):
            chunk_metadata = {
                **base_metadata,
                "paper_id": paper_id,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "chunk_text": chunk_text  # Store for retrieval
            }
            
            document_chunks.append(DocumentChunk(
                text=chunk_text,
                chunk_index=idx,
                metadata=chunk_metadata
            ))
        
        logger.info(f"Created {len(document_chunks)} chunks from {file_path}")
        return document_chunks
