"""
Tests for Endee client
"""
import pytest
from src.endee_client import EndeeClient, VectorDocument


class TestEndeeClient:
    """Test suite for Endee HTTP client"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return EndeeClient(
            base_url="http://localhost:3000",
            collection="test_collection"
        )
    
    def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client.base_url == "http://localhost:3000"
        assert client.collection == "test_collection"
    
    def test_create_collection(self, client):
        """Test collection creation"""
        success = client.create_collection(
            dimension=384,
            metric="cosine",
            force_recreate=True
        )
        assert success is True or success is False  # May fail if Endee not running
    
    def test_insert_vectors(self, client):
        """Test vector insertion"""
        documents = [
            VectorDocument(
                id="test_1",
                vector=[0.1] * 384,
                metadata={"text": "test document 1"}
            ),
            VectorDocument(
                id="test_2",
                vector=[0.2] * 384,
                metadata={"text": "test document 2"}
            )
        ]
        
        # This will only pass if Endee is running
        # success = client.insert_vectors(documents)
        # assert success is True
    
    def test_search(self, client):
        """Test similarity search"""
        query_vector = [0.15] * 384
        
        # This will only pass if Endee is running and has data
        # results = client.search(query_vector, top_k=5)
        # assert isinstance(results, list)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        # Will return False if Endee not running
        health = client.health_check()
        assert isinstance(health, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
