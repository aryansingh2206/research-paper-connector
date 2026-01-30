"""
Ingestion pipeline: orchestrates document processing, embedding, and Endee storage
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid

from src.endee_client import EndeeClient, VectorDocument
from src.embeddings import get_embedding_model
from src.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

# Absolute project root inside Docker container
PROJECT_ROOT = Path("/app")


class IngestionPipeline:
    """
    End-to-end pipeline for ingesting research papers into Endee.
    """

    def __init__(
        self,
        endee_client: Optional[EndeeClient] = None,
        initialize_collection: bool = True
    ):
        self.endee_client = endee_client or EndeeClient()
        self.embedding_model = get_embedding_model()
        self.document_processor = DocumentProcessor()

        if initialize_collection:
            self._initialize_collection()

    # --------------------------------------------------
    # Collection init (implicit, Endee-native)
    # --------------------------------------------------
    def _initialize_collection(self):
        logger.info("Initializing Endee collection (implicit)...")
        self.endee_client.create_collection(
            dimension=self.embedding_model.dimension,
            metric="cosine",
            force_recreate=False
        )
        logger.info("Collection ready (implicit)")

    # --------------------------------------------------
    # Single paper ingestion
    # --------------------------------------------------
    def ingest_single_paper(
        self,
        file_path: str,
        paper_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        try:
            paper_id = paper_id or str(uuid.uuid4())
            metadata = metadata or {}

            metadata["file_path"] = file_path
            metadata["file_name"] = Path(file_path).name

            logger.info(f"Ingesting paper {paper_id}: {file_path}")

            chunks = self.document_processor.process_document(
                file_path=file_path,
                paper_id=paper_id,
                metadata=metadata
            )

            if not chunks:
                logger.warning(f"No chunks created for {file_path}")
                return False

            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_model.embed_batch(texts=texts)

            vectors: List[VectorDocument] = []
            for chunk, embedding in zip(chunks, embeddings):
                vectors.append(
                    VectorDocument(
                        id=f"{paper_id}_chunk_{chunk.chunk_index}",
                        vector=embedding,
                        metadata=chunk.metadata
                    )
                )

            success = self.endee_client.insert_vectors(vectors)

            if success:
                logger.info(
                    f"Successfully ingested {len(vectors)} chunks from {file_path}"
                )
            return success

        except Exception as e:
            logger.exception(f"Failed to ingest {file_path}: {e}")
            return False

    # --------------------------------------------------
    # Directory ingestion (FINAL, DETERMINISTIC)
    # --------------------------------------------------
    def ingest_from_directory(
        self,
        directory: str,
        metadata_extractor: Optional[callable] = None
    ) -> Dict[str, bool]:
        """
        Ingest all .txt and .pdf files from a directory.

        - Uses absolute paths
        - Uses iterdir() (no glob)
        - Works identically on Windows/Linux/Docker
        """

        directory_path = (PROJECT_ROOT / directory).resolve()
        logger.info(f"Resolved ingestion directory to: {directory_path}")

        if not directory_path.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return {}

        # 🔥 EXPLICIT DIRECTORY WALK (NO GLOB)
        files: List[Path] = []
        for item in directory_path.iterdir():
            if item.is_file() and item.suffix.lower() in {".txt", ".pdf"}:
                files.append(item)

        files.sort()

        logger.info(f"Files discovered: {[f.name for f in files]}")
        logger.info(f"Found {len(files)} files for ingestion")

        results: Dict[str, bool] = {}

        for file_path in files:
            metadata = (
                metadata_extractor(file_path)
                if metadata_extractor
                else {
                    "title": file_path.stem,
                    "source": "local_file"
                }
            )

            results[str(file_path)] = self.ingest_single_paper(
                file_path=str(file_path),
                metadata=metadata
            )

        logger.info(
            f"Ingestion complete: {sum(results.values())}/{len(results)} papers successful"
        )
        return results
