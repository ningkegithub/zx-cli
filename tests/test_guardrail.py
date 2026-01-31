import sys
import os
from langchain_core.messages import AIMessage, SystemMessage

sys.path.append(os.getcwd())
from agent_core.nodes import call_model

class MockLLM:
    """模拟一个不听话的 LLM，试图并发读写"""
    def invoke(self, messages):
        return AIMessage(
            content="我想要抢跑！",
            tool_calls=[
                {"name": "read_file", "args": {"file_path": "a.txt"}, "id": "1"},
                {"name": "write_file", "args": {"file_path": "b.txt", "content": "bad"}, "id": "2"},
                {"name": "activate_skill", "args": {"skill_name": "test"}, "id": "3"},
                {"name": "run_shell", "args": {"command": "ls"}, "id": "4"}
            ]
        )
    def bind_tools(self, tools): return self

def test_guardrail_logic():
    print("🧪 测试安全守卫 (Hard Guardrail)...")
    
    # 劫持 LLM
    import agent_core.nodes
    original_llm = agent_core.nodes.llm_with_tools
    agent_core.nodes.llm_with_tools = MockLLM()
    
    try:
        state = {"messages": [SystemMessage(content="test")], "active_skills": {}}
        print("⚡️ 触发模拟调用...")
        result = call_model(state)
        response = result["messages"][0]
        
        tool_names = [tc["name"] for tc in response.tool_calls]
        print(f"📊 过滤后的工具列表: {tool_names}")
        
        # 验证 1: 写操作被拦截
        if "write_file" in tool_names:
            print("❌ 失败: write_file 未被拦截！")
            sys.exit(1)
        
        # 验证 2: 抢跑执行被拦截 (activate_skill vs run_shell)
        # 根据逻辑，如果同时有 activate_skill，其他都被干掉
        if "activate_skill" in tool_names and "run_shell" in tool_names:
             print("❌ 失败: 激活与执行未隔离！")
             sys.exit(1)
             
        # 验证 3: 内容被重写
        # 新逻辑：不再强制包含表情，而是检查是否包含核心拦截信息
        if "我需要先激活技能" not in response.content:
             print("❌ 失败: Agent 回复未被重写引导！")
             print(f"实际内容: {response.content}")
             sys.exit(1)

        print("✅ 安全守卫拦截逻辑验证通过！")
            
    finally:
        # 还原现场
        agent_core.nodes.llm_with_tools = original_llm

if __name__ == "__main__":
    test_guardrail_logic()
