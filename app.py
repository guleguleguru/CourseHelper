#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Research TA Agent - Streamlit Web 界面
"""

import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 强制加载环境变量
env_path = Path(__file__).parent / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    
# 如果还没有设置，尝试从根目录加载
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv()

from src.agent import ResearchAgent


# 页面配置
st.set_page_config(
    page_title="Research TA Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_agent():
    """加载 Agent（使用缓存避免重复初始化）"""
    try:
        agent = ResearchAgent()
        return agent, None
    except Exception as e:
        return None, str(e)


def main():
    """主界面"""
    
    # 标题和说明
    st.title("🎓 Research TA Agent")
    st.markdown("*智能研究助手 - 文献检索 + 数据分析*")
    
    # 侧边栏
    with st.sidebar:
        st.header("📚 功能说明")
        
        st.markdown("""
        ### 🔍 文献检索
        - 查询理论定义
        - 检索概念解释
        - 自动标注来源和页码
        
        ### 📊 数据分析
        - 计算统计量
        - 数据可视化
        - 自动生成代码
        
        ### 🤖 智能决策
        - 自动选择工具
        - 多步骤组合
        - 可追溯结果
        """)
        
        st.divider()
        
        st.header("💡 使用示例")
        
        example_queries = {
            "📚 文献检索": [
                "什么是球形性假设？",
                "解释 Greenhouse-Geisser 校正",
                "重复测量方差分析的前提条件"
            ],
            "📊 数据分析": [
                "展示 experiment_data.csv 的基本信息",
                "计算各组的平均年龄",
                "比较对照组和治疗组的 BMI 差异"
            ],
            "🔄 组合查询": [
                "先解释相关分析，再计算示例数据的相关系数",
                "什么是效应量？并计算我的数据的 Cohen's d"
            ]
        }
        
        for category, examples in example_queries.items():
            with st.expander(category):
                for example in examples:
                    if st.button(example, key=example):
                        st.session_state.query = example
        
        st.divider()
        
        # 系统状态
        st.header("⚙️ 系统状态")
        if 'agent' in st.session_state and st.session_state.agent:
            st.success("✅ Agent 已就绪")
            
            # 显示可用工具
            tools = st.session_state.agent.list_tools()
            st.info(f"**可用工具**: {', '.join(tools)}")
        else:
            st.error("❌ Agent 未初始化")
    
    # 主界面
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 提问区")
    
    with col2:
        if st.button("🗑️ 清空历史", type="secondary"):
            if 'history' in st.session_state:
                st.session_state.history = []
            st.rerun()
    
    # 初始化 session state
    if 'agent' not in st.session_state:
        with st.spinner("正在初始化 Agent..."):
            agent, error = load_agent()
            if agent:
                st.session_state.agent = agent
                st.success("✅ Agent 初始化成功！")
            else:
                st.error(f"❌ 初始化失败: {error}")
                st.info("请确保已运行 `python build_index.py` 构建索引")
                st.stop()
    
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    if 'query' not in st.session_state:
        st.session_state.query = ""
    
    # 输入区域
    user_input = st.text_area(
        "请输入您的问题：",
        value=st.session_state.query,
        height=100,
        placeholder="例如：什么是重复测量方差分析的球形性假设？",
        key="input_area"
    )
    
    # 重置临时查询
    if st.session_state.query:
        st.session_state.query = ""
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        submit_button = st.button("🚀 提交查询", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🔄 清空输入", use_container_width=True)
    
    if clear_button:
        st.rerun()
    
    # 处理查询
    if submit_button and user_input.strip():
        with st.spinner("🤔 Agent 正在思考..."):
            try:
                # 执行查询
                result = st.session_state.agent.run(user_input)
                
                # 保存到历史
                st.session_state.history.append({
                    'question': user_input,
                    'answer': result
                })
                
            except Exception as e:
                st.error(f"执行出错: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # 显示结果
    st.divider()
    st.header("📋 查询结果")
    
    if st.session_state.history:
        # 显示最新的结果
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(
                f"❓ {item['question'][:100]}..." if len(item['question']) > 100 else f"❓ {item['question']}",
                expanded=(i == 0)  # 只展开最新的
            ):
                st.markdown("### 📝 问题")
                st.info(item['question'])
                
                st.markdown("### 💡 回答")
                st.markdown(item['answer'])
                
                st.caption(f"查询 #{len(st.session_state.history) - i}")
    else:
        st.info("👆 在上方输入问题并点击「提交查询」开始使用")
        
        # 显示快速开始提示
        st.markdown("""
        ### 🚀 快速开始
        
        1. **文献检索示例**：在左侧边栏点击示例问题
        2. **数据分析示例**：尝试询问数据集的统计信息
        3. **自定义问题**：在输入框中输入您的问题
        
        ---
        
        **提示**：您可以：
        - 📚 询问理论概念和定义
        - 📊 要求分析 CSV 数据
        - 🔗 同时使用两种功能（如：先解释理论，再用数据演示）
        """)


if __name__ == "__main__":
    main()

