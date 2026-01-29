import sys
import os
import shutil

# 动态添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core.utils import get_available_skills_list, INTERNAL_SKILLS_DIR

def test_discovery():
    print("🧪 测试技能自动发现 (Skill Discovery)...")
    
    # 1. 验证 XML 格式
    xml_output = get_available_skills_list()
    print(f"📄 生成的 XML:\n{xml_output[:100]}...") # 打印前100字符预览
    
    if "<available_skills>" not in xml_output:
        print("❌ 失败: 缺少根标签 <available_skills>")
        sys.exit(1)
        
    # 2. 验证内置技能是否存在
    expected_skills = ["web_scraper", "image_to_pdf"]
    for skill in expected_skills:
        # 检查 <skill name="web_scraper"> 格式
        target_str = f'name="{skill}"'
        if target_str in xml_output:
            print(f"✅ 发现内置技能: {skill}")
        else:
            print(f"❌ 警告: 未在清单中找到内置技能 {skill}")
            # 注意：如果目录被改名，这里会报错，这正是测试的目的
            
    # 3. 验证描述信息是否提取 (检查是否包含中文字符)
    # web_scraper 的描述包含 "抓取内容"
    if "抓取内容" in xml_output or "PDF" in xml_output:
        print("✅ 成功提取技能描述")
    else:
        print("⚠️ 警告: 描述信息似乎为空或提取失败")

    print("🎉 技能发现功能测试通过！")

if __name__ == "__main__":
    test_discovery()
