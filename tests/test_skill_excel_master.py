import unittest
import os
import sys
import json
import shutil
import pandas as pd
from rich.console import Console

# 动态添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入要测试的脚本模块
# 注意：因为脚本在 skills/ 目录下，可能不在 PYTHONPATH 中，我们动态加载它
from skills.excel_master.scripts.excel_ops import process_excel

console = Console()
OUTPUT_DIR = os.path.join(project_root, "output", "test_excel")

class TestExcelMaster(unittest.TestCase):
    def setUp(self):
        """准备测试数据"""
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)
        
        self.json_file = os.path.join(OUTPUT_DIR, "data.json")
        self.csv_file = os.path.join(OUTPUT_DIR, "data.csv")
        
        # 写入 JSON 数据
        data = [
            {"Name": "Alice", "Age": 30, "Score": 85},
            {"Name": "Bob",   "Age": 25, "Score": 90},
            {"Name": "Charlie","Age": 35,"Score": 88}
        ]
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
            
        # 写入 CSV 数据
        with open(self.csv_file, 'w') as f:
            f.write("Name,Age,Score\nAlice,30,85\nBob,25,90\nCharlie,35,88")

    def tearDown(self):
        """清理"""
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)

    def test_json_to_excel(self):
        """测试 JSON 转 Excel"""
        console.print("\n[cyan]🧪 Testing JSON -> Excel...[/cyan]")
        output_file = os.path.join(OUTPUT_DIR, "report_json.xlsx")
        
        # 调用核心函数
        # process_excel(input_path, output_path, title=None, calculate=None)
        try:
            process_excel(self.json_file, output_file, title="Test Report", calculate="mean")
        except SystemExit:
            self.fail("process_excel raised SystemExit unexpectedly!")
            
        # 验证文件存在
        self.assertTrue(os.path.exists(output_file))
        self.assertTrue(os.path.getsize(output_file) > 1000)
        
        # 验证内容 (读取生成的 Excel)
        df = pd.read_excel(output_file, header=1) # header=1 因为有 title 占了一行
        self.assertEqual(len(df), 3)
        self.assertEqual(df.iloc[0]['Name'], 'Alice')

    def test_csv_to_excel(self):
        """测试 CSV 转 Excel"""
        console.print("\n[cyan]🧪 Testing CSV -> Excel...[/cyan]")
        output_file = os.path.join(OUTPUT_DIR, "report_csv.xlsx")
        
        try:
            process_excel(self.csv_file, output_file)
        except SystemExit:
            self.fail("process_excel raised SystemExit unexpectedly!")
            
        self.assertTrue(os.path.exists(output_file))
        
        # 验证内容 (无 title)
        df = pd.read_excel(output_file)
        self.assertEqual(len(df), 3)
        self.assertEqual(df.iloc[1]['Name'], 'Bob')

    def test_invalid_input(self):
        """测试无效输入文件"""
        console.print("\n[cyan]🧪 Testing invalid input...[/cyan]")
        output_file = os.path.join(OUTPUT_DIR, "fail.xlsx")
        
        # 捕获 SystemExit
        with self.assertRaises(SystemExit):
            process_excel("non_existent_file.json", output_file)

if __name__ == "__main__":
    unittest.main()
