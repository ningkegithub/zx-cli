#!/usr/bin/env python3
import sys
import os
import re
import json

# Rich 库
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.live import Live
from rich.markup import escape

# LangChain & PromptToolkit
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# Agent Core
from agent_core import build_graph

console = Console()

def main():
    # 自动创建 output 目录，保持根目录整洁
    os.makedirs("output", exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]🤖 Modular Agent CLI (v1.5)[/bold cyan]\n"
        "[dim]Powered by LangGraph & DeepSeek/OpenAI[/dim]",
        border_style="blue"
    ))
    console.print("💡 [green]提示[/green]: 试着说 [italic]‘帮我查看当前目录下的文件’[/italic]")
    console.print("🚪 输入 [bold red]exit[/bold red] 退出。\n")
    
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LLM_API_KEY"):
        console.print("⚠️  [bold yellow]警告[/bold yellow]: 未找到 API Key。", style="yellow")
        return

    try:
        app = build_graph()
    except Exception as e:
        console.print(f"❌ [bold red]初始化失败:[/bold red] {e}")
        return
    
    chat_history = []
    active_skills = {}
    style = Style.from_dict({'prompt': 'ansigreen bold'})
    session = PromptSession()

    while True:
        try:
            print()
            user_input = session.prompt("用户> ", style=style)
            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input.strip():
                continue

            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
                "active_skills": active_skills
            }
            
            # 状态变量
            current_messages = inputs["messages"]
            accumulated_content = ""
            seen_message_ids = set() # 消息去重
            
            with Live(console=console, refresh_per_second=12, vertical_overflow="visible") as live:
                live.update(Text("⠋ 正在思考...", style="cyan"))
                
                # 使用双模式：messages 用于 UI 流式，updates 用于状态同步
                for mode, data in app.stream(inputs, stream_mode=["messages", "updates"]):
                    
                    # --- 1. 流式展示 Token (仅展示文本) ---
                    if mode == "messages":
                        chunk = data[0]
                        if isinstance(chunk, AIMessageChunk) and chunk.content:
                            accumulated_content += chunk.content
                            display_content = f"**AI >** {accumulated_content}"
                            live.update(Markdown(display_content))

                    # --- 2. 处理节点更新 (展示动作和结果) ---
                    elif mode == "updates":
                        for node_name, node_output in data.items():
                            if not node_output: continue
                            
                            # 更新技能池
                            if "active_skills" in node_output:
                                active_skills = node_output["active_skills"]
                            
                            if "messages" in node_output:
                                for msg in node_output["messages"]:
                                    if msg.id in seen_message_ids: continue
                                    seen_message_ids.add(msg.id)
                                    
                                    # 情况 A: AI 决定发起动作 (AIMessage 包含 tool_calls)
                                    if isinstance(msg, AIMessage) and msg.tool_calls:
                                        # 清除 Spinner 残留
                                        live.update(Text(""))
                                        live.refresh()
                                        live.stop() 
                                        
                                        for tc in msg.tool_calls:
                                            # 提取参数字符串
                                            args_str = json.dumps(tc['args'], ensure_ascii=False)
                                            # 针对 run_shell 做特殊美化
                                            if tc['name'] == 'run_shell' and 'command' in tc['args']:
                                                display_args = f"[bold white]$ {tc['args']['command']}[/bold white]"
                                            else:
                                                display_args = escape(args_str)

                                            console.print(Panel(
                                                display_args,
                                                title=f"[bold blue]⚙️ 动作: {tc['name']}[/bold blue]",
                                                border_style="blue",
                                                expand=False
                                            ))
                                        
                                        # 开启新一轮转圈
                                        accumulated_content = "" 
                                        live.start()
                                        live.update(Text("⠋ 正在执行工具...", style="yellow"))
                                    
                                    # 情况 B: 工具返回结果 (ToolMessage)
                                    elif isinstance(msg, ToolMessage):
                                        # 清除 Spinner 残留
                                        live.update(Text(""))
                                        live.refresh()
                                        live.stop()
                                        
                                        raw_content = msg.content.strip()
                                        if "SYSTEM_INJECTION" in raw_content:
                                            display_res = "[系统] 技能协议已成功加载。"
                                        else:
                                            safe_res = escape(raw_content)
                                            lines = safe_res.split('\n')
                                            display_res = "\n".join(lines[:10]) + (f"\n... (截断)" if len(lines) > 10 else "")
                                        
                                        console.print(Panel(
                                            display_res or "[无返回结果]",
                                            title=f"[bold green]✅ {msg.name or '工具'} 执行结果[/bold green]",
                                            border_style="green",
                                            expand=False
                                        ))
                                        
                                        # 继续思考转圈
                                        live.start()
                                        live.update(Text("⠋ 继续思考...", style="cyan"))
                                        live.refresh()
                                    
                                    current_messages.append(msg)

            chat_history = current_messages

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"\n❌ [bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
