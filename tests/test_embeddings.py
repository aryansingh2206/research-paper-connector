"""
Tests for embedding generation
"""
import pytest
import numpy as np
from src.embeddings import EmbeddingModel


class TestEmbeddingModel:
    """Test suite for embedding model"""
    
    @pytest.fixture
    def model(self):
        """Create test model"""
        return EmbeddingModel()
    
    def test_model_initialization(self, model):
        """Test model loads correctly"""
        assert model.model is not None
        assert model.dimension == 384  # all-MiniLM-L6-v2 dimension
    
    def test_embed_single_text(self, model):
        """Test single text embedding"""
        text = "This is a test sentence about machine learning."
        embedding = model.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_batch(self, model):
        """Test batch embedding"""
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        
        embeddings = model.embed_batch(texts, show_progress=False)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
    
    def test_compute_similarity(self, model):
        """Test similarity computation"""
        text1 = "Machine learning is fascinating."
        text2 = "Deep learning is interesting."
        text3 = "The weather is nice today."
        
        emb1 = model.embed_text(text1)
        emb2 = model.embed_text(text2)
        emb3 = model.embed_text(text3)
        
        sim_12 = model.compute_similarity(emb1, emb2)
        sim_13 = model.compute_similarity(emb1, emb3)
        
        # Related texts should be more similar
        assert sim_12 > sim_13
        assert -1 <= sim_12 <= 1
        assert -1 <= sim_13 <= 1
    
    def test_empty_text(self, model):
        """Test handling of empty text"""
        embedding = model.embed_text("")
        assert len(embedding) == 384


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
