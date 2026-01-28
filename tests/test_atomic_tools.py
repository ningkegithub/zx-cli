import sys
import os
import shutil

# 动态添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core.tools import read_file, write_file

TEST_DIR = os.path.join(project_root, "tests", "temp_atomic_test")
TEST_FILE = os.path.join(TEST_DIR, "test_doc.txt")

def setup():
    """准备测试环境"""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

def teardown():
    """清理测试环境"""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_write_and_read():
    print("🧪 测试原子工具: write_file 和 read_file")
    
    # 1. 测试写入（包含自动创建父目录）
    content_to_write = "Hello, Agent!\nThis is a test file."
    print(f"   📝 尝试写入文件: {TEST_FILE}")
    result_write = write_file.invoke({"file_path": TEST_FILE, "content": content_to_write})
    
    if "成功写入" in result_write:
        print("   ✅ 写入成功")
    else:
        print(f"   ❌ 写入失败: {result_write}")
        sys.exit(1)

    # 验证文件物理存在
    if not os.path.exists(TEST_FILE):
        print("   ❌ 文件未在磁盘上创建！")
        sys.exit(1)

    # 2. 测试读取
    print(f"   📖 尝试读取文件: {TEST_FILE}")
    result_read = read_file.invoke({"file_path": TEST_FILE})
    
    if result_read == content_to_write:
        print("   ✅ 读取内容匹配")
    else:
        print(f"   ❌ 读取内容不匹配.\n期望:\n{content_to_write}\n实际:\n{result_read}")
        sys.exit(1)

    # 3. 测试读取不存在的文件
    print("   🔍 测试读取不存在的文件...")
    result_missing = read_file.invoke({"file_path": "non_existent_file.xyz"})
    if "错误" in result_missing or "Error" in result_missing:
        print("   ✅ 正确处理了缺失文件")
    else:
        print(f"   ❌ 未报错: {result_missing}")
        sys.exit(1)

    print("🎉 原子工具测试通过！")

if __name__ == "__main__":
    try:
        setup()
        test_write_and_read()
    finally:
        teardown()
