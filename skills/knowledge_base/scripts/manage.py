import sys
import os
import argparse

# 添加项目根目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
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
    if source_file not in stats:
        return f"错误: 知识库中未找到文件 '{source_file}'。"
        
    db.delete_by_source(collection, source_file)
    return f"✅ 已成功从知识库删除: {source_file}"

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
