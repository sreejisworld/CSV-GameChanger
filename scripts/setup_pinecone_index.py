"""
Pinecone Index Setup Script for CSV-GameChanger Knowledge Base.

Creates the 'csv-knowledge-base' index with dimension 1536 for OpenAI embeddings.

:requirement: URS-5.8 - System shall verify index exists before upserting.
"""

import os
import sys

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    print("ERROR: pinecone-client not installed")
    print("Run: pip install pinecone-client")
    sys.exit(1)


# Configuration
INDEX_NAME = "csv-knowledge-base"
DIMENSION = 1536  # OpenAI text-embedding-3-small/ada-002
METRIC = "cosine"
CLOUD = "aws"
REGION = "us-east-1"


def create_index() -> bool:
    """
    Create the csv-knowledge-base Pinecone index.

    :return: True if index created or already exists, False on error.
    :requirement: URS-5.8 - System shall verify index exists before upserting.
    """
    api_key = os.getenv("PINECONE_API_KEY")

    if not api_key:
        print("ERROR: PINECONE_API_KEY not found in environment")
        return False

    print(f"Connecting to Pinecone...")
    pc = Pinecone(api_key=api_key)

    # List existing indexes
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    print(f"Existing indexes: {existing_indexes}")

    if INDEX_NAME in existing_indexes:
        print(f"\nIndex '{INDEX_NAME}' already exists.")
        # Get index stats
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        print(f"Index stats:")
        print(f"  Dimension: {stats.dimension}")
        print(f"  Total vectors: {stats.total_vector_count}")
        return True

    print(f"\nCreating index '{INDEX_NAME}'...")
    print(f"  Dimension: {DIMENSION}")
    print(f"  Metric: {METRIC}")
    print(f"  Cloud: {CLOUD}")
    print(f"  Region: {REGION}")

    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric=METRIC,
        spec=ServerlessSpec(
            cloud=CLOUD,
            region=REGION
        )
    )

    print(f"\nIndex '{INDEX_NAME}' created successfully!")
    return True


if __name__ == "__main__":
    success = create_index()
    sys.exit(0 if success else 1)
