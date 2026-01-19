#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test LangGraph Implementation

Compare old manual loop vs new LangGraph implementation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import load_config, load_env, get_openai_api_key
from src.ingest.indexer import load_indexes
from src.tools import create_retriever_tool, create_pandas_runner_tool

# Test both implementations
print("=" * 70)
print("Testing LangGraph Implementation")
print("=" * 70)
print()

try:
    from src.agent.research_agent_langgraph import ResearchAgent
    
    print("[1] Testing LangGraph version...")
    print("-" * 70)
    
    # Initialize agent
    agent = ResearchAgent()
    
    # Test query
    test_query = "What is sphericity assumption?"
    print(f"Query: {test_query}\n")
    
    # Run
    result = agent.run(test_query, max_iterations=5)
    
    print("\n" + "=" * 70)
    print("Result:")
    print("=" * 70)
    print(result[:500] + "..." if len(result) > 500 else result)
    print()
    
    print("[OK] LangGraph implementation works!")
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("Make sure langgraph is installed: pip install langgraph")
except Exception as e:
    print(f"[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)

