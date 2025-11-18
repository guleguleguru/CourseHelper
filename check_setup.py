#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统检查脚本 - 验证环境配置是否正确
"""

import sys
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    print("1. 检查 Python 版本...")
    version = sys.version_info
    if version.major == 3 and version.minor in [10, 11]:
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ✗ Python 版本不符合要求（当前: {version.major}.{version.minor}，要求: 3.10 或 3.11）")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n2. 检查依赖包...")
    
    required_packages = [
        ('langchain', 'LangChain'),
        ('langchain_openai', 'LangChain OpenAI'),
        ('faiss', 'FAISS'),
        ('pandas', 'Pandas'),
        ('pypdf', 'PyPDF'),
        ('rank_bm25', 'BM25'),
        ('yaml', 'PyYAML'),
        ('dotenv', 'python-dotenv'),
    ]
    
    all_ok = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {name}")
        except ImportError:
            print(f"   ✗ {name} 未安装")
            all_ok = False
    
    return all_ok

def check_directories():
    """检查目录结构"""
    print("\n3. 检查目录结构...")
    
    required_dirs = [
        'knowledge_base',
        'data',
        'src',
        'config',
        'outputs'
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"   ✓ {dir_name}/")
        else:
            print(f"   ✗ {dir_name}/ 不存在")
            all_ok = False
    
    return all_ok

def check_config():
    """检查配置文件"""
    print("\n4. 检查配置文件...")
    
    all_ok = True
    
    # 检查 settings.yaml
    settings_path = Path("config/settings.yaml")
    if settings_path.exists():
        print(f"   ✓ config/settings.yaml")
    else:
        print(f"   ✗ config/settings.yaml 不存在")
        all_ok = False
    
    # 检查 .env 或环境变量
    env_path = Path("config/.env")
    import os
    
    if env_path.exists():
        print(f"   ✓ config/.env 存在")
        # 尝试读取
        from dotenv import load_dotenv
        load_dotenv(env_path)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your_openai_api_key_here":
        print(f"   ✓ OPENAI_API_KEY 已设置")
    else:
        print(f"   ✗ OPENAI_API_KEY 未设置或无效")
        print(f"      请在 config/.env 中设置您的 API key")
        all_ok = False
    
    return all_ok

def check_data():
    """检查数据文件"""
    print("\n5. 检查数据文件...")
    
    kb_path = Path("knowledge_base")
    data_path = Path("data")
    
    # 检查知识库文件
    kb_files = list(kb_path.glob("**/*"))
    kb_files = [f for f in kb_files if f.is_file() and f.suffix in ['.pdf', '.txt', '.md']]
    
    if kb_files:
        print(f"   ✓ 知识库: 找到 {len(kb_files)} 个文档")
        for f in kb_files[:3]:  # 显示前 3 个
            print(f"      - {f.name}")
        if len(kb_files) > 3:
            print(f"      ... 还有 {len(kb_files) - 3} 个文件")
    else:
        print(f"   ⚠ 知识库为空（将无法使用 retriever 功能）")
    
    # 检查数据文件
    csv_files = list(data_path.glob("*.csv"))
    
    if csv_files:
        print(f"   ✓ 数据集: 找到 {len(csv_files)} 个 CSV 文件")
        for f in csv_files[:3]:
            print(f"      - {f.name}")
        if len(csv_files) > 3:
            print(f"      ... 还有 {len(csv_files) - 3} 个文件")
    else:
        print(f"   ⚠ 数据目录为空（将无法使用 pandas_runner 功能）")
    
    return True

def check_indexes():
    """检查索引"""
    print("\n6. 检查索引...")
    
    faiss_path = Path("outputs/faiss_index")
    bm25_path = Path("outputs/bm25_index.pkl")
    
    if faiss_path.exists() and bm25_path.exists():
        print(f"   ✓ 索引已构建")
        return True
    else:
        print(f"   ⚠ 索引未构建")
        print(f"      请运行: python build_index.py")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("Research TA Agent - 系统检查")
    print("=" * 70)
    print()
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_directories(),
        check_config(),
        check_data(),
        check_indexes()
    ]
    
    print("\n" + "=" * 70)
    print("检查完成！")
    print("=" * 70)
    print()
    
    if all(checks[:4]):  # 前 4 项是必须的
        print("✓ 核心配置正常，可以运行 Agent")
        if not checks[5]:
            print("⚠ 但需要先构建索引: python build_index.py")
        else:
            print("✓ 可以直接运行: python main.py")
    else:
        print("✗ 存在配置问题，请根据上述提示修复")
        print("\n建议:")
        if not checks[1]:
            print("  1. 安装依赖: pip install -r requirements.txt")
        if not checks[3]:
            print("  2. 配置 API Key: 编辑 config/.env 文件")
        print("  3. 查看安装文档: INSTALL.md")
    
    print()


if __name__ == "__main__":
    main()



