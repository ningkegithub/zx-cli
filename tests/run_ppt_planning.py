import sys
import os
from langchain_core.messages import HumanMessage, AIMessage

sys.path.append(os.getcwd())
from agent_core import build_graph

def run_task():
    print("🚀 开始执行 PPT 策划任务 (GPT-4o-mini 压力测试)...")
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ 未设置 OPENAI_API_KEY")
        return

    app = build_graph()
    chat_history = []
    active_skills = {}
    
    # 目标文件
    source_file = "某大型零售连锁企业门店管理数字化转型设计思维案例_公众号长文版.md"
    
    # 阶段一：提炼摘要
    print("\n📝 [Phase 1] 提炼核心摘要...")
    step1_query = f"读取 '{source_file}'，提炼出文章的核心痛点、解决方案和最终成效，简要写入 summary.md。"
    
    inputs = {"messages": chat_history + [HumanMessage(content=step1_query)], "active_skills": active_skills}
    
    for event in app.stream(inputs, stream_mode="values"):
        last_msg = event["messages"][-1]
        active_skills = event.get("active_skills", active_skills)
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                print(f"   🤖 动作: {tc['name']}")
        elif last_msg.content:
            # 简单打印部分思考，不刷屏
            pass
            
    chat_history = event["messages"]
    
    if os.path.exists("summary.md"):
        print("✅ summary.md 生成成功！")
        with open("summary.md", 'r') as f:
            print(f"   (预览: {f.read()[:100]}...)")
    else:
        print("❌ Phase 1 失败，文件未生成。")
        return

    # 阶段二：生成大纲
    print("\n📊 [Phase 2] 生成 PPT 大纲...")
    step2_query = "根据 summary.md 的内容，规划一份 10 页 PPT 的详细大纲。注明每一页的版式（封面/目录/正文/图表）、标题和核心要点。将结果写入 ppt_outline.md。"
    
    inputs = {"messages": chat_history + [HumanMessage(content=step2_query)], "active_skills": active_skills}
    
    for event in app.stream(inputs, stream_mode="values"):
        last_msg = event["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                print(f"   🤖 动作: {tc['name']}")

    if os.path.exists("ppt_outline.md"):
        print("✅ ppt_outline.md 生成成功！任务完成。")
    else:
        print("❌ Phase 2 失败。")

if __name__ == "__main__":
    run_task()
