#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reranker Validation Script

Tests the two-stage retrieval system:
1. Recall stage (FAISS + BM25 fusion)
2. Rerank stage (cross-encoder reranking)

Shows the effect of reranking on result quality.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import load_config, load_env, get_openai_api_key
from src.ingest.indexer import load_indexes
from src.tools.retriever_tool import HybridRetriever, create_retriever_tool
from src.tools.reranker import create_reranker
from langchain_openai import ChatOpenAI


def test_reranking():
    """Test reranking functionality."""
    
    print("=" * 70)
    print("Reranker Validation Test")
    print("=" * 70)
    print()
    
    # Load configuration
    try:
        load_env()
        config = load_config()
        print("[OK] Configuration loaded")
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return
    
    # Load indexes
    try:
        retriever_config = config.get('retriever', {})
        embedding_model = retriever_config.get('embedding_model', 'text-embedding-3-small')
        
        print("Loading indexes...")
        vectorstore, bm25_index = load_indexes(
            embedding_model=embedding_model,
            index_dir="outputs"
        )
        print("[OK] Indexes loaded")
    except FileNotFoundError as e:
        print(f"[ERROR] Indexes not found: {e}")
        print("Please run: python build_index.py")
        return
    
    # Create retriever without reranking
    print("\n" + "-" * 70)
    print("Creating retriever WITHOUT reranking (baseline)")
    print("-" * 70)
    
    config_no_rerank = config.copy()
    config_no_rerank['retriever']['rerank'] = {'enabled': False}
    
    retriever_no_rerank = HybridRetriever(
        vectorstore=vectorstore,
        bm25_index=bm25_index,
        vector_weight=0.65,
        bm25_weight=0.35,
        top_k=4,
        reranker=None
    )
    
    # Create retriever with reranking
    print("\n" + "-" * 70)
    print("Creating retriever WITH reranking")
    print("-" * 70)
    
    rerank_config = config.get('retriever', {}).get('rerank', {})
    reranker = None
    
    if rerank_config.get('enabled', False):
        try:
            reranker = create_reranker(rerank_config)
            if reranker:
                print(f"[OK] Reranker loaded: {rerank_config.get('model_name', 'unknown')}")
            else:
                print("[WARNING] Reranker failed to load. Install sentence-transformers:")
                print("  pip install sentence-transformers")
                print("Continuing with baseline (no reranking)...")
        except Exception as e:
            print(f"[WARNING] Reranker error: {e}")
            print("Continuing with baseline (no reranking)...")
    else:
        print("[INFO] Reranking disabled in config. Enable it in config/settings.yaml:")
        print("  retriever.rerank.enabled: true")
    
    retriever_with_rerank = HybridRetriever(
        vectorstore=vectorstore,
        bm25_index=bm25_index,
        vector_weight=0.65,
        bm25_weight=0.35,
        top_k=4,
        reranker=reranker,
        top_n_candidates=rerank_config.get('top_n_candidates', 32)
    )
    
    # Test queries
    test_queries = [
        "What is sphericity assumption?",
        "Explain ANOVA",
        "What is the definition of correlation?",
    ]
    
    print("\n" + "=" * 70)
    print("Testing Retrieval Quality")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 70}")
        print(f"Test Query {i}: {query}")
        print("=" * 70)
        
        # Without reranking
        print("\n[1] WITHOUT Reranking (Baseline):")
        print("-" * 70)
        start_time = time.time()
        docs_no_rerank, timing_no_rerank = retriever_no_rerank.search(
            query, return_timing=True
        )
        baseline_time = time.time() - start_time
        
        print(f"Time: Recall={timing_no_rerank['recall_time']:.3f}s, Total={baseline_time:.3f}s")
        print(f"Results ({len(docs_no_rerank)} documents):")
        for j, doc in enumerate(docs_no_rerank, 1):
            source = doc.metadata.get('source_file', 'Unknown')
            page = doc.metadata.get('page', 'N/A')
            content_preview = doc.page_content[:100].replace('\n', ' ')
            print(f"  {j}. {source} (page {page + 1 if page != 'N/A' else 'N/A'}): {content_preview}...")
        
        # With reranking (if available)
        if reranker:
            print("\n[2] WITH Reranking:")
            print("-" * 70)
            start_time = time.time()
            docs_with_rerank, timing_with_rerank = retriever_with_rerank.search(
                query, return_timing=True
            )
            rerank_time = time.time() - start_time
            
            print(f"Time: Recall={timing_with_rerank['recall_time']:.3f}s, "
                  f"Rerank={timing_with_rerank['rerank_time']:.3f}s, "
                  f"Total={rerank_time:.3f}s")
            print(f"Results ({len(docs_with_rerank)} documents):")
            for j, doc in enumerate(docs_with_rerank, 1):
                source = doc.metadata.get('source_file', 'Unknown')
                page = doc.metadata.get('page', 'N/A')
                content_preview = doc.page_content[:100].replace('\n', ' ')
                print(f"  {j}. {source} (page {page + 1 if page != 'N/A' else 'N/A'}): {content_preview}...")
            
            # Compare results
            print("\n[3] Comparison:")
            print("-" * 70)
            baseline_sources = {doc.metadata.get('source_file', '') for doc in docs_no_rerank}
            rerank_sources = {doc.metadata.get('source_file', '') for doc in docs_with_rerank}
            
            if baseline_sources == rerank_sources:
                print("✓ Same documents returned (reranking may have reordered)")
            else:
                print(f"Different documents: Baseline={baseline_sources}, Rerank={rerank_sources}")
            
            time_overhead = rerank_time - baseline_time
            print(f"Time overhead: +{time_overhead:.3f}s ({time_overhead/baseline_time*100:.1f}% slower)")
        else:
            print("\n[2] WITH Reranking: Skipped (reranker not available)")
            print("To enable reranking:")
            print("  1. Install: pip install sentence-transformers")
            print("  2. Enable in config/settings.yaml: retriever.rerank.enabled: true")
    
    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
    print("\nSummary:")
    print("- Two-stage retrieval: Recall (FAISS+BM25) -> Rerank (cross-encoder)")
    print("- Reranking improves precision by re-scoring top candidates")
    print("- Trade-off: Better relevance vs. additional computation time")
    print()


if __name__ == "__main__":
    test_reranking()

