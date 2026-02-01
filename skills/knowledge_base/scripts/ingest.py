import os
import sys
import glob
import shutil
import hashlib

# [关键修复] 先计算并添加项目根目录，再进行后续 import
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# 现在可以安全地导入了
from skills.knowledge_base.scripts.db_manager import DBManager, DOCS_ARCHIVE_PATH
from agent_core.tools import read_file

def chunk_text_by_lines(text, chunk_size=20, overlap=5):
    """
    按行切分文本，并尝试提取语义化的位置信息（如 Slide 1, Page 2, Sheet Name）。
    返回: List[dict] -> [{'text': '...', 'lines': '10-30', 'location': 'Slide 5'}]
    """
    lines = text.splitlines()
    chunks = []
    total_lines = len(lines)
    
    # 预扫描：建立行号到位置的映射
    line_location_map = {}
    current_location = "Unknown Location"
    
    import re
    # 匹配模式: --- Slide 1 ---, --- Page 1 ---, --- Sheet: Sheet1 ---
    loc_pattern = re.compile(r'^--- (Slide \d+|Page \d+|Sheet: .+) ---$')
    
    for i, line in enumerate(lines):
        match = loc_pattern.match(line.strip())
        if match:
            current_location = match.group(1)
        line_location_map[i] = current_location
    
    for i in range(0, total_lines, chunk_size - overlap):
        end = min(i + chunk_size, total_lines)
        chunk_lines = lines[i:end]
        chunk_content = "\n".join(chunk_lines).strip()
        
        if not chunk_content: continue
        
        start_loc = line_location_map.get(i, "Unknown")
        end_loc = line_location_map.get(end-1, "Unknown")
        
        if start_loc == end_loc:
            location = start_loc
        else:
            location = f"{start_loc} -> {end_loc}"
            
        chunks.append({
            "text": chunk_content,
            "line_start": i + 1,
            "line_end": end,
            "location": location
        })
        
        if end == total_lines: break
        
    return chunks

def archive_file(file_path):
    """将文件归档到影子目录，返回归档后的绝对路径"""
    try:
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        
        filename = os.path.basename(file_path)
        new_filename = f"{file_hash}_{filename}"
        new_path = os.path.join(DOCS_ARCHIVE_PATH, new_filename)
        
        if not os.path.exists(new_path):
            shutil.copy2(file_path, new_path)
            print(f"📦 Archived to: {new_path}")
        else:
            print(f"📦 Used existing archive: {new_path}")
            
        return new_path
    except Exception as e:
        print(f"⚠️ Archive failed: {e}. Using original path.")
        return file_path

def ingest_file(file_path, collection_name="documents"):
    # 1. 归档 (Copy-on-Ingest)
    target_path = archive_file(file_path)
    print(f"📄 Processing: {target_path}")
    
    # 2. 调用 Core Tool 读取文件 (使用归档后的路径)
    full_content = ""
    start_line = 1
    page_size = 1000 
    
    while True:
        # 使用 read_file.func 直接调用
        part = read_file.func(target_path, start_line=start_line, end_line=start_line + page_size)
        
        body = part
        if "--- 文件元数据 ---" in part:
            body = part.split("--- 文件元数据 ---")[1].split("\n", 4)[-1]
        if "[SYSTEM WARNING]" in body:
            body = body.split("[SYSTEM WARNING]")[0]
            
        full_content += body
        
        if "[SYSTEM WARNING]" not in part: 
            break
        start_line += page_size
        if start_line > 10000:
            print("⚠️ File too large (>10k lines), stopping.")
            break

    # 3. 切片
    chunks = chunk_text_by_lines(full_content)
    print(f"   -> Split into {len(chunks)} chunks.")
    
    if not chunks: return

    # 4. 向量化 & 存储
    db = DBManager.get_instance()
    vectors = db.embed_documents([c['text'] for c in chunks])
    
    # 使用归档路径作为 Source
    final_source = target_path

    data = []
    for i, chunk in enumerate(chunks):
        data.append({
            "vector": vectors[i],
            "text": chunk['text'],
            "source": final_source, 
            "line_range": f"{chunk['line_start']}-{chunk['line_end']}",
            "location": chunk['location'], 
            "type": "document"
        })
        
    # 5. 写入 DB
    is_compatible = db.check_schema_compatibility(collection_name, data[0])
    
    tbl = db.get_table(collection_name)
    if tbl and is_compatible:
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