import sys
import os
import argparse

# [关键修复] 先添加路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from skills.knowledge_base.scripts.db_manager import DBManager

def list_knowledge(collection="documents"):
    db = DBManager.get_instance()
    stats = db.list_sources(collection)
    if not stats:
        return f"知识库 '{collection}' 为空或不存在。"
    
    output = [f"--- 知识库 '{collection}' 索引清单 ---"]
    total_chunks = 0
    for source, count in stats.items():
        output.append(f"- {source} ({count} 片段)")
        total_chunks += count
    output.append(f"\n总计: {len(stats)} 个文件, {total_chunks} 个片段。")
    return "\n".join(output)

def delete_knowledge(source_file, collection="documents"):
    db = DBManager.get_instance()
    # 简单的存在性检查（通过 list）
    stats = db.list_sources(collection)
    
    # 这里的 source_file 是归档后的绝对路径
    # 如果用户传的是文件名（如 'report.pdf'），我们可能需要模糊匹配？
    # 为了精确，我们要求用户传完整路径。或者 manage list 返回的就是完整路径。
    
    if source_file not in stats:
        # 尝试匹配文件名
        matches = [s for s in stats.keys() if os.path.basename(s) == source_file]
        if len(matches) == 1:
            source_file = matches[0] # 自动修正为完整路径
        elif len(matches) > 1:
            return f"错误: 找到多个匹配 '{source_file}' 的文件。请使用完整路径删除。"
        else:
            return f"错误: 知识库中未找到文件 '{source_file}'。"
        
    db.delete_by_source(collection, source_file)
    
    # [新增] 物理删除归档文件
    # 如果 source_file 存在于 DOCS_ARCHIVE_PATH 中，则删除
    # 注意 source_file 可能是绝对路径
    if os.path.exists(source_file) and os.path.isfile(source_file):
        try:
            os.remove(source_file)
            msg = f"✅ 已成功从知识库及归档目录删除: {os.path.basename(source_file)}"
        except Exception as e:
            msg = f"⚠️ 已从知识库删除，但物理文件删除失败: {e}"
    else:
        msg = f"✅ 已成功从知识库删除索引 (文件已不存在): {source_file}"
        
    return msg

def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Management Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # List command
    cmd_list = subparsers.add_parser("list", help="List all indexed files")
    cmd_list.add_argument("--collection", "-c", default="documents")
    
    # Delete command
    cmd_del = subparsers.add_parser("delete", help="Delete a file from index")
    cmd_del.add_argument("filename", help="Exact filename to delete (e.g., 'report.pdf')")
    cmd_del.add_argument("--collection", "-c", default="documents")
    
    args = parser.parse_args()
    
    if args.command == "list":
        print(list_knowledge(args.collection))
    elif args.command == "delete":
        print(delete_knowledge(args.filename, args.collection))

if __name__ == "__main__":
    main()
