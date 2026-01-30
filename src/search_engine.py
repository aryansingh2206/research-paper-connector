"""
Search engine: query processing and result ranking
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.config import settings
from src.endee_client import EndeeClient, SearchResult
from src.embeddings import get_embedding_model

logger = logging.getLogger(__name__)


@dataclass
class SearchMatch:
    """Enriched search result with readable format"""
    paper_id: str
    paper_title: str
    chunk_text: str
    chunk_index: int
    similarity_score: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "paper_id": self.paper_id,
            "paper_title": self.paper_title,
            "chunk_text": self.chunk_text,
            "chunk_index": self.chunk_index,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata
        }


class SearchEngine:
    """
    Search engine that uses Endee for semantic similarity search.
    
    Core functionality:
    1. Accept natural language queries
    2. Generate query embeddings
    3. Search Endee for similar vectors
    4. Post-process and rank results
    """
    
    def __init__(
        self,
        endee_client: Optional[EndeeClient] = None,
        top_k: int = None
    ):
        self.endee_client = endee_client or EndeeClient()
        self.embedding_model = get_embedding_model()
        self.top_k = top_k or settings.TOP_K_RESULTS
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_similarity: Optional[float] = None
    ) -> List[SearchMatch]:
        """
        Perform semantic search.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of SearchMatch objects
        """
        try:
            k = top_k or self.top_k
            threshold = min_similarity or settings.SIMILARITY_THRESHOLD
            
            logger.info(f"Searching for: '{query}'")
            
            # Step 1: Generate query embedding
            query_embedding = self.embedding_model.embed_text(query)
            
            # Step 2: Search in Endee
            raw_results = self.endee_client.search(
                query_vector=query_embedding,
                top_k=k,
                filter_metadata=filter_metadata
            )
            
            # Step 3: Convert to SearchMatch objects and filter by threshold
            matches = []
            for result in raw_results:
                if result.score >= threshold:
                    match = self._convert_to_search_match(result)
                    if match:
                        matches.append(match)
            
            logger.info(f"Found {len(matches)} matches above threshold {threshold}")
            return matches
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _convert_to_search_match(self, result: SearchResult) -> Optional[SearchMatch]:
        """Convert Endee SearchResult to SearchMatch"""
        try:
            metadata = result.metadata
            
            return SearchMatch(
                paper_id=metadata.get("paper_id", "unknown"),
                paper_title=metadata.get("title", "Untitled"),
                chunk_text=metadata.get("chunk_text", ""),
                chunk_index=metadata.get("chunk_index", 0),
                similarity_score=result.score,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error converting result: {e}")
            return None
    
    def find_related_papers(
        self,
        paper_id: str,
        top_k: int = 5
    ) -> List[SearchMatch]:
        """
        Find papers related to a given paper.
        
        Uses the first chunk of the paper as the query.
        
        Args:
            paper_id: Paper ID to find related papers for
            top_k: Number of related papers to return
        
        Returns:
            List of related paper chunks
        """
        try:
            # Get the first chunk of the target paper
            vector_id = f"{paper_id}_chunk_0"
            vector_data = self.endee_client.get_vector(vector_id)
            
            if not vector_data:
                logger.warning(f"Paper {paper_id} not found")
                return []
            
            # Use its vector for similarity search
            query_vector = vector_data.get("vector", [])
            
            raw_results = self.endee_client.search(
                query_vector=query_vector,
                top_k=top_k * 3  # Get more to filter out same paper
            )
            
            # Filter out chunks from the same paper
            matches = []
            seen_papers = set()
            
            for result in raw_results:
                result_paper_id = result.metadata.get("paper_id")
                
                # Skip chunks from the same paper
                if result_paper_id == paper_id:
                    continue
                
                # Skip if we already have results from this paper
                if result_paper_id in seen_papers:
                    continue
                
                match = self._convert_to_search_match(result)
                if match:
                    matches.append(match)
                    seen_papers.add(result_paper_id)
                
                if len(matches) >= top_k:
                    break
            
            logger.info(f"Found {len(matches)} related papers for {paper_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding related papers: {e}")
            return []
    
    def find_contradictions(
        self,
        query: str,
        top_k: int = 10
    ) -> List[SearchMatch]:
        """
        Find potentially contradictory statements.
        
        Strategy: Search for the query, then search for negated concepts.
        This is a simplified approach - a production system would use
        more sophisticated NLI models.
        
        Args:
            query: Query describing a concept or finding
            top_k: Number of results
        
        Returns:
            List of potentially contradictory passages
        """
        # Search with negation keywords
        negation_query = f"NOT {query} OR contrary OR opposite OR different from"
        
        logger.info(f"Searching for contradictions to: '{query}'")
        return self.search(negation_query, top_k=top_k)
    
    def aggregate_results_by_paper(
        self,
        matches: List[SearchMatch]
    ) -> Dict[str, List[SearchMatch]]:
        """
        Group search results by paper ID.
        
        Args:
            matches: List of search matches
        
        Returns:
            Dictionary mapping paper_id to list of matches
        """
        aggregated = {}
        
        for match in matches:
            paper_id = match.paper_id
            if paper_id not in aggregated:
                aggregated[paper_id] = []
            aggregated[paper_id].append(match)
        
        # Sort each paper's matches by score
        for paper_id in aggregated:
            aggregated[paper_id].sort(
                key=lambda m: m.similarity_score,
                reverse=True
            )
        
        return aggregated
    
    def format_results(
        self,
        matches: List[SearchMatch],
        max_text_length: int = 300
    ) -> str:
        """
        Format search results for display.
        
        Args:
            matches: List of search matches
            max_text_length: Maximum text length to display
        
        Returns:
            Formatted string
        """
        if not matches:
            return "No results found."
        
        output = []
        output.append(f"\nFound {len(matches)} matches:\n")
        output.append("=" * 80)
        
        for idx, match in enumerate(matches, 1):
            # Truncate text if too long
            text = match.chunk_text
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            
            output.append(f"\n{idx}. Paper: {match.paper_title}")
            output.append(f"   Paper ID: {match.paper_id}")
            output.append(f"   Similarity: {match.similarity_score:.4f}")
            output.append(f"   Chunk {match.chunk_index + 1}:")
            output.append(f"   {text}")
            output.append("-" * 80)
        
        return "\n".join(output)
