#!/usr/bin/env python3
import sys
import time
import threading
import queue
import signal

# Rich & PromptToolkit
from rich.live import Live
from rich.text import Text
from rich.markup import escape
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# 核心依赖
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk
from agent_core import build_graph
from agent_core.nodes import shutdown_llm_clients

# 本地模块
from cli.config import console, check_api_key, get_random_phrase
from cli.async_worker import run_worker
import cli.ui as ui

def _msg_key(msg):
    """生成消息去重键：优先使用消息 id，缺失时回退到对象地址。"""
    msg_id = getattr(msg, "id", None)
    if msg_id:
        return f"id:{msg_id}"
    # 注意：部分消息可能没有 id，避免 None 造成全量去重
    return f"obj:{id(msg)}"

def _maybe_trim_prefix(text: str, trim_prefix: str) -> tuple[str, str]:
    """如果新内容重复旧前缀，则在显示时裁剪该前缀。"""
    if not trim_prefix or not text:
        return text, trim_prefix
    # 前缀还没完整到达，先不显示，避免重复闪现
    if trim_prefix.startswith(text):
        return "", trim_prefix
    # 新内容包含旧前缀，裁剪掉
    if text.startswith(trim_prefix):
        return text[len(trim_prefix):].lstrip(), ""
    # 无匹配则直接显示并清除前缀
    return text, ""

def _render_live(live, accumulated_content: str, spinner_text: Text | None):
    """更新 Live 视图（单区）。"""
    if accumulated_content:
        live.update(Markdown(f"**AI >** {accumulated_content}"))
    else:
        live.update(spinner_text or Text(""))

def _flush_live_snapshot(live, accumulated_content: str):
    """将当前 Live 内容固化为持久输出，避免被清屏覆盖。"""
    if not accumulated_content:
        return
    live.update(Text(""))
    live.refresh()
    live.stop()
    console.print(Markdown(f"**AI >** {accumulated_content}"))

def _graceful_exit(stop_event, worker_thread):
    """退出前尽量停止后台线程，并忽略后续 SIGINT 以避免 shutdown 噪音。"""
    try:
        if stop_event and worker_thread and worker_thread.is_alive():
            stop_event.set()
            worker_thread.join(timeout=1.0)
        shutdown_llm_clients()
    finally:
        try:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        except Exception:
            pass

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

    last_interrupt_time = 0.0

    while True:
        stop_event = None
        worker_thread = None
        try:
            print()
            user_input = session.prompt("用户> ", style=style)
            if user_input.lower() in ["exit", "quit"]:
                console.print("[dim]👋 再见！[/dim]")
                _graceful_exit(stop_event, worker_thread)
                return
            if not user_input.strip():
                continue

            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
                "active_skills": active_skills
            }
            
            # --- 初始化状态 ---
            current_messages = inputs["messages"]
            accumulated_content = ""
            last_flushed_content = ""
            display_trim_prefix = ""
            seen_message_keys = {_msg_key(msg) for msg in chat_history}
            
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
                        spinner_text = ui.get_spinner_text(current_phrase, elapsed)
                        display_content, display_trim_prefix = _maybe_trim_prefix(accumulated_content, display_trim_prefix)
                        _render_live(live, display_content, spinner_text)
                    else:
                        display_content, display_trim_prefix = _maybe_trim_prefix(accumulated_content, display_trim_prefix)
                        _render_live(live, display_content, None)

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
                                        display_content, display_trim_prefix = _maybe_trim_prefix(accumulated_content, display_trim_prefix)
                                        _render_live(live, display_content, None)
                                    
                                    if chunk.tool_call_chunks:
                                        tc = chunk.tool_call_chunks[0]
                                        if tc.get("name"):
                                            # 切换状态前，先固化当前流式内容，避免被清屏覆盖
                                            if accumulated_content and accumulated_content != last_flushed_content:
                                                _flush_live_snapshot(live, accumulated_content)
                                                last_flushed_content = accumulated_content
                                                display_trim_prefix = last_flushed_content
                                            live.start() # 清屏
                                            accumulated_content = ""
                                            
                                            safe_name = escape(tc.get("name", "Unknown"))
                                            # 在 Spinner 中显式显示正在准备调用的工具名
                                            current_phrase = f"[bold yellow]⚙️ 准备执行: {safe_name}...[/bold yellow]"
                                            is_thinking = True
                                            _render_live(live, accumulated_content, ui.get_spinner_text(current_phrase, elapsed))

                            elif mode == "updates":
                                for _, node_output in data.items():
                                    if not node_output: continue
                                    
                                    if "active_skills" in node_output:
                                        active_skills = node_output["active_skills"]
                                    
                                    if "messages" in node_output:
                                        for msg in node_output["messages"]:
                                            msg_key = _msg_key(msg)
                                            if msg_key in seen_message_keys: continue
                                            seen_message_keys.add(msg_key)
                                            
                                            # [优化] 跳过 AIMessage 的文本部分，防止与流式输出重复
                                            # 但如果包含工具调用，必须在这里渲染工具卡片（因为 Stream 模式下无法获取完整参数）
                                            if isinstance(msg, AIMessage):
                                                if msg.tool_calls:
                                                    live.update(Text(""))
                                                    live.stop()
                                                    for tc in msg.tool_calls:
                                                        ui.render_tool_action(console, tc['name'], tc['args'])
                                                    live.start()
                                                    is_thinking = True # 工具执行中
                                                
                                                current_messages.append(msg)
                                                continue
                                            
                                            # 展示结果 (ToolMessage)
                                            # 工具结果通常不通过 stream message chunk 发送，或者是整块发送，适合在这里处理
                                            if isinstance(msg, ToolMessage):
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
            now = time.monotonic()
            # 二次 Ctrl+C 直接退出
            if now - last_interrupt_time < 1.5:
                console.print("\n[bold red]👋 已退出[/bold red]")
                _graceful_exit(stop_event, worker_thread)
                return
            last_interrupt_time = now

            # 任务中则取消，否则直接退出
            if stop_event and worker_thread and worker_thread.is_alive():
                stop_event.set()
                console.print("\n[bold red]⛔ 用户取消操作 (User Cancelled)[/bold red]")
                time.sleep(0.2)
                continue
            console.print("\n[bold red]👋 已退出[/bold red]")
            _graceful_exit(stop_event, worker_thread)
            return
        except Exception as e:
            ui.render_error(console, e)

if __name__ == "__main__":
    main()
