#!/usr/bin/env python3
import sys
import time
import threading
import queue

# Rich & PromptToolkit
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown
from rich.markup import escape
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# 核心依赖
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from agent_core import build_graph

# 本地模块
from cli.config import console, check_api_key, get_random_phrase
from cli.async_worker import run_worker
import cli.ui as ui

def main():
    ui.render_header()
    
    if not check_api_key():
        return

    try:
        app = build_graph()
    except Exception as e:
        ui.render_error(console, f"初始化失败: {e}")
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
                console.print("[dim]👋 再见！[/dim]")
                sys.exit(0)
            if not user_input.strip():
                continue

            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
                "active_skills": active_skills
            }
            
            # --- 初始化状态 ---
            current_messages = inputs["messages"]
            accumulated_content = ""
            seen_message_ids = {msg.id for msg in chat_history}
            
            # 线程通信
            output_queue = queue.Queue()
            stop_event = threading.Event()
            worker_thread = threading.Thread(
                target=run_worker, 
                args=(app, inputs, output_queue, stop_event), 
                daemon=True
            )
            worker_thread.start()
            
            # UI 状态
            start_time = time.time()
            last_phrase_update = start_time
            current_phrase = get_random_phrase()
            is_thinking = True
            
            with Live(console=console, refresh_per_second=12, vertical_overflow="visible") as live:
                while True:
                    # 更新状态栏
                    now = time.time()
                    elapsed = now - start_time
                    if now - last_phrase_update > 3.0:
                        current_phrase = get_random_phrase()
                        last_phrase_update = now
                    
                    if is_thinking:
                        live.update(ui.get_spinner_text(current_phrase, elapsed))
                        if accumulated_content:
                            # 技巧：同时显示 Markdown 和 Spinner 比较难，这里优先保证 Markdown 更新
                            # 实际上 Live update 会覆盖。所以如果正在输出文字，Spinner 会暂时消失。
                            # 为了体验，我们在文字输出时不显示 Spinner，只显示文字
                            live.update(Markdown(f"**AI >** {accumulated_content}"))

                    # 消费队列
                    try:
                        msg_type, mode, data = output_queue.get(timeout=0.05)
                        
                        if msg_type == "done": break
                        if msg_type == "error": raise data
                        
                        if msg_type == "stream":
                            if mode == "messages":
                                chunk = data[0]
                                if isinstance(chunk, AIMessageChunk):
                                    if chunk.content:
                                        is_thinking = False # 有字了，停转圈
                                        accumulated_content += chunk.content
                                        live.update(Markdown(f"**AI >** {accumulated_content}"))
                                    
                                    if chunk.tool_call_chunks:
                                        tc = chunk.tool_call_chunks[0]
                                        if tc.get("name"):
                                            # 切换状态
                                            live.stop()
                                            live.start() # 清屏
                                            accumulated_content = ""
                                            
                                            safe_name = escape(tc.get("name", "Unknown"))
                                            current_phrase = f"[yellow]⚙️ 正在调用工具: {safe_name}...[/yellow]"
                                            is_thinking = True
                                            live.update(ui.get_spinner_text(current_phrase, elapsed))

                            elif mode == "updates":
                                for _, node_output in data.items():
                                    if not node_output: continue
                                    
                                    if "active_skills" in node_output:
                                        active_skills = node_output["active_skills"]
                                    
                                    if "messages" in node_output:
                                        for msg in node_output["messages"]:
                                            if msg.id in seen_message_ids: continue
                                            seen_message_ids.add(msg.id)
                                            
                                            # 展示动作
                                            if isinstance(msg, AIMessage) and msg.tool_calls:
                                                live.update(Text("")) # 清空
                                                live.stop()
                                                for tc in msg.tool_calls:
                                                    ui.render_tool_action(console, tc['name'], tc['args'])
                                                live.start()
                                                is_thinking = True
                                            
                                            # 展示结果
                                            elif isinstance(msg, ToolMessage):
                                                live.update(Text(""))
                                                live.stop()
                                                ui.render_tool_result(console, msg.name, msg.content)
                                                live.start()
                                                is_thinking = True
                                                current_phrase = "继续思考..."
                                            
                                            current_messages.append(msg)

                    except queue.Empty:
                        continue

            chat_history = current_messages

        except KeyboardInterrupt:
            stop_event.set()
            console.print("\n[bold red]⛔ 用户取消操作 (User Cancelled)[/bold red]")
            time.sleep(0.2)
            continue
        except Exception as e:
            ui.render_error(console, e)

if __name__ == "__main__":
    main()