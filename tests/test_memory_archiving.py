import unittest
import os
import sys
from langchain_core.messages import HumanMessage, AIMessage

# 确保能导入 main.py
sys.path.append(os.getcwd())
from main import _archive_session
from agent_core.utils import USER_MEMORY_DIR

class TestMemoryArchiving(unittest.TestCase):
    
    def test_archive_and_ingest_call(self):
        """验证会话归档是否成功生成文件并尝试调用同步"""
        print("\n🧪 Testing Session Archiving...")
        
        # 1. 模拟对话历史
        history = [
            HumanMessage(content="你好，帮我记一下今天天气不错。"),
            AIMessage(content="好的，我已经记下了。")
        ]
        
        # 2. 调用归档函数
        # 注意：这里会真实调用 subprocess，为了防止模型下载耗时，我们假设 ingest.py 已存在
        try:
            _archive_session(history)
            
            # 3. 检查文件是否生成
            import datetime
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            logs_dir = os.path.join(USER_MEMORY_DIR, "logs", today)
            
            self.assertTrue(os.path.exists(logs_dir), f"Log directory {logs_dir} not created")
            
            files = [f for f in os.listdir(logs_dir) if f.endswith("_session.md")]
            self.assertGreater(len(files), 0, "No session markdown file found")
            
            # 读取最新文件内容
            latest_file = os.path.join(logs_dir, sorted(files)[-1])
            with open(latest_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("今天天气不错", content)
                self.assertIn("## User", content)
                self.assertIn("## AI", content)
                
            print(f"    ✅ Session archived successfully to: {latest_file}")
            
        except Exception as e:
            self.fail(f"Archiving failed with error: {e}")

if __name__ == '__main__':
    unittest.main()
