#!/usr/bin/env python3
"""
CLI script to create OpenSearch indices and Pinecone index.

This script initializes the search infrastructure before ingestion.

Usage:
    python scripts/build_indexes.py
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../apps/backend/api"))

from opensearchpy import OpenSearch
from pinecone import Pinecone


def create_opensearch_indices():
    """Create OpenSearch indices for papers and startups."""
    print("📦 Creating OpenSearch indices...")
    
    # Connect to OpenSearch
    host = os.getenv("OPENSEARCH_HOST", "localhost")
    port = int(os.getenv("OPENSEARCH_PORT", "9200"))
    
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=("admin", "admin"),
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )
    
    # Papers index mapping
    papers_mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "source": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "english"},
                "snippet": {"type": "text", "analyzer": "english"},
                "metadata": {
                    "properties": {
                        "year": {"type": "integer"},
                        "venue": {"type": "keyword"},
                        "concepts": {"type": "keyword"},
                        "authors": {"type": "keyword"},
                        "doi": {"type": "keyword"},
                    }
                },
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
    }
    
    # Startups index mapping
    startups_mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "source": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "english"},
                "snippet": {"type": "text", "analyzer": "english"},
                "metadata": {
                    "properties": {
                        "year": {"type": "integer"},
                        "website": {"type": "keyword"},
                        "industry": {"type": "keyword"},
                        "stage": {"type": "keyword"},
                    }
                },
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
    }
    
    # Create indices
    try:
        # Delete if exists
        if client.indices.exists("papers"):
            client.indices.delete("papers")
            print("   Deleted existing 'papers' index")
        
        if client.indices.exists("startups"):
            client.indices.delete("startups")
            print("   Deleted existing 'startups' index")
        
        # Create new indices
        client.indices.create("papers", body=papers_mapping)
        print("   ✅ Created 'papers' index")
        
        client.indices.create("startups", body=startups_mapping)
        print("   ✅ Created 'startups' index")
        
    except Exception as e:
        print(f"   ❌ Error creating indices: {e}")
        return False
    
    return True


def create_pinecone_index():
    """Create Pinecone index for vector storage."""
    print("\n📦 Creating Pinecone index...")
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "r2d-chunks")
    
    if not api_key or api_key.startswith("your-"):
        print("   ⚠️  Skipping: PINECONE_API_KEY not set")
        return True
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # Check if index exists
        existing_indexes = pc.list_indexes().names()
        
        if index_name in existing_indexes:
            print(f"   ✅ Index '{index_name}' already exists")
            return True
        
        # Create index (768 dimensions for e5-base-v2)
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec={
                "serverless": {
                    "cloud": "aws",
                    "region": "us-west-2",
                }
            },
        )
        
        print(f"   ✅ Created index '{index_name}'")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating index: {e}")
        return False


def main():
    """Create all search indices."""
    print("🚀 Building search indexes...\n")
    
    success = True
    
    # Create OpenSearch indices
    if not create_opensearch_indices():
        success = False
    
    # Create Pinecone index
    if not create_pinecone_index():
        success = False
    
    if success:
        print("\n✅ All indices created successfully!")
        return 0
    else:
        print("\n❌ Some indices failed to create")
        return 1


if __name__ == "__main__":
    sys.exit(main())

