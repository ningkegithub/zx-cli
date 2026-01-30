import sys
import os
import socket
from urllib.parse import urlparse
from langchain_core.messages import HumanMessage

# Add current directory to path so we can import agent_core
sys.path.append(os.getcwd())

try:
    from agent_core import build_graph
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def can_reach_llm():
    """快速检查 LLM 端点是否可达（解析 + TCP）。不可达则跳过在线测试。"""
    base_url = os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1"
    host = urlparse(base_url).hostname or base_url

    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except Exception as e:
        print(f"⚠️ 无法解析 LLM 域名: {host} ({e})，跳过在线测试。")
        return False

    try:
        with socket.create_connection((host, 443), timeout=3):
            return True
    except Exception as e:
        print(f"⚠️ 无法连接 LLM 端点: {host}:443 ({e})，跳过在线测试。")
        return False

def test_graph_execution():
    print("🧪 Starting Integration Test...")
    
    # Check API Key
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LLM_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY / LLM_API_KEY not found. Test might fail due to auth.")
    
    # 网络不可达时跳过
    if not can_reach_llm():
        return

    try:
        app = build_graph()
        print("✅ Graph built successfully.")
    except Exception as e:
        print(f"❌ Graph build failed: {e}")
        sys.exit(1)

    # Simulating a user input
    # We ask a simple question first to avoid complex skill loading issues if paths are wrong
    inputs = {
        "messages": [HumanMessage(content="Hello! Who are you?")],
        "active_skills": {}
    }

    print("🔄 Running graph invoke...")
    try:
        # We use invoke instead of stream for a quick check
        result = app.invoke(inputs)
        
        last_msg = result["messages"][-1]
        print(f"🤖 Final Response: {last_msg.content}")
        print("✅ Integration Test: SUCCESS")
             
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_graph_execution()
