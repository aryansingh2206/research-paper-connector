#!/usr/bin/env python3
"""
Setup verification script for Research Paper Idea Connector.

This script verifies:
- Endee connectivity
- Implicit collection readiness
- Embedding model loading
- Embedding generation
- Presence of sample papers
"""

import sys
from pathlib import Path

# --------------------------------------------------
# Ensure project root (/app) is on PYTHONPATH
# This allows `import src.*` to work correctly
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.endee_client import EndeeClient
from src.embeddings import get_embedding_model
from src.config import settings


def check_endee():
    """Check if Endee is accessible"""
    print("🔍 Checking Endee connection...")

    try:
        client = EndeeClient()
        if client.health_check():
            print("✅ Endee is running and accessible")
            return True
        print("❌ Endee is not responding")
        return False
    except Exception as e:
        print(f"❌ Cannot connect to Endee: {e}")
        return False


def check_collection():
    """
    Check collection readiness.

    Endee creates collections implicitly on first insert,
    so this is treated as a logical readiness check.
    """
    print("\n📦 Checking Endee collection (implicit creation)...")

    try:
        client = EndeeClient()
        # No-op call for compatibility
        if client.create_collection():
            print(f"✅ Collection '{settings.ENDEE_COLLECTION}' ready (implicit)")
            return True
        print("❌ Collection check failed")
        return False
    except Exception as e:
        print(f"❌ Error during collection check: {e}")
        return False


def load_embedding_model():
    """Test embedding model loading"""
    print("\n🤖 Loading embedding model...")

    try:
        model = get_embedding_model()
        print(f"✅ Model loaded: {model.model_name}")
        print(f"   Dimension: {model.dimension}")
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False


def test_embedding():
    """Test embedding generation"""
    print("\n🧪 Testing embedding generation...")

    try:
        model = get_embedding_model()
        test_text = "This is a test sentence for the Research Paper Connector."
        embedding = model.embed_text(test_text)

        print(f"✅ Generated {len(embedding)}-dimensional embedding")
        print(f"   Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
        return True
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False


def check_sample_papers():
    """Check if sample papers exist"""
    print("\n📚 Checking sample papers...")

    sample_dir = PROJECT_ROOT / "data" / "sample_papers"

    if not sample_dir.exists():
        print("⚠️  Sample papers directory not found")
        print("   Expected at: data/sample_papers/")
        return False

    papers = list(sample_dir.glob("*.txt"))
    if not papers:
        print("⚠️  Sample papers directory exists but is empty")
        return False

    print(f"✅ Found {len(papers)} sample papers")
    for paper in papers:
        print(f"   - {paper.name}")

    return True


def main():
    print("=" * 80)
    print("Research Paper Idea Connector - Setup Verification")
    print("=" * 80)

    results = []

    results.append(("Endee Connection", check_endee()))
    results.append(("Collection Readiness", check_collection()))
    results.append(("Embedding Model", load_embedding_model()))
    results.append(("Embedding Test", test_embedding()))
    results.append(("Sample Papers", check_sample_papers()))

    print("\n" + "=" * 80)
    print("SETUP VERIFICATION SUMMARY")
    print("=" * 80)

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    all_passed = all(success for _, success in results)

    print("\n" + "=" * 80)

    if all_passed:
        print("🎉 All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Ingest sample papers:")
        print("   docker-compose exec app python scripts/ingest_papers.py data/sample_papers/")
        print("2. Open the UI at http://localhost:8501")
    else:
        print("⚠️  Some checks failed.")
        print("   Review the messages above to resolve missing setup steps.")

    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
