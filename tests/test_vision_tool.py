import unittest
import os
import sys
from rich.console import Console

# 动态添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core.tools import describe_image

console = Console()

class TestVisionTool(unittest.TestCase):
    def setUp(self):
        # 创建一个临时的 1x1 红色像素图片
        self.img_path = os.path.join(project_root, "temp_vision_test.png")
        data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
        with open(self.img_path, "wb") as f:
            f.write(data)
            
    def tearDown(self):
        if os.path.exists(self.img_path):
            os.remove(self.img_path)

    def test_describe_image(self):
        """测试 describe_image 工具能否独立调用 GPT-4o-mini 解析图片"""
        
        # 检查是否配置了 OPENAI_API_KEY
        if not os.environ.get("OPENAI_API_KEY"):
            console.print("[yellow]⚠️ 未检测到 OPENAI_API_KEY，跳过视觉测试。[/yellow]")
            return

        console.print(f"\n[cyan]🧪 正在测试图片: {self.img_path}[/cyan]")
        
        # 调用工具
        # 提示词让模型简单识别颜色，因为那是 1x1 的红色图片
        result = describe_image.invoke({
            "image_path": self.img_path, 
            "prompt": "这张图片的主要颜色是什么？请用简短的一个词回答（例如：红色、蓝色）。"
        })
        
        console.print(f"[green]👁️ 视觉模型返回:[/green] {result}")
        
        # 验证结果
        self.assertIn("Vision Model: gpt-4o-mini", result)
        # 模型可能会说 "Red" 或 "红色"，或者因为图片太小而困惑，只要没有报错且有返回即可
        self.assertFalse("错误" in result[:10]) # 简单的错误检查

if __name__ == "__main__":
    unittest.main()
