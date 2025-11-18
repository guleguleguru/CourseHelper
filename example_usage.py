#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Research TA Agent 使用示例
演示不同类型的查询
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import ResearchAgent


def run_examples():
    """运行示例查询"""
    
    print("=" * 70)
    print("Research TA Agent - 使用示例演示")
    print("=" * 70)
    print()
    
    # 初始化 Agent
    try:
        print("正在初始化 Agent...\n")
        agent = ResearchAgent()
        print("\n" + "=" * 70)
        print()
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        print("请先运行 build_index.py 构建索引")
        return
    
    # 示例查询列表
    examples = [
        {
            'type': '文献检索',
            'query': '什么是球形性假设（sphericity assumption）？',
            'description': '从知识库中检索理论定义'
        },
        {
            'type': '数据分析',
            'query': '列出 data 目录中可用的 CSV 文件，并展示第一个文件的基本统计信息',
            'description': '探索性数据分析'
        },
        {
            'type': '组合查询',
            'query': '先解释什么是重复测量方差分析，然后如果有相关数据集，进行一个示例分析',
            'description': '结合文献检索和数据分析'
        }
    ]
    
    # 运行每个示例
    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 70}")
        print(f"示例 {i}: {example['type']}")
        print(f"描述: {example['description']}")
        print(f"{'=' * 70}")
        print(f"\n问题: {example['query']}\n")
        print("-" * 70)
        
        try:
            response = agent.run(example['query'])
            print("\n回答:")
            print(response)
            print()
        except Exception as e:
            print(f"\n✗ 执行失败: {e}\n")
        
        print("=" * 70)
        
        # 询问是否继续
        if i < len(examples):
            input("\n按 Enter 继续下一个示例...")
    
    print("\n✓ 所有示例运行完成！")


if __name__ == "__main__":
    run_examples()



