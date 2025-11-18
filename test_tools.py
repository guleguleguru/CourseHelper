#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具测试脚本 - 单独测试 retriever 和 pandas_runner
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import load_config, load_env, get_openai_api_key
from src.ingest.indexer import load_indexes
from src.tools import create_retriever_tool, create_pandas_runner_tool
from langchain_openai import ChatOpenAI


def test_retriever():
    """测试 retriever 工具"""
    print("=" * 70)
    print("测试 Retriever 工具")
    print("=" * 70)
    print()
    
    try:
        # 加载配置
        load_env()
        config = load_config()
        
        # 加载索引
        print("加载索引...")
        retriever_config = config.get('retriever', {})
        embedding_model = retriever_config.get('embedding_model', 'text-embedding-3-small')
        
        vectorstore, bm25_index = load_indexes(
            embedding_model=embedding_model,
            index_dir="outputs"
        )
        print("✓ 索引加载成功\n")
        
        # 创建工具
        retriever_tool = create_retriever_tool(vectorstore, bm25_index, config)
        
        # 测试查询
        test_queries = [
            "重复测量",
            "方差分析",
            "统计"
        ]
        
        for query in test_queries:
            print(f"查询: {query}")
            print("-" * 70)
            result = retriever_tool.func(query)
            print(result[:500] + "..." if len(result) > 500 else result)
            print("\n")
        
        print("✓ Retriever 测试完成\n")
        return True
        
    except FileNotFoundError as e:
        print(f"✗ 索引未找到: {e}")
        print("请先运行: python build_index.py\n")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pandas_runner():
    """测试 pandas_runner 工具"""
    print("=" * 70)
    print("测试 Pandas Runner 工具")
    print("=" * 70)
    print()
    
    try:
        # 加载配置
        load_env()
        config = load_config()
        api_key = get_openai_api_key()
        
        # 创建 LLM
        llm_config = config.get('llm', {})
        llm = ChatOpenAI(
            model=llm_config.get('chat_model', 'gpt-4o'),
            temperature=llm_config.get('temperature', 0.2),
            api_key=api_key
        )
        
        # 创建工具
        pandas_tool = create_pandas_runner_tool(llm, config)
        
        # 检查是否有数据文件
        data_dir = Path("data")
        csv_files = list(data_dir.glob("*.csv"))
        
        if not csv_files:
            print("⚠ data/ 目录中没有 CSV 文件")
            print("请添加至少一个 CSV 文件进行测试\n")
            return False
        
        print(f"找到 {len(csv_files)} 个 CSV 文件:")
        for f in csv_files:
            print(f"  - {f.name}")
        print()
        
        # 测试查询
        test_query = f"列出 data 目录中的所有 CSV 文件，并展示第一个文件的基本信息（行数、列数、列名）"
        
        print(f"测试查询: {test_query}")
        print("-" * 70)
        result = pandas_tool.func(test_query)
        print(result)
        print()
        
        print("✓ Pandas Runner 测试完成\n")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("Research TA Agent - 工具测试")
    print("=" * 70)
    print()
    
    print("此脚本将单独测试两个工具的功能\n")
    
    # 测试 retriever
    retriever_ok = test_retriever()
    
    # 测试 pandas_runner
    pandas_ok = test_pandas_runner()
    
    # 总结
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print()
    
    if retriever_ok:
        print("✓ Retriever 工具正常")
    else:
        print("✗ Retriever 工具异常")
    
    if pandas_ok:
        print("✓ Pandas Runner 工具正常")
    else:
        print("✗ Pandas Runner 工具异常")
    
    print()
    
    if retriever_ok and pandas_ok:
        print("✓ 所有工具测试通过！可以运行完整的 Agent")
        print("运行命令: python main.py")
    else:
        print("⚠ 部分工具测试未通过，请根据上述信息修复")
    
    print()


if __name__ == "__main__":
    main()



