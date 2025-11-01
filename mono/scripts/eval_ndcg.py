#!/usr/bin/env python3
"""
CLI script to evaluate search quality using NDCG (Normalized Discounted Cumulative Gain).

Reads gold-standard queries from data/eval/gold_queries.jsonl and computes NDCG@10.

Usage:
    python scripts/eval_ndcg.py
"""
import json
import os
import sys
import httpx
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

# API configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")


def compute_dcg(relevances, k=10):
    """
    Compute Discounted Cumulative Gain.
    
    Args:
        relevances: List of relevance scores (0 or 1)
        k: Number of results to consider
    
    Returns:
        DCG score
    """
    relevances = relevances[:k]
    gains = [rel / np.log2(i + 2) for i, rel in enumerate(relevances)]
    return sum(gains)


def compute_ndcg(relevances, k=10):
    """
    Compute Normalized Discounted Cumulative Gain.
    
    Args:
        relevances: List of relevance scores (0 or 1)
        k: Number of results to consider
    
    Returns:
        NDCG score
    """
    dcg = compute_dcg(relevances, k)
    
    # Ideal DCG (all relevant docs at top)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = compute_dcg(ideal_relevances, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def load_gold_queries(filepath):
    """
    Load gold-standard queries from JSONL file.
    
    Args:
        filepath: Path to gold_queries.jsonl
    
    Returns:
        List of query dictionaries
    """
    queries = []
    with open(filepath, "r") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
    return queries


def evaluate_query(query_data):
    """
    Evaluate a single query.
    
    Args:
        query_data: Dictionary with 'query' and 'relevant_ids'
    
    Returns:
        NDCG score and result details
    """
    query_text = query_data["query"]
    relevant_ids = set(query_data["relevant_ids"])
    
    # Search via API
    url = f"{API_URL}/api/search"
    response = httpx.post(
        url,
        json={"query": query_text, "limit": 20},
        timeout=30.0,
    )
    response.raise_for_status()
    
    search_results = response.json()
    
    # Extract result IDs
    result_ids = [r["id"] for r in search_results["results"]]
    
    # Compute relevances (1 if in relevant_ids, 0 otherwise)
    relevances = [1 if rid in relevant_ids else 0 for rid in result_ids]
    
    # Compute NDCG@10
    ndcg = compute_ndcg(relevances, k=10)
    
    return {
        "query": query_text,
        "ndcg": ndcg,
        "total_results": len(result_ids),
        "relevant_found": sum(relevances),
        "relevant_total": len(relevant_ids),
    }


def main():
    """Run evaluation on all gold queries."""
    print("📊 Evaluating search quality...\n")
    
    # Load gold queries
    gold_file = os.path.join(
        os.path.dirname(__file__), "../data/eval/gold_queries.jsonl"
    )
    
    if not os.path.exists(gold_file):
        print(f"❌ Gold queries file not found: {gold_file}")
        return 1
    
    queries = load_gold_queries(gold_file)
    print(f"Loaded {len(queries)} gold queries\n")
    
    # Evaluate each query
    results = []
    for i, query_data in enumerate(queries, 1):
        try:
            print(f"[{i}/{len(queries)}] Evaluating: {query_data['query'][:50]}...")
            result = evaluate_query(query_data)
            results.append(result)
            print(f"   NDCG@10: {result['ndcg']:.3f}")
            print(f"   Found {result['relevant_found']}/{result['relevant_total']} relevant docs\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    # Compute average NDCG
    if results:
        avg_ndcg = np.mean([r["ndcg"] for r in results])
        print(f"\n{'='*60}")
        print(f"✅ Evaluation complete!")
        print(f"   Average NDCG@10: {avg_ndcg:.3f}")
        print(f"   Queries evaluated: {len(results)}/{len(queries)}")
        print(f"{'='*60}\n")
        
        # Print per-query results
        print("Per-query results:")
        for r in results:
            print(f"   {r['query'][:50]:50s} | NDCG: {r['ndcg']:.3f}")
        
        return 0
    else:
        print("❌ No queries were successfully evaluated")
        return 1


if __name__ == "__main__":
    sys.exit(main())

