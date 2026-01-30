import sys
import os
import time
import queue
import threading
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown

# 动态添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入重构后的模块
import cli.ui as ui
from cli.config import console, get_random_phrase

def run_integration_ui_test():
    console.print(ui.Panel("[bold green]集成 UI 组件测试 (v1.7)[/bold green]\n验证 cli/ui.py 的渲染逻辑。", border_style="green"))
    
    # 1. 测试静态渲染函数
    print("\n--- 测试静态面板 ---")
    try:
        ui.render_header()
        ui.render_tool_action(console, "run_shell", {"command": "echo 'Hello World'"})
        ui.render_tool_result(console, "run_shell", "执行成功\n第二行\n[系统] 注入成功")
        # 测试异常字符
        ui.render_tool_result(console, "danger_tool", "包含 [bold red]未闭合标签 的危险内容")
        print("✅ 静态渲染通过 (无 MarkupError)")
    except Exception as e:
        print(f"❌ 静态渲染失败: {e}")
        return

    # 2. 测试动态 Spinner (模拟 main.py 循环)
    print("\n--- 测试动态交互 ---")
    start_time = time.time()
    
    try:
        with Live(console=console, refresh_per_second=12, vertical_overflow="visible") as live:
            for i in range(20):
                elapsed = time.time() - start_time
                phrase = get_random_phrase()
                
                # 测试 get_spinner_text
                text = ui.get_spinner_text(phrase, elapsed)
                live.update(text)
                time.sleep(0.1)
                
                if i == 10:
                    # 模拟Markdown流
                    live.update(Markdown("**AI >** 突然开始说话了..."))
                    time.sleep(1)
                    
            print("\n✅ 动态交互通过")
            
    except Exception as e:
        print(f"❌ 动态交互失败: {e}")

if __name__ == "__main__":
    run_integration_ui_test()
