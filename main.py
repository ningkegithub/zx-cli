#!/usr/bin/env python3
import sys
import re
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from agent_core import build_graph

def main():
    print("🤖 模块化智能体 CLI (v1.0)")
    print("---------------------------")
    print("提示：你可以试着说“把当前文件夹下的图片合并为 PDF”。")
    print("输入 'exit' 或 'quit' 退出。\n")
    
    # Check API Key
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  警告：在环境变量中未找到 OPENAI_API_KEY。")
        print("   请运行：export OPENAI_API_KEY='sk-...' ")
        return

    # 初始化图
    app = build_graph()
    
    chat_history = []
    active_skills = {} # 改为字典存储多技能

    # 初始化交互 Session (支持历史记录、中文退格优化)
    style = Style.from_dict({
        'prompt': 'ansigreen bold',
    })
    session = PromptSession()

    while True:
        try:
            user_input = session.prompt("用户> ", style=style)
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Skip empty input
            if not user_input.strip():
                continue

            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
                "active_skills": active_skills
            }
            
            print("   (思考中...)")
            # 关键：初始化已读 ID，包含历史消息，避免重复打印
            seen_message_ids = {msg.id for msg in chat_history} 

            for event in app.stream(inputs, stream_mode="values"):
                # 获取当前所有消息
                all_msgs = event["messages"]
                # 从事件中获取更新后的技能池
                active_skills = event.get("active_skills", active_skills)
                
                # 只处理还没打印过的消息
                for msg in all_msgs:
                    if msg.id in seen_message_ids:
                        continue
                    
                    if isinstance(msg, AIMessage):
                        # 1. 如果有工具调用，content 视为思考过程
                        if msg.tool_calls:
                            if msg.content:
                                # [UI 清洗] 去除重复的思考前缀 (DeepSeek 有时会输出两次)
                                clean_content = msg.content.strip()
                                clean_content = re.sub(r'(🧠\s*\[思考\]\s*)+', '🧠 [思考] ', clean_content)
                                print(f"{clean_content}")
                            for tc in msg.tool_calls:
                                print(f"   🤖 动作: {tc['name']}({tc['args']})")
                        # 2. 如果没有工具调用，content 视为最终回答
                        elif msg.content:
                            # 过滤掉之前的用户输入对应的 AI 响应（如果是旧消息）
                            # 实际上因为我们在 stream 内部处理，msg 只要是新的就打印
                            print(f"Agent> {msg.content.strip()}")
                        
                        seen_message_ids.add(msg.id)
                    
                    elif isinstance(msg, ToolMessage):
                        # 展示工具执行结果预览，增加“轮次感”
                        res_text = msg.content.strip().replace("\n", " ")
                        if len(res_text) > 60:
                            res_text = res_text[:60] + "..."
                        print(f"   ✅ [结果] {res_text}")
                        seen_message_ids.add(msg.id)
                
            chat_history = event["messages"]
            print("")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
