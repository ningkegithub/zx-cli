import sys
import os

# 动态添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core.tools import activate_skill

def test_skill_suggestions():
    print("🧪 测试技能建议提示 (activate_skill)...")
    
    result = activate_skill.invoke({"skill_name": "imagetopdf"})
    if "image_to_pdf" not in result:
        print(f"❌ 失败: 未给出建议技能。返回: {result}")
        sys.exit(1)

    print("✅ 技能建议提示通过！")

if __name__ == "__main__":
    test_skill_suggestions()
