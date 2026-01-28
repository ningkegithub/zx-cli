import os
import yaml

# =====================
# 📂 路径配置常量
# =====================
CURRENT_FILE = os.path.abspath(__file__)
AGENT_CORE_DIR = os.path.dirname(CURRENT_FILE)
PROJECT_ROOT = os.path.dirname(AGENT_CORE_DIR)
INTERNAL_SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
USER_SKILLS_DIR = os.path.expanduser("~/.gemini/skills") # 保留用户目录作为扩展

# =====================
# 🛠️ 系统辅助函数
# =====================

def get_available_skills_list():
    """
    扫描所有可用技能并返回其名称和描述的 XML 格式字符串。
    此函数仅用于构建 System Prompt，不作为 Tool 暴露给 LLM。
    """
    search_dirs = [INTERNAL_SKILLS_DIR, USER_SKILLS_DIR]
    skills_found = []

    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
        
        # 遍历每个子目录
        for skill_dir in os.listdir(base_dir):
            skill_path = os.path.join(base_dir, skill_dir)
            if not os.path.isdir(skill_path):
                continue
            
            skill_md = os.path.join(skill_path, "SKILL.md")
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # 简单的 YAML Frontmatter 提取
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            metadata = yaml.safe_load(parts[1])
                            name = metadata.get("name", skill_dir)
                            desc = metadata.get("description", "无描述")
                            skills_found.append({"name": name, "description": desc})
                except Exception:
                    # 忽略解析错误的技能
                    continue
    
    # 转换为 XML 格式
    if not skills_found:
        return "<available_skills>\n  <!-- 未发现本地技能 -->\n</available_skills>"
    
    xml_parts = ["<available_skills>"]
    for s in skills_found:
        xml_parts.append(f'  <skill name="{s["name"]}">{s["description"]}</skill>')
    xml_parts.append("</available_skills>")
    
    return "\n".join(xml_parts)
