import sys
import os

# 动态添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core.tools import activate_skill

def test_activate_skill_encoding():
    print("🧪 测试技能读取编码 (activate_skill)...")
    
    result = activate_skill.invoke({"skill_name": "ppt_master"})
    if "SYSTEM_INJECTION" not in result:
        print(f"❌ 失败: 未返回 SYSTEM_INJECTION。\n返回: {result}")
        sys.exit(1)
    
    # 校验中文内容是否被正确读取
    if "PPT 渲染大师" not in result:
        print("❌ 失败: 中文内容疑似未正确读取或被破坏。")
        sys.exit(1)

    print("✅ 技能读取编码通过！")

if __name__ == "__main__":
    test_activate_skill_encoding()
