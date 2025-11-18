#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Research TA Agent 主入口
交互式查询界面
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import ResearchAgent


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           Research TA Agent - 研究助手代理系统                ║
║                                                              ║
║  功能:                                                        ║
║    • 文献检索 (retriever) - 从本地知识库检索并标注出处        ║
║    • 数据分析 (pandas_runner) - 对 CSV 数据进行真实计算       ║
║                                                              ║
║  命令:                                                        ║
║    • 输入问题开始查询                                         ║
║    • 输入 'quit' 或 'exit' 退出                               ║
║    • 输入 'help' 查看帮助                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = """
使用示例:

1. 文献检索型查询:
   "解释 repeated-measures ANOVA 的球形性假设，并标注来源页码"
   
2. 数据分析型查询:
   "在 covid.csv 中，按 intubated 分组计算平均年龄"
   
3. 组合型查询:
   "先给出 Greenhouse–Geisser 校正的定义，再用数据集做示例"

Agent 会自动选择合适的工具并返回带有出处/数据源的结果。
    """
    print(help_text)


def main():
    """主函数"""
    print_banner()
    
    # 初始化 Agent
    try:
        print("正在初始化 Agent...")
        print("-" * 60)
        agent = ResearchAgent(
            config_path="config/settings.yaml",
            index_dir="outputs"
        )
        print("-" * 60)
        print()
    except FileNotFoundError as e:
        print(f"\n✗ 初始化失败: {e}")
        print("\n请先运行 build_index.py 构建索引！")
        print("命令: python build_index.py")
        return 1
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 交互式循环
    print("Agent 就绪！输入 'help' 查看使用示例。\n")
    
    while True:
        try:
            # 获取用户输入
            query = input("\n🔍 您的问题: ").strip()
            
            if not query:
                continue
            
            # 处理命令
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n再见！👋")
                break
            
            if query.lower() == 'help':
                print_help()
                continue
            
            # 执行查询
            print("\n" + "=" * 60)
            print("正在处理...")
            print("=" * 60)
            print()
            
            response = agent.run(query)
            
            print("\n" + "=" * 60)
            print("📋 结果:")
            print("=" * 60)
            print()
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\n操作已取消。输入 'quit' 退出。")
            continue
        except Exception as e:
            print(f"\n✗ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            continue


if __name__ == "__main__":
    sys.exit(main())



