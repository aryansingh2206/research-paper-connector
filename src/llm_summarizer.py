"""
Optional LLM integration for summarization and analysis.
Supports OpenAI and Anthropic models.
"""
import logging
from typing import List, Optional
from enum import Enum

from src.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    NONE = "none"


class LLMSummarizer:
    """
    Optional LLM integration for result summarization.
    
    This is a lightweight wrapper that can be enabled/disabled.
    The core system works without this component.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider = LLMProvider(provider.lower())
        self.model = model or settings.LLM_MODEL
        self.enabled = settings.USE_LLM_SUMMARIZATION
        
        if not self.enabled:
            logger.info("LLM summarization disabled")
            return
        
        # Initialize client based on provider
        if self.provider == LLMProvider.OPENAI:
            self._init_openai(api_key)
        elif self.provider == LLMProvider.ANTHROPIC:
            self._init_anthropic(api_key)
    
    def _init_openai(self, api_key: Optional[str] = None):
        """Initialize OpenAI client"""
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key or settings.OPENAI_API_KEY
            )
            logger.info("OpenAI client initialized")
        except ImportError:
            logger.error("OpenAI package not installed")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.enabled = False
    
    def _init_anthropic(self, api_key: Optional[str] = None):
        """Initialize Anthropic client"""
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=api_key or settings.ANTHROPIC_API_KEY
            )
            logger.info("Anthropic client initialized")
        except ImportError:
            logger.error("Anthropic package not installed")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
            self.enabled = False
    
    def summarize_search_results(
        self,
        query: str,
        results: List[dict],
        max_results: int = 5
    ) -> Optional[str]:
        """
        Generate a summary of search results using LLM.
        
        Args:
            query: Original search query
            results: List of search result dictionaries
            max_results: Maximum results to include in summary
        
        Returns:
            Summary text or None if disabled/failed
        """
        if not self.enabled:
            return None
        
        try:
            # Prepare context from results
            context = self._prepare_context(results[:max_results])
            
            # Create prompt
            prompt = f"""Based on the following research paper excerpts, provide a brief summary addressing the query: "{query}"

Excerpts:
{context}

Summary:"""
            
            # Call LLM
            if self.provider == LLMProvider.OPENAI:
                return self._call_openai(prompt)
            elif self.provider == LLMProvider.ANTHROPIC:
                return self._call_anthropic(prompt)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None
    
    def _prepare_context(self, results: List[dict], max_chars: int = 2000) -> str:
        """Prepare context string from results"""
        context_parts = []
        total_chars = 0
        
        for idx, result in enumerate(results, 1):
            text = result.get("chunk_text", "")
            title = result.get("paper_title", "Unknown")
            
            excerpt = f"{idx}. From '{title}':\n{text}\n"
            
            if total_chars + len(excerpt) > max_chars:
                break
            
            context_parts.append(excerpt)
            total_chars += len(excerpt)
        
        return "\n".join(context_parts)
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant helping to summarize findings from academic papers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
    
    def identify_contradictions(
        self,
        results: List[dict]
    ) -> Optional[str]:
        """
        Analyze results for contradictions.
        
        Args:
            results: List of search result dictionaries
        
        Returns:
            Analysis text or None
        """
        if not self.enabled or len(results) < 2:
            return None
        
        context = self._prepare_context(results)
        
        prompt = f"""Analyze these research paper excerpts and identify any contradictions or conflicting findings:

{context}

Analysis:"""
        
        if self.provider == LLMProvider.OPENAI:
            return self._call_openai(prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._call_anthropic(prompt)
