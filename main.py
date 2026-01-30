#!/usr/bin/env python3
import sys
import os
import re
import json
import time
import threading
import queue
import random

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

# 趣味文案库 (中文版)
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

def agent_worker(app, inputs, output_queue, stop_event):
    """
    后台工作线程：负责执行 Agent 逻辑并将结果推送到队列。
    """
    try:
        # 使用双模式：messages 用于 UI 流式，updates 用于状态同步
        for mode, data in app.stream(inputs, stream_mode=["messages", "updates"]):
            if stop_event.is_set():
                break
            output_queue.put(("stream", mode, data))
    except Exception as e:
        output_queue.put(("error", None, e))
    finally:
        output_queue.put(("done", None, None))

def main():
    # 标题面板 (静态内容，安全)
    console.print(Panel.fit(
        "[bold cyan]🤖 Modular Agent CLI (v1.6)[/bold cyan]\n"
        "[dim]Powered by LangGraph & DeepSeek/OpenAI[/dim]",
        border_style="blue"
    ))
    console.print("💡 [green]提示[/green]: 试着说 [italic]‘帮我用 PPT 总结一下这个文件’[/italic]")
    console.print("🚪 输入 [bold red]exit[/bold red] 退出。\n")
    
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LLM_API_KEY"):
        console.print("⚠️  [bold yellow]警告[/bold yellow]: 未找到 API Key。请设置 LLM_API_KEY 或 OPENAI_API_KEY。", style="yellow")
        return

    # 初始化图
    try:
        app = build_graph()
    except Exception as e:
        # [安全修复] 使用 Text 对象打印异常
        err_msg = Text("❌ 初始化失败: ", style="bold red")
        err_msg.append(str(e))
        console.print(err_msg)
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
            
            # 线程通信机制
            output_queue = queue.Queue()
            stop_event = threading.Event()
            
            # 启动后台线程
            worker_thread = threading.Thread(
                target=agent_worker, 
                args=(app, inputs, output_queue, stop_event),
                daemon=True # 设置为守护线程，主程序退出时自动销毁
            )
            worker_thread.start()
            
            # 计时与文案状态
            start_time = time.time()
            last_phrase_update = start_time
            current_phrase = get_random_phrase()
            
            # UI 状态机
            is_thinking = True
            current_tool_status = ""
            
            # 使用 Live 刷新屏幕
            with Live(console=console, refresh_per_second=12, vertical_overflow="visible") as live:
                
                while True:
                    # 1. 检查是否被用户中断 (Ctrl+C) 在外层捕获
                    
                    # 2. 更新计时器和文案 (每 3 秒换一次文案)
                    now = time.time()
                    elapsed = now - start_time
                    if now - last_phrase_update > 3.0:
                        current_phrase = get_random_phrase()
                        last_phrase_update = now
                    
                    # 3. 渲染顶部状态栏 (Spinner)
                    if is_thinking:
                        # [安全修复] 对动态内容进行 escape
                        if "正在调用工具" in current_phrase:
                            # 已经是格式化过的，不需要 escape
                            display_phrase = current_phrase
                        else:
                            display_phrase = escape(current_phrase)

                        spinner_text = Text.from_markup(
                            f"[cyan]⠋[/cyan] {display_phrase} "
                            f"[dim]({elapsed:.1f}s)[/dim] "
                            f"(Ctrl+C 取消)"
                        )
                        # 如果有累积内容，显示在上方
                        if accumulated_content:
                            live.update(Markdown(f"**AI >** {accumulated_content} \n\n") )
                        else:
                            live.update(spinner_text)
                    
                    # 4. 消费队列 (非阻塞)
                    try:
                        # 每次取一个，但循环处理直到空，或者限制处理数量
                        msg_type, mode, data = output_queue.get(timeout=0.05)
                        
                        if msg_type == "done":
                            break
                        
                        if msg_type == "error":
                            raise data
                        
                        if msg_type == "stream":
                            # === 原来的处理逻辑搬过来 ===
                            
                            if mode == "messages":
                                chunk = data[0]
                                if isinstance(chunk, AIMessageChunk):
                                    if chunk.content:
                                        is_thinking = False 
                                        accumulated_content += chunk.content
                                        live.update(Markdown(f"**AI >** {accumulated_content}"))
                                    
                                    # 工具调用指令 -> 切换回 Spinner 模式
                                    if chunk.tool_call_chunks:
                                        tc = chunk.tool_call_chunks[0]
                                        if tc.get("name"):
                                            live.stop()
                                            live.start() # 清屏
                                            
                                            accumulated_content = "" # 清空缓冲区
                                            # [安全修复] escape 工具名
                                            safe_tool_name = escape(tc.get("name", "Unknown"))
                                            current_phrase = f"[yellow]⚙️ 正在调用工具: {safe_tool_name}...[/yellow]"
                                            is_thinking = True # 回到转圈模式
                                            # 强制立即刷新一次状态
                                            live.update(Text.from_markup(f"{current_phrase} ⠋"))

                            elif mode == "updates":
                                for node_name, node_output in data.items():
                                    if not node_output: continue
                                    
                                    if "active_skills" in node_output:
                                        active_skills = node_output["active_skills"]
                                    
                                    if "messages" in node_output:
                                        for msg in node_output["messages"]:
                                            if msg.id in seen_message_ids: continue
                                            seen_message_ids.add(msg.id)
                                            
                                            if isinstance(msg, AIMessage) and msg.tool_calls:
                                                # 动作展示
                                                live.update(Text("")) # 清空 Spinner
                                                live.stop()
                                                
                                                for tc in msg.tool_calls:
                                                    args_str = json.dumps(tc['args'], ensure_ascii=False)
                                                    if tc['name'] == 'run_shell' and 'command' in tc['args']:
                                                        # [安全修复] escape 命令参数
                                                        cmd_safe = escape(tc['args']['command'])
                                                        display_args = f"[bold white]$ {cmd_safe}[/bold white]"
                                                    else:
                                                        display_args = escape(args_str)

                                                    console.print(Panel(
                                                        display_args,
                                                        title=f"[bold blue]⚙️ 动作: {escape(tc['name'])}[/bold blue]",
                                                        border_style="blue",
                                                        expand=False
                                                    ))
                                                
                                                live.start()
                                                is_thinking = True
                                            
                                            elif isinstance(msg, ToolMessage):
                                                # 结果展示
                                                live.update(Text(""))
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
                                                    title=f"[bold green]✅ {escape(msg.name or '工具')} 执行结果[/bold green]",
                                                    border_style="green",
                                                    expand=False
                                                ))
                                                
                                                live.start()
                                                is_thinking = True
                                                current_phrase = "继续思考..." # 重置文案
                                            
                                            current_messages.append(msg)

                    except queue.Empty:
                        continue # 队列空了，继续循环刷新时间

            chat_history = current_messages

        except KeyboardInterrupt:
            # 捕获 Ctrl+C
            if 'stop_event' in locals():
                stop_event.set() # 通知后台线程停止
            console.print("\n[bold red]⛔ 用户取消操作 (User Cancelled)[/bold red]")
            # 等待一小会儿让线程清理（可选）
            time.sleep(0.2)
            continue
            
        except Exception as e:
            # [安全修复] 使用 Text 对象构建错误信息，彻底避免 MarkupError
            err_text = Text("\n❌ Error: ", style="bold red")
            # 这里的 str(e) 如果包含 Markup 标签，会被 Text 当作普通文本处理，不会解析
            err_text.append(str(e))
            console.print(err_text)

if __name__ == "__main__":
    main()
