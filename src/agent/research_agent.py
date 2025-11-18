"""
Research TA Agent 主类
"""

from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage

from src.utils import load_config, load_env, get_openai_api_key
from src.ingest.indexer import load_indexes
from src.tools import create_retriever_tool, create_pandas_runner_tool
from .prompts import SYSTEM_PROMPT


class ResearchAgent:
    """Research TA Agent - 研究助手代理"""
    
    def __init__(
        self,
        config_path: str = "config/settings.yaml",
        index_dir: str = "outputs"
    ):
        """
        初始化 Research Agent
        
        Args:
            config_path: 配置文件路径
            index_dir: 索引目录路径
        """
        # 加载环境变量和配置
        load_env()
        self.config = load_config()
        
        # 验证 API Key
        api_key = get_openai_api_key()
        
        # 初始化 LLM
        llm_config = self.config.get('llm', {})
        self.llm = ChatOpenAI(
            model=llm_config.get('chat_model', 'gpt-4o'),
            temperature=llm_config.get('temperature', 0.2),
            api_key=api_key
        )
        
        # 加载索引
        print("正在加载索引...")
        retriever_config = self.config.get('retriever', {})
        embedding_model = retriever_config.get('embedding_model', 'text-embedding-3-small')
        
        try:
            self.vectorstore, self.bm25_index = load_indexes(
                embedding_model=embedding_model,
                index_dir=index_dir
            )
            print("[OK] Index loaded successfully")
        except FileNotFoundError as e:
            print(f"[WARNING] {e}")
            print("Please run build_index.py first!")
            raise
        
        # 创建工具
        self.tools = self._create_tools()
        
        # 绑定工具到 LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        print("[OK] Research TA Agent initialized\n")
    
    def _create_tools(self) -> List[Tool]:
        """
        创建工具列表
        
        Returns:
            工具列表
        """
        tools = []
        
        # Retriever 工具
        retriever_tool = create_retriever_tool(
            vectorstore=self.vectorstore,
            bm25_index=self.bm25_index,
            config=self.config
        )
        tools.append(retriever_tool)
        
        # Pandas Runner 工具
        pandas_tool = create_pandas_runner_tool(
            llm=self.llm,
            config=self.config
        )
        tools.append(pandas_tool)
        
        return tools
    
    def _execute_tool_calls(self, message: AIMessage) -> List[str]:
        """执行工具调用"""
        results = []
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                print(f"  -> Calling {tool_name} with args: {tool_args}")
                
                # 查找并执行工具
                tool_found = False
                for tool in self.tools:
                    if tool.name == tool_name:
                        tool_found = True
                        try:
                            # 提取实际参数
                            if isinstance(tool_args, dict):
                                # 工具通常期望单个字符串参数
                                arg_value = tool_args.get('query') or tool_args.get('task') or list(tool_args.values())[0] if tool_args else ""
                                result = tool.func(arg_value)
                            else:
                                result = tool.func(tool_args)
                            
                            results.append(f"\n[Tool: {tool_name}]\n{result}")
                            print(f"  <- Tool executed successfully")
                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            results.append(f"\n[Tool Error: {tool_name}]\n{error_msg}")
                            print(f"  <- Tool error: {error_msg}")
                        break
                
                if not tool_found:
                    print(f"  <- Tool not found: {tool_name}")
        
        return results
    
    def run(self, query: str, max_iterations: int = 3) -> str:
        """
        执行查询
        
        Args:
            query: 用户查询
            max_iterations: 最大迭代次数
            
        Returns:
            Agent 响应
        """
        try:
            messages = [
                ("system", SYSTEM_PROMPT),
                ("human", query)
            ]
            
            for iteration in range(max_iterations):
                # 调用 LLM
                response = self.llm_with_tools.invoke(messages)
                
                # 检查是否需要调用工具
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    print(f"\n[Iteration {iteration + 1}] Calling tools...")
                    
                    # 执行工具调用
                    tool_results = self._execute_tool_calls(response)
                    
                    # 将工具结果添加到消息中
                    messages.append(("assistant", response.content or ""))
                    for result in tool_results:
                        messages.append(("human", result))
                else:
                    # 没有工具调用，返回最终响应
                    return response.content
            
            # 达到最大迭代次数
            return response.content
            
        except Exception as e:
            error_msg = f"[ERROR] Execution failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    async def arun(self, query: str) -> str:
        """
        异步执行查询（简化版本）
        
        Args:
            query: 用户查询
            
        Returns:
            Agent 响应
        """
        return self.run(query)  # 简化：使用同步版本
    
    def list_tools(self) -> List[str]:
        """
        列出可用工具
        
        Returns:
            工具名称列表
        """
        return [tool.name for tool in self.tools]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, str]]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具信息字典
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return {
                    'name': tool.name,
                    'description': tool.description
                }
        return None

