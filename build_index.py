#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
索引构建脚本
运行此脚本以构建知识库索引
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import load_config, load_env, get_openai_api_key
from src.ingest import load_documents, build_indexes


def main():
    """主函数"""
    print("=" * 60)
    print("Research TA Agent - Index Building")
    print("=" * 60)
    print()
    
    # 加载环境变量和配置
    try:
        load_env()
        config = load_config()
        api_key = get_openai_api_key()
        print("[OK] Configuration loaded successfully\n")
    except Exception as e:
        print(f"[ERROR] Configuration failed: {e}")
        print("\nPlease ensure:")
        print("1. config/settings.yaml file exists")
        print("2. config/.env file exists and contains valid OPENAI_API_KEY")
        return 1
    
    # 检查知识库目录
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        print(f"[ERROR] Knowledge base directory not found: {kb_path}")
        print("Please create knowledge_base directory and add PDF/TXT/MD files")
        return 1
    
    # 加载文档
    try:
        retriever_config = config.get('retriever', {})
        chunk_size = retriever_config.get('chunk_size', 800)
        chunk_overlap = retriever_config.get('chunk_overlap', 120)
        
        documents = load_documents(
            knowledge_base_path="knowledge_base",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        if not documents:
            print("[ERROR] No documents loaded")
            return 1
        
    except Exception as e:
        print(f"[ERROR] Document loading failed: {e}")
        return 1
    
    # 构建索引
    try:
        embedding_model = retriever_config.get('embedding_model', 'text-embedding-3-small')
        
        vectorstore, bm25_index = build_indexes(
            documents=documents,
            embedding_model=embedding_model,
            output_dir="outputs"
        )
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Index building completed!")
        print("=" * 60)
        print("\nYou can now run main.py to start the Agent")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Index building failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

