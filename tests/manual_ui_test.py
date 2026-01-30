import time
import threading
import queue
import random
import sys
import os
import signal

# 模拟 main.py 的依赖环境
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

LOADING_PHRASES = [
    "正在加载量子核心...",
    "正在与母体通讯...",
    "别急，我在思考...",
]

def get_random_phrase():
    return random.choice(LOADING_PHRASES)

def mock_agent_worker(output_queue, stop_event):
    """模拟 Agent 行为：每隔 0.1s 吐一个字"""
    try:
        time.sleep(1) # 思考模拟
        
        mock_text = "这是一段很长的模拟文本，用于测试流式输出的效果。系统将在3秒后自动触发中断测试...\n\n这里是一个 Markdown 列表：\n- item 1\n- item 2"
        
        for char in mock_text:
            if stop_event.is_set():
                output_queue.put(("text", " [线程已收到停止信号]"))
                return
            
            output_queue.put(("text", char))
            time.sleep(0.05)
            
        output_queue.put(("tool_start", "run_shell"))
        time.sleep(2)
        if stop_event.is_set(): return
        output_queue.put(("tool_end", "执行成功！"))
        
    except Exception as e:
        output_queue.put(("error", e))
    finally:
        output_queue.put(("done", None))

def run_ui_test():
    console.print(Panel("[bold green]交互式 UI & 线程测试[/bold green]\n程序将在 3 秒后自动触发 Ctrl+C 信号。", border_style="green"))
    
    output_queue = queue.Queue()
    stop_event = threading.Event()
    
    worker_thread = threading.Thread(
        target=mock_agent_worker,
        args=(output_queue, stop_event),
        daemon=True
    )
    worker_thread.start()
    
    start_time = time.time()
    last_phrase_update = start_time
    current_phrase = get_random_phrase()
    is_thinking = True
    accumulated_content = ""
    
    try:
        with Live(console=console, refresh_per_second=12, vertical_overflow="visible") as live:
            while True:
                # 自动触发中断测试
                now = time.time()
                elapsed = now - start_time
                if elapsed > 3.0:
                    live.stop()
                    console.print("\n[bold yellow]⚡️ 自动触发 Ctrl+C 信号测试...[/bold yellow]")
                    os.kill(os.getpid(), signal.SIGINT)

                if now - last_phrase_update > 2.0:
                    current_phrase = get_random_phrase()
                    last_phrase_update = now
                
                if is_thinking:
                    live.update(Text.from_markup(f"[cyan]⠋[/cyan] {current_phrase} [dim]({elapsed:.1f}s)[/dim]"))
                
                try:
                    msg_type, data = output_queue.get(timeout=0.05)
                    
                    if msg_type == "done":
                        break
                    
                    if msg_type == "text":
                        is_thinking = False
                        accumulated_content += data
                        live.update(Markdown(f"**AI >** {accumulated_content}"))
                        
                    if msg_type == "tool_start":
                        live.stop()
                        live.start()
                        is_thinking = True
                        current_phrase = f"正在调用工具: {data}..."
                        accumulated_content = ""
                        
                    if msg_type == "tool_end":
                        live.update(Text(""))
                        live.stop()
                        console.print(Panel(f"结果: {data}", title="✅ 工具完成", border_style="green"))
                        live.start()
                        is_thinking = True
                        current_phrase = "继续思考..."

                except queue.Empty:
                    continue

    except KeyboardInterrupt:
        stop_event.set()
        console.print("\n[bold red]⛔ 测试成功：检测到中断信号！[/bold red]")
        worker_thread.join(timeout=1)
        if worker_thread.is_alive():
            console.print("[red]警告：后台线程未能及时退出！[/red]")
        else:
            console.print("[green]后台线程已安全销毁。[/green]")

if __name__ == "__main__":
    run_ui_test()
