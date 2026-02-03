import unittest
from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage
from agent_core.state import AgentState
import os
import sys

# Mock 依赖
sys.modules['langchain_openai'] = MagicMock()

# 导入目标模块
from agent_core import nodes

class TestPromptStructure(unittest.TestCase):
    
    @patch('agent_core.nodes.llm_with_tools')
    @patch('agent_core.nodes.get_available_skills_list', return_value="<skills_mock></skills_mock>")
    @patch('agent_core.nodes._get_memory_content', return_value="Memory Content")
    @patch('os.getcwd', return_value="/test/dir")
    def test_cognitive_layering_rendered(self, mock_getcwd, mock_memory, mock_skills, mock_llm):
        """验证 System Prompt 是否正确渲染了认知分层结构"""
        
        state = AgentState(messages=[], active_skills={})
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "OK"
        mock_llm.invoke.return_value = mock_response
        
        # 执行构建
        try:
            nodes.call_model(state)
        except Exception as e:
            self.fail(f"call_model 抛出了异常，说明 nodes.py 有语法错误: {e}")
            
        # 获取 Prompt
        args, _ = mock_llm.invoke.call_args
        messages = args[0]
        sys_msg = next((m for m in messages if isinstance(m, SystemMessage)), None)
        content = sys_msg.content
        
        # 1. 验证四个认知层级是否存在
        layers = [
            "🧠 大脑皮层 (形态切换)",
            "🧠 海马体 (记忆与检索)",
            "👀 感官系统 (环境感知)",
            "🖐️ 肢体动作 (环境执行)"
        ]
        for layer in layers:
            self.assertIn(layer, content, f"缺失认知层级: {layer}")
            
        # 2. 验证关键工具名是否更新
        self.assertIn("retrieve_knowledge", content, "Prompt 中未包含 retrieve_knowledge")
        self.assertIn("save_memory", content, "Prompt 中未包含 save_memory")
        self.assertIn("forget_memory", content, "Prompt 中未包含 forget_memory")
        
        # 3. 验证 run_shell 约束
        self.assertIn("严禁使用 run_shell", content)

        print("\n✅ Prompt 结构验证通过：认知分层与新工具名均已就位。")

if __name__ == '__main__':
    unittest.main()
