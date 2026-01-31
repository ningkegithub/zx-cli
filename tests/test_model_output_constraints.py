import sys
import os

# 动态添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_core.nodes import _ensure_tool_call_thought_prefix

def assert_equal(actual, expected, label):
    if actual != expected:
        print(f"❌ 失败: {label}\n期望: {expected!r}\n实际: {actual!r}")
        sys.exit(1)

def test_tool_call_prefix_empty():
    text = ""
    # 新逻辑：空内容补全一句话，无表情
    expected = "正在分析任务并调用相关工具..."
    assert_equal(_ensure_tool_call_thought_prefix(text), expected, "空内容补全")

def test_tool_call_prefix():
    text = "需要查天气"
    # 新逻辑：有内容则保持原样，不强加前缀
    expected = "需要查天气"
    assert_equal(_ensure_tool_call_thought_prefix(text), expected, "保持已有思考")

def test_tool_call_prefix_keep_answer():
    text = "先查天气。\n最终回答：北京今天+1°C。"
    # 保持原样
    expected = "先查天气。\n最终回答：北京今天+1°C。"
    assert_equal(_ensure_tool_call_thought_prefix(text), expected, "保留回答内容")

if __name__ == "__main__":
    test_tool_call_prefix_empty()
    test_tool_call_prefix()
    test_tool_call_prefix_keep_answer()
    print("✅ 模型输出约束测试通过！")
