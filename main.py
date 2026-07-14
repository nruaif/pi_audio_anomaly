import threading
import time
import queue
from rich.live import Live

from config import tui_q, command_q, memory_info
from audio import audio_server
from classifier import classifier_loop
from database import database_writer
from web import web_server_loop
from tui import generate_layout, update_ui

def main():
    t_audio = threading.Thread(target=audio_server, daemon=True)
    t_classifier = threading.Thread(target=classifier_loop, daemon=True)
    t_db_writer = threading.Thread(target=database_writer, daemon=True)
    t_web = threading.Thread(target=web_server_loop, daemon=True)

    t_audio.start()
    t_classifier.start()
    t_db_writer.start()
    t_web.start()

    def on_press(key):
        try:
            if key.char == 'k': command_q.put({'action': 'record_next', 'duration': 15})
        except AttributeError:
            pass

    status_msg, anomaly_score, warmup, alert_history, sys_messages = "Initializing...", 0.0, True, [], [
        "System started.", "Web PWA enabled on port 8000."]
    layout = generate_layout()

    print("System initializing... Waiting for warmup to complete (approx 30s).")
    try:
        while warmup:
            while not tui_q.empty():
                try:
                    msg = tui_q.get_nowait()
                    if "status" in msg: 
                        status_msg = msg["status"]
                        print(f"\rStatus: {status_msg} | Mem: {memory_info['mem_mb']:.1f}MB", end="", flush=True)
                    if "anomaly_score" in msg: 
                        anomaly_score = msg["anomaly_score"]
                        warmup = msg.get("warmup", False)
                    if "sys_msg" in msg: 
                        sys_messages.append(msg["sys_msg"])
                except queue.Empty:
                    break
            time.sleep(0.1)

        with Live(layout, refresh_per_second=10, screen=True):
            while True:
                while not tui_q.empty():
                    try:
                        msg = tui_q.get_nowait()
                        if "status" in msg: status_msg = msg["status"]
                        if "anomaly_score" in msg: 
                            anomaly_score, warmup = msg["anomaly_score"], msg.get("warmup", False)
                        if "alert" in msg:
                            alert_history.append(msg["alert"])
                            if len(alert_history) > 100: alert_history.pop(0)
                        if "sys_msg" in msg:
                            sys_messages.append(msg["sys_msg"])
                            if len(sys_messages) > 100: sys_messages.pop(0)
                    except queue.Empty:
                        break

                update_ui(layout, status_msg, anomaly_score, warmup, alert_history, sys_messages)
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down system gracefully...")

if __name__ == '__main__':
    main()
