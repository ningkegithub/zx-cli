import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# 确保能导入 agent_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_core.tools import retrieve_knowledge, PROJECT_ROOT

class TestToolRetrieveKnowledge(unittest.TestCase):
    
    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_retrieve_knowledge_success(self, mock_exists, mock_run):
        """测试知识检索工具调用成功"""
        # Mock 脚本存在
        mock_exists.return_value = True
        
        # Mock subprocess 返回结果
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Found relevant document: design_doc.pdf"
        mock_res.stderr = ""
        mock_run.return_value = mock_res
        
        # 调用工具
        result = retrieve_knowledge.invoke({"query": "design patterns", "collection": "documents"})
        
        # 验证调用参数
        # 检查是否正确拼装了 python path 和脚本路径
        args, kwargs = mock_run.call_args
        cmd_list = args[0]
        self.assertTrue(cmd_list[0].endswith("python") or cmd_list[0].endswith("python3"))
        self.assertTrue(cmd_list[1].endswith("query.py"))
        self.assertEqual(cmd_list[2], "design patterns")
        self.assertEqual(cmd_list[3], "documents")
        
        # 验证环境变量注入
        env_arg = kwargs.get("env")
        self.assertIsNotNone(env_arg)
        self.assertEqual(env_arg["PYTHONPATH"], PROJECT_ROOT)
        
        # 验证返回结果
        self.assertEqual(result, "Found relevant document: design_doc.pdf")

    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_retrieve_knowledge_script_missing(self, mock_exists, mock_run):
        """测试脚本文件缺失"""
        mock_exists.return_value = False
        
        result = retrieve_knowledge.invoke({"query": "test"})
        
        self.assertIn("错误", result)
        self.assertIn("未找到", result)
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_retrieve_knowledge_runtime_error(self, mock_exists, mock_run):
        """测试底层脚本运行时报错"""
        mock_exists.return_value = True
        
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""
        mock_res.stderr = "LanceDB Connection Failed"
        mock_run.return_value = mock_res
        
        result = retrieve_knowledge.invoke({"query": "test"})
        
        self.assertIn("检索失败", result)
        self.assertIn("LanceDB Connection Failed", result)

if __name__ == "__main__":
    unittest.main()
