import os
import subprocess
from langchain_core.tools import tool

# Configuration
SKILL_PATH = os.path.expanduser("~/.gemini/skills/image-to-pdf/SKILL.md")

@tool
def run_shell(command: str):
    """Execute shell commands. e.g. 'ls -F', 'python3 script.py'."""
    print(f"\n💻 [Shell] Executing: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if len(output) > 2000:
            output = output[:2000] + "...(truncated)"
        return output
    except Exception as e:
        return f"Error executing command: {e}"

@tool
def activate_skill(skill_name: str):
    """Activate a special skill. e.g. 'imagetopdf'."""
    print(f"\n⚡️ [Tool] Activating skill: {skill_name}...")
    
    # In a real dynamic system, this would map names to paths
    target_path = SKILL_PATH 
    
    if skill_name == "imagetopdf":
        if os.path.exists(target_path):
            with open(target_path, "r") as f:
                content = f.read()
            return f"SYSTEM_INJECTION: {content}"
        else:
            return f"Error: Skill definition file not found at {target_path}"
    else:
        return f"Error: Skill '{skill_name}' is not installed locally."

# Export list for binding
available_tools = [run_shell, activate_skill]
