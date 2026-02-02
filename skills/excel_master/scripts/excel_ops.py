import argparse
import pandas as pd
import json
import os
import sys

def process_excel(input_path, output_path, title=None, calculate=None):
    """处理输入数据并生成带样式的 Excel 文件"""
    
    # 1. 加载数据
    ext = os.path.splitext(input_path)[1].lower()
    try:
        if ext == '.json':
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif ext == '.csv':
            df = pd.read_csv(input_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(input_path)
        else:
            # 尝试作为文本表格读取
            df = pd.read_table(input_path, sep=None, engine='python')
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        sys.exit(1)

    # 2. 基础计算 (可选)
    if calculate:
        calc_types = [c.strip().lower() for c in calculate.split(',')]
        # 这里可以根据需求增加更复杂的逻辑，目前仅作为示例输出信息
        print(f"ℹ️ 正在执行计算: {', '.join(calc_types)}")

    # 3. 写入 Excel 并应用样式
    try:
        # 确保输出目录规范 (强制使用 output/ 目录，除非已包含)
        if not output_path.startswith('output/') and not os.path.isabs(output_path):
            output_path = os.path.join('output', output_path)
            os.makedirs('output', exist_ok=True)

        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1 if title else 0)
        
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']

        # 定义样式
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })

        # 应用标题
        if title:
            worksheet.merge_range(0, 0, 0, len(df.columns) - 1, title, title_format)

        # 应用表头样式
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(1 if title else 0, col_num, value, header_format)
            # 自动调整列宽
            column_len = max(df[value].astype(str).map(len).max(), len(value)) + 2
            worksheet.set_column(col_num, col_num, column_len)

        writer.close()
        print(f"🎉 成功生成报表: {output_path}")
    except Exception as e:
        print(f"❌ Excel 生成失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Excel Automation Master Script")
    parser.add_argument("--input", required=True, help="输入数据文件路径 (JSON/CSV/Excel)")
    parser.add_argument("--output", required=True, help="输出 Excel 文件路径")
    parser.add_argument("--title", help="报表大标题")
    parser.add_argument("--calculate", help="执行的计算类型 (例如: sum, mean)")
    
    args = parser.parse_args()
    process_excel(args.input, args.output, args.title, args.calculate)
