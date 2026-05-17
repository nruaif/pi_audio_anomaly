import queue
import threading

# Global queues
audio_q = queue.Queue(maxsize=15)
command_q = queue.Queue(maxsize=10)
db_q = queue.Queue(maxsize=10)
tui_q = queue.Queue(maxsize=20)

# SSE connected clients for real-time web notifications
sse_clients = set()
sse_lock = threading.Lock()

# Global memory info
memory_info = {"mem_mb": 0.0}
