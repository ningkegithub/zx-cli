import os
import difflib
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

def _extract_frontmatter_metadata(content: str):
    """解析 SKILL.md 的 YAML Frontmatter，返回 dict。"""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        return {}
    return metadata

def _iter_skill_metadata():
    """迭代所有技能的元数据（包含目录名、描述等）。"""
    search_dirs = [INTERNAL_SKILLS_DIR, USER_SKILLS_DIR]
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue

        for skill_dir in os.listdir(base_dir):
            skill_path = os.path.join(base_dir, skill_dir)
            if not os.path.isdir(skill_path):
                continue

            skill_md = os.path.join(skill_path, "SKILL.md")
            if not os.path.exists(skill_md):
                continue

            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()
                metadata = _extract_frontmatter_metadata(content)
            except Exception:
                # 忽略解析错误的技能
                continue

            name = metadata.get("name", skill_dir)
            desc = metadata.get("description", "无描述")
            yield {
                "dir": skill_dir,
                "name": name,
                "description": desc
            }

def get_available_skills_list():
    """
    扫描所有可用技能并返回其名称和描述的 XML 格式字符串。
    此函数仅用于构建 System Prompt，不作为 Tool 暴露给 LLM。
    """
    skills_found = list(_iter_skill_metadata())

    if not skills_found:
        return "<available_skills>\n  <!-- 未发现本地技能 -->\n</available_skills>"

    xml_parts = ["<available_skills>"]
    for s in skills_found:
        skill_id = s["dir"]
        skill_name = s["name"]
        xml_parts.append(f'  <skill id="{skill_id}" name="{skill_name}">{s["description"]}</skill>')
    xml_parts.append("</available_skills>")

    return "\n".join(xml_parts)

def get_available_skill_ids() -> list:
    """返回所有技能的 canonical id 列表（即目录名）。"""
    return [meta["dir"] for meta in _iter_skill_metadata()]

def get_skill_suggestions(requested_name: str, limit: int = 3) -> list:
    """基于相似度返回建议的技能 id，不做自动映射。"""
    if not requested_name:
        return []
    ids = get_available_skill_ids()
    if not ids:
        return []
    return difflib.get_close_matches(requested_name, ids, n=limit, cutoff=0.5)

def get_available_skills_hint(limit: int = 5) -> str:
    """返回用于错误提示的可用技能清单（ID + 简述）。"""
    items = []
    for meta in _iter_skill_metadata():
        items.append(f'{meta["dir"]}: {meta["description"]}')
        if len(items) >= limit:
            break
    return "；".join(items)
