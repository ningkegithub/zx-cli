import os
import sys
import glob

# 添加项目根目录到 path 以导入 agent_core
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
sys.path.append(PROJECT_ROOT)

from agent_core.tools import read_file
from skills.knowledge_base.scripts.db_manager import DBManager

def chunk_text_by_lines(text, chunk_size=20, overlap=5):
    """
    按行切分文本，保证行号精准。
    返回: List[dict] -> [{'text': '...', 'lines': '10-30'}]
    """
    # 移除 read_file 返回的 header/footer (通过简单的 split)
    lines = text.splitlines()
    
    # 过滤掉 header (--- 文件元数据 ---) 和 footer ([SYSTEM WARNING])
    # 简单策略：找到第一个不以 --- 开头的行作为开始？
    # 或者直接相信 lines，因为 read_file 输出的内容主要是 body
    # 为了稳健，我们暂时全量切分，Agent 检索到 header 也没坏处
    
    chunks = []
    total_lines = len(lines)
    
    for i in range(0, total_lines, chunk_size - overlap):
        end = min(i + chunk_size, total_lines)
        chunk_lines = lines[i:end]
        chunk_content = "\n".join(chunk_lines).strip()
        
        if not chunk_content: continue
        
        chunks.append({
            "text": chunk_content,
            "line_start": i + 1,
            "line_end": end
        })
        
        if end == total_lines: break
        
    return chunks

def ingest_file(file_path, collection_name="documents"):
    print(f"📄 Processing: {file_path}")
    
    # 1. 调用 Core Tool 读取文件 (利用其强大的解析能力)
    # 不使用 outline_only，直接读全文 (利用新特性: end_line=-1)
    # 注意：read_file 内部有截断保护，但我们作为内部调用，希望读全量。
    # 我们需要绕过 read_file 的 500 行保护吗？
    # 是的。但 read_file 的实现是 end_line=-1 时默认截断。
    # 我们可以 loop 读取，或者修改 read_file 的逻辑。
    # 为了简单，我们先读前 2000 行。如果文件超大，Ingest 脚本应该实现分页循环。
    
    full_content = ""
    start_line = 1
    page_size = 1000 # 每次读 1000 行
    
    while True:
        # 调用 tool.invoke 或者是直接导入函数调用
        # 这里直接调用函数（因为我们在 python 脚本里）
        # 但 read_file 是 StructuredTool，需要 .invoke 或 .func
        # 简单起见，直接调用底层的 _read_docx 等？不，那样破坏了封装。
        # 我们用 read_file.func
        
        part = read_file.func(file_path, start_line=start_line, end_line=start_line + page_size)
        
        # 去除 Header/Footer 噪音
        # 这是一个 hack，但有效
        body = part
        if "--- 文件元数据 ---" in part:
            body = part.split("--- 文件元数据 ---")[1].split("\n", 4)[-1] # 跳过头几行
        if "[SYSTEM WARNING]" in body:
            body = body.split("[SYSTEM WARNING]")[0]
            
        full_content += body
        
        # 检查是否读完
        if "[SYSTEM WARNING]" not in part: 
            break
        start_line += page_size
        if start_line > 10000: # 安全熔断
            print("⚠️ File too large (>10k lines), stopping.")
            break

    # 2. 切片
    chunks = chunk_text_by_lines(full_content)
    print(f"   -> Split into {len(chunks)} chunks.")
    
    if not chunks: return

    # 3. 向量化 & 存储
    db = DBManager.get_instance()
    vectors = db.embed_documents([c['text'] for c in chunks])
    
    data = []
    for i, chunk in enumerate(chunks):
        data.append({
            "vector": vectors[i],
            "text": chunk['text'],
            "source": os.path.basename(file_path),
            "line_range": f"{chunk['line_start']}-{chunk['line_end']}",
            "type": "document"
        })
        
    # 4. 写入 DB
    tbl = db.get_table(collection_name)
    if tbl:
        tbl.add(data)
    else:
        db.create_table(collection_name, data)
        
    print(f"✅ Ingested {len(data)} vectors to '{collection_name}'.")

def main(input_path, collection="documents"):
    if os.path.isfile(input_path):
        ingest_file(input_path, collection)
    elif os.path.isdir(input_path):
        # 递归查找支持的格式
        exts = ['*.docx', '*.pdf', '*.xlsx', '*.pptx', '*.md', '*.txt']
        files = []
        for ext in exts:
            files.extend(glob.glob(os.path.join(input_path, '**', ext), recursive=True))
            
        print(f"🔍 Found {len(files)} files in {input_path}")
        for f in files:
            try:
                ingest_file(f, collection)
            except Exception as e:
                print(f"❌ Error processing {f}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <file_or_dir> [collection_name]")
        sys.exit(1)
    
    target = sys.argv[1]
    coll = sys.argv[2] if len(sys.argv) > 2 else "documents"
    main(target, coll)
