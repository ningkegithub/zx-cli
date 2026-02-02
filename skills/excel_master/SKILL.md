---
name: excel_master
description: 专业的 Excel 自动化工具，支持数据处理、报表生成及高级样式设置。
---

# Excel 自动化大师 (Excel Master)

此技能负责处理复杂的 Excel 操作，包括从数据源生成报表、执行自动化计算及应用企业级样式。

## 🌟 核心功能
- **报表生成**：支持将 JSON、CSV 或文本表格快速转换为 Excel 文件。
- **数据分析**：内置常用的统计计算（总和、平均值、同比环比等）。
- **样式定制**：支持设置表头颜色、单元格边框、数值格式（百分比、货币等）。
- **多表集成**：支持在一个工作簿中创建和管理多个工作表 (Sheet)。

## 🚀 使用方法

### 基础数据转换
将 JSON 数据文件转换为 Excel 报表：
```bash
python3 {SKILL_DIR}/scripts/excel_ops.py --input data.json --output report.xlsx
```

### 高级报表（带样式和计算）
```bash
python3 {SKILL_DIR}/scripts/excel_ops.py --input data.csv --output analysis.xlsx --title "2024年度门店销售分析" --calculate "Total,Average"
```

## 📝 输入格式建议
- **JSON**: 应为对象列表，如 `[{"日期": "2024-01-01", "销量": 100}, ...]`
- **CSV**: 标准逗号分隔符文件。
