import os
import random
from rich.console import Console

console = Console()

# 趣味文案库
LOADING_PHRASES = [
    "正在与赛博空间建立连接...",
    "别急，让子弹飞一会儿...",
    "正在将咖啡因转化为代码...",
    "正在查询全宇宙的知识库...",
    "思考中... CPU 正在冒烟...",
    "正在与模型进行脑波同步...",
    "不要惊慌...",
    "正在构建思维殿堂...",
    "正在解析矩阵代码...",
    "喝口水，马上就好..."
]

def get_random_phrase():
    return random.choice(LOADING_PHRASES)

def check_api_key():
    """检查必要的 API Key"""
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LLM_API_KEY"):
        console.print("⚠️  [bold yellow]警告[/bold yellow]: 未找到 API Key。请设置 LLM_API_KEY 或 OPENAI_API_KEY。", style="yellow")
        return False
    return True
