"""
Pandas Runner Tool - 使用 LLM 生成并执行 pandas 代码
"""

import os
import re
import traceback
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI


class PandasRunner:
    """Pandas 代码生成和执行器"""
    
    def __init__(
        self,
        llm: ChatOpenAI,
        data_dir: str = "data",
        output_dir: str = "outputs",
        max_rows: int = 100000,
        round_digits: int = 3
    ):
        """
        初始化 Pandas Runner
        
        Args:
            llm: LLM 模型
            data_dir: 数据目录
            output_dir: 输出目录
            max_rows: 最大行数限制
            round_digits: 保留小数位数
        """
        self.llm = llm
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.max_rows = max_rows
        self.round_digits = round_digits
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
    
    def list_available_files(self) -> str:
        """
        列出可用的 CSV 文件
        
        Returns:
            文件列表字符串
        """
        if not self.data_dir.exists():
            return "数据目录不存在"
        
        csv_files = list(self.data_dir.glob("*.csv"))
        if not csv_files:
            return "未找到 CSV 文件"
        
        return ", ".join([f.name for f in csv_files])
    
    def generate_code(self, task: str) -> str:
        """
        使用 LLM 生成 pandas 代码
        
        Args:
            task: 任务描述
            
        Returns:
            生成的 Python 代码
        """
        available_files = self.list_available_files()
        
        prompt = f"""你是一个专业的数据分析助手。用户需要分析 CSV 数据，请生成 Python pandas 代码。

**可用数据文件**: {available_files}

**任务**: {task}

**要求**:
1. 只返回可执行的 Python 代码，不要有任何解释文字
2. 代码应该完整且可直接运行
3. 使用 pandas 读取 data/ 目录下的 CSV 文件
4. 将最终结果存储在变量 `result` 中
5. result 应该是可打印的（DataFrame、数字、字符串等）
6. 如果需要绘图，保存到 outputs/ 目录，不要显示图表
7. 处理可能的异常（文件不存在、列不存在等）
8. 保留 {self.round_digits} 位小数

**代码模板**:
```python
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv('data/your_file.csv')

# 数据处理和分析
# ...

# 最终结果
result = ...  # 你的计算结果
```

现在请生成代码："""

        response = self.llm.invoke(prompt)
        code = response.content.strip()
        
        # 提取代码块
        code = self._extract_code(code)
        
        return code
    
    def _extract_code(self, text: str) -> str:
        """
        从响应中提取 Python 代码
        
        Args:
            text: LLM 响应文本
            
        Returns:
            提取的代码
        """
        # 尝试提取 markdown 代码块
        code_block_pattern = r'```python\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # 如果没有代码块，尝试提取所有以 import 或其他 Python 关键字开头的部分
        code_pattern = r'(import\s+.*?result\s*=.*?)(?:\n\n|$)'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # 否则返回整个文本
        return text
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        在沙箱环境中执行代码
        
        Args:
            code: Python 代码
            
        Returns:
            执行结果字典 {success, result, error}
        """
        # 准备执行环境
        exec_globals = {
            'pd': pd,
            'np': np,
            'plt': plt,
            'sns': sns,
            '__builtins__': __builtins__,
        }
        
        exec_locals = {}
        
        try:
            # 执行代码
            exec(code, exec_globals, exec_locals)
            
            # 获取 result 变量
            if 'result' not in exec_locals:
                return {
                    'success': False,
                    'result': None,
                    'error': "代码未定义 'result' 变量"
                }
            
            result = exec_locals['result']
            
            # 格式化结果
            formatted_result = self._format_result(result)
            
            return {
                'success': True,
                'result': formatted_result,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
    
    def _format_result(self, result: Any) -> str:
        """
        格式化结果
        
        Args:
            result: 执行结果
            
        Returns:
            格式化的字符串
        """
        if isinstance(result, pd.DataFrame):
            return result.to_string()
        elif isinstance(result, pd.Series):
            return result.to_string()
        elif isinstance(result, (int, float, np.integer, np.floating)):
            if isinstance(result, (float, np.floating)):
                return f"{result:.{self.round_digits}f}"
            return str(result)
        elif isinstance(result, dict):
            return str(result)
        else:
            return str(result)
    
    def run(self, task: str) -> str:
        """
        执行完整的分析流程
        
        Args:
            task: 任务描述
            
        Returns:
            分析结果
        """
        # 1. 生成代码
        try:
            code = self.generate_code(task)
        except Exception as e:
            return f"代码生成失败: {str(e)}"
        
        # 2. 执行代码
        exec_result = self.execute_code(code)
        
        # 3. 格式化输出
        if exec_result['success']:
            output = f"✓ 分析完成\n\n"
            output += f"**结果**:\n{exec_result['result']}\n\n"
            output += f"**执行的代码**:\n```python\n{code}\n```"
            return output
        else:
            output = f"✗ 执行失败\n\n"
            output += f"**错误信息**:\n{exec_result['error']}\n\n"
            output += f"**执行的代码**:\n```python\n{code}\n```\n\n"
            output += "提示: 请检查文件名、列名是否正确，或尝试重新描述任务。"
            return output


def create_pandas_runner_tool(llm: ChatOpenAI, config: Dict[str, Any]) -> Tool:
    """
    创建 pandas runner 工具
    
    Args:
        llm: LLM 模型
        config: 配置字典
        
    Returns:
        LangChain Tool 对象
    """
    pandas_config = config.get('pandas_runner', {})
    
    runner = PandasRunner(
        llm=llm,
        data_dir=pandas_config.get('sandbox_paths', ['./data'])[0],
        output_dir="outputs",
        max_rows=pandas_config.get('max_rows', 100000),
        round_digits=pandas_config.get('round_digits', 3)
    )
    
    def pandas_runner_func(task: str) -> str:
        """
        Pandas runner 函数
        
        Args:
            task: 任务描述
            
        Returns:
            分析结果
        """
        return runner.run(task)
    
    return Tool(
        name="pandas_runner",
        description=(
            "Analyze CSV data in the data/ folder using pandas. "
            "Input should be a natural language description of the analysis task "
            "(e.g., 'calculate average age by gender', 'show correlation between X and Y'). "
            "Returns computation results with key numbers and interpretation."
        ),
        func=pandas_runner_func
    )

