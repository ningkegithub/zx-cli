import json
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.markup import escape
from rich.console import Console

console = Console()

def render_header():
    console.print(Panel.fit(
        "[bold cyan]🤖 Modular Agent CLI (v1.7)[/bold cyan]\n"
        "[dim]Powered by LangGraph & DeepSeek/OpenAI[/dim]",
        border_style="blue"
    ))
    console.print("💡 [green]提示[/green]: 试着说 [italic]“帮我用 PPT 总结一下这个文件”[/italic]")
    console.print("🚪 输入 [bold red]exit[/bold red] 退出。\n")

def get_spinner_text(phrase, elapsed):
    # [安全] 确保文案被转义
    safe_phrase = escape(phrase) if "正在调用工具" not in phrase else phrase
    return Text.from_markup(
        f"[cyan]⠋[/cyan] {safe_phrase} "
        f"[dim]({elapsed:.1f}s)[/dim] "
        f"[red](Ctrl+C 取消)[/red]"
    )

def render_tool_action(console, tool_name, tool_args):
    """渲染工具动作面板 (蓝色)"""
    args_str = json.dumps(tool_args, ensure_ascii=False)
    
    if tool_name == 'run_shell' and 'command' in tool_args:
        cmd_safe = escape(tool_args['command'])
        display_args = f"[bold white]$ {cmd_safe}[/bold white]"
    else:
        display_args = escape(args_str)

    console.print(Panel(
        display_args,
        title=f"[bold blue]⚙️ 动作: {escape(tool_name)}[/bold blue]",
        border_style="blue",
        expand=False
    ))

def render_tool_result(console, tool_name, content):
    """渲染工具结果面板 (绿色)"""
    raw_content = content.strip()
    if "SYSTEM_INJECTION" in raw_content:
        display_res = "[系统] 技能协议已成功加载。"
    else:
        safe_res = escape(raw_content)
        lines = safe_res.split('\n')
        # 最多显示 10 行
        if len(lines) > 10:
            display_res = "\n".join(lines[:10]) + f"\n... (截断，共 {len(lines)} 行)"
        else:
            display_res = safe_res
    
    console.print(Panel(
        display_res or "[无返回结果]",
        title=f"[bold green]✅ {escape(tool_name or '工具')} 执行结果[/bold green]",
        border_style="green",
        expand=False
    ))

def render_error(console, e):
    """安全渲染错误信息"""
    err_text = Text("\n❌ Error: ", style="bold red")
    err_text.append(str(e))
    console.print(err_text)
