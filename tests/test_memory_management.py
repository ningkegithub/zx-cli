import unittest
import os
import sys
import shutil
from unittest.mock import patch

# 确保能导入 agent_core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_core.tools import save_memory, forget_memory

class TestMemoryManagement(unittest.TestCase):
    def setUp(self):
        # 使用临时文件作为测试记忆库
        self.test_memory_file = "tests/TEST_MEMORY.md"
        # 确保环境干净
        if os.path.exists(self.test_memory_file):
            os.remove(self.test_memory_file)
        
        # 预制一些初始数据
        with open(self.test_memory_file, "w", encoding="utf-8") as f:
            f.write("# Test Memory\n")
            f.write("- [2026-02-01 10:00] Initial fact 1\n")
            f.write("- [2026-02-01 10:05] Initial fact 2\n")

    def tearDown(self):
        # 清理临时文件
        if os.path.exists(self.test_memory_file):
            os.remove(self.test_memory_file)

    def test_save_memory_fresh(self):
        """测试 save_memory: 添加全新的记忆"""
        with patch("agent_core.tools.MEMORY_FILE", self.test_memory_file):
            result = save_memory.invoke({"content": "New fresh fact"})
            
        self.assertIn("成功保存记忆", result)
        
        with open(self.test_memory_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("New fresh fact", content)

    def test_save_memory_duplicate(self):
        """测试 save_memory: 添加重复/高度相似的记忆 (应被拦截)"""
        with patch("agent_core.tools.MEMORY_FILE", self.test_memory_file):
            # 尝试添加一个与 "Initial fact 1" 极度相似的内容
            result = save_memory.invoke({"content": "Initial fact 1"})
        
        self.assertIn("记忆已存在", result)
        self.assertIn("跳过写入", result)

        # 验证文件行数没有增加 (初始3行: Header + 2 facts)
        with open(self.test_memory_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 3)

    def test_forget_memory_success(self):
        """测试 forget_memory: 物理删除记忆"""
        with patch("agent_core.tools.MEMORY_FILE", self.test_memory_file):
            # 删除包含 "fact 1" 的记录
            result = forget_memory.invoke({"content": "fact 1"})
            
        self.assertIn("成功遗忘 1 条", result)
        
        with open(self.test_memory_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertNotIn("Initial fact 1", content)
        self.assertIn("Initial fact 2", content) # 确保没误删其他内容

    def test_forget_memory_not_found(self):
        """测试 forget_memory: 删除不存在的记忆"""
        with patch("agent_core.tools.MEMORY_FILE", self.test_memory_file):
            result = forget_memory.invoke({"content": "Ghost fact"})
            
        self.assertIn("未找到", result)

if __name__ == "__main__":
    unittest.main()