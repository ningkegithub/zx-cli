import queue
from agent_core import build_graph

def run_worker(app, inputs, output_queue, stop_event):
    """
    后台工作线程：负责执行 Agent 逻辑并将结果推送到队列。
    统一输出格式: (msg_type, mode, data)
    """
    try:
        # 使用双模式：messages 用于 UI 流式，updates 用于状态同步
        for mode, data in app.stream(inputs, stream_mode=["messages", "updates"]):
            if stop_event.is_set():
                break
            output_queue.put(("stream", mode, data))
    except Exception as e:
        output_queue.put(("error", None, e))
    finally:
        output_queue.put(("done", None, None))
