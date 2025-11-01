#!/usr/bin/env python3
"""
CLI script to trigger OpenAlex ingestion via API.

Usage:
    python scripts/ingest_openalex.py
"""
import os
import sys
import time
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
ADMIN_TOKEN = os.getenv("ADMIN_BEARER_TOKEN", "dev-admin-token-change-in-production")


def ingest_openalex():
    """Trigger OpenAlex ingestion via API."""
    print("🚀 Starting OpenAlex ingestion...")
    print(f"   API URL: {API_URL}")
    
    url = f"{API_URL}/api/ingest/openalex"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json",
    }
    
    start_time = time.time()
    
    try:
        # Make POST request to trigger ingestion
        with httpx.Client(timeout=600.0) as client:  # 10 min timeout
            response = client.post(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            # Print results
            duration = time.time() - start_time
            print(f"\n✅ OpenAlex ingestion completed in {duration:.1f}s")
            print(f"   Status: {result['status']}")
            print(f"   Fetched: {result['total_fetched']}")
            print(f"   Processed: {result['total_processed']}")
            print(f"   Indexed: {result['total_indexed']}")
            print(f"   Errors: {result['error_count']}")
            
            if result.get('errors'):
                print(f"\n⚠️  First few errors:")
                for error in result['errors'][:5]:
                    print(f"   - {error}")
            
            return 0
            
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP error: {e.response.status_code}")
        print(f"   {e.response.text}")
        return 1
        
    except httpx.RequestError as e:
        print(f"\n❌ Request error: {e}")
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(ingest_openalex())

