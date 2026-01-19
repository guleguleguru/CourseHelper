"""
Research TA Agent - LangGraph Implementation

Cleaner, more maintainable agent using LangGraph for state management.
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.utils import load_config, load_env, get_openai_api_key
from src.ingest.indexer import load_indexes
from src.tools import create_retriever_tool, create_pandas_runner_tool
from .prompts import SYSTEM_PROMPT


class AgentState(TypedDict):
    """Agent state for LangGraph"""
    messages: Annotated[List[BaseMessage], "List of messages in the conversation"]


class ResearchAgent:
    """Research TA Agent - LangGraph-based implementation"""
    
    def __init__(
        self,
        config_path: str = "config/settings.yaml",
        index_dir: str = "outputs"
    ):
        """
        Initialize Research Agent with LangGraph.
        
        Args:
            config_path: Configuration file path
            index_dir: Index directory path
        """
        # Load environment and config
        load_env()
        self.config = load_config()
        
        # Validate API Key
        api_key = get_openai_api_key()
        
        # Initialize LLM
        llm_config = self.config.get('llm', {})
        self.llm = ChatOpenAI(
            model=llm_config.get('chat_model', 'gpt-4o'),
            temperature=llm_config.get('temperature', 0.2),
            api_key=api_key
        )
        
        # Load indexes
        print("Loading indexes...")
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
        
        # Create tools
        self.tools = self._create_tools()
        
        # Build LangGraph
        self.graph = self._build_graph()
        
        print("[OK] Research TA Agent initialized (LangGraph)\n")
    
    def _create_tools(self) -> List:
        """Create tool list"""
        tools = []
        
        # Retriever tool
        retriever_tool = create_retriever_tool(
            vectorstore=self.vectorstore,
            bm25_index=self.bm25_index,
            config=self.config
        )
        tools.append(retriever_tool)
        
        # Pandas Runner tool
        pandas_tool = create_pandas_runner_tool(
            llm=self.llm,
            config=self.config
        )
        tools.append(pandas_tool)
        
        return tools
    
    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph workflow.
        
        Graph structure:
        START -> agent (LLM with tools) -> should_continue -> tool_node OR END
        """
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Create tool node (executes tool calls)
        tool_node = ToolNode(self.tools)
        
        # Define agent node (calls LLM)
        def agent_node(state: AgentState) -> Dict[str, List[BaseMessage]]:
            """Agent node: calls LLM with tools"""
            messages = state["messages"]
            
            # Add system message if not present
            has_system = any(isinstance(m, SystemMessage) for m in messages)
            if not has_system:
                messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
            
            # Call LLM
            response = llm_with_tools.invoke(messages)
            
            return {"messages": [response]}
        
        # Define conditional edge function
        def should_continue(state: AgentState) -> str:
            """Determine next step: call tools or end"""
            messages = state["messages"]
            if not messages:
                return "end"
            
            last_message = messages[-1]
            
            # If last message has tool calls, execute tools
            if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
                if last_message.tool_calls:
                    return "tools"
            # Otherwise, end
            return "end"
        
        # Build graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")
        
        # Compile graph
        # Note: MemorySaver is optional, can be None for stateless execution
        graph = workflow.compile()
        
        return graph
    
    def run(
        self,
        query: str,
        max_iterations: int = 5,
        config: Optional[Dict] = None
    ) -> str:
        """
        Execute query using LangGraph.
        
        Args:
            query: User query
            max_iterations: Maximum number of iterations
            config: Optional runtime config
            
        Returns:
            Agent response
        """
        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=query)]
            }
            
            # Run graph
            config_dict = config or {"recursion_limit": max_iterations}
            
            final_state = self.graph.invoke(
                initial_state,
                config=config_dict
            )
            
            # Extract final response
            messages = final_state["messages"]
            
            # Find last AI message (should be the final answer)
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                    return msg.content
            
            # Fallback: return last message content
            return messages[-1].content if messages else "No response generated"
            
        except Exception as e:
            error_msg = f"[ERROR] Execution failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    async def arun(
        self,
        query: str,
        max_iterations: int = 5
    ) -> str:
        """
        Async execution.
        
        Args:
            query: User query
            max_iterations: Maximum iterations
            
        Returns:
            Agent response
        """
        try:
            initial_state = {
                "messages": [HumanMessage(content=query)]
            }
            
            config_dict = {"recursion_limit": max_iterations}
            
            final_state = await self.graph.ainvoke(
                initial_state,
                config=config_dict
            )
            
            messages = final_state["messages"]
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                    return msg.content
            
            return messages[-1].content if messages else "No response generated"
            
        except Exception as e:
            error_msg = f"[ERROR] Async execution failed: {str(e)}"
            print(error_msg)
            return error_msg
    
    def list_tools(self) -> List[str]:
        """List available tools"""
        return [tool.name for tool in self.tools]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, str]]:
        """Get tool information"""
        for tool in self.tools:
            if tool.name == tool_name:
                return {
                    'name': tool.name,
                    'description': tool.description
                }
        return None

