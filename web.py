import json
import urllib.parse
import queue
import sqlite3
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from config import sse_clients, sse_lock, tui_q
from html_assets import HTML_CONTENT, MANIFEST_CONTENT, SW_CONTENT, ICON_SVG

class LightweightAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)

        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
            return

        if parsed_path.path == '/manifest.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(MANIFEST_CONTENT.encode('utf-8'))
            return

        if parsed_path.path == '/sw.js':
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(SW_CONTENT.encode('utf-8'))
            return

        if parsed_path.path == '/icon.svg':
            self.send_response(200)
            self.send_header('Content-type', 'image/svg+xml')
            self.end_headers()
            self.wfile.write(ICON_SVG.encode('utf-8'))
            return

        if parsed_path.path == '/api/stream':
            self.send_response(200)
            self.send_header('Content-type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            client_q = queue.Queue(maxsize=100)
            with sse_lock:
                sse_clients.add(client_q)
            try:
                while True:
                    try:
                        alert_data = client_q.get(timeout=10)
                        self.wfile.write(f"data: {json.dumps(alert_data)}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except Exception:
                pass
            finally:
                with sse_lock:
                    sse_clients.discard(client_q)
            return

        if parsed_path.path == '/api/logs':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                conn = sqlite3.connect("security_logs_v2.db")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, timestamp, detected_class, confidence_score FROM incident_logs ORDER BY timestamp DESC LIMIT 50")
                rows = cursor.fetchall()
                conn.close()

                logs = [{"id": r[0], "timestamp": r[1], "detected_class": r[2], "confidence_score": r[3],
                         "audio_url": f"/api/audio/{r[0]}"} for r in rows]
                self.wfile.write(json.dumps({"status": "success", "logs": logs}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        if parsed_path.path.startswith('/api/audio/'):
            log_id = os.path.basename(parsed_path.path)
            conn = sqlite3.connect("security_logs_v2.db")
            cursor = conn.cursor()
            cursor.execute("SELECT audio_data FROM incident_logs WHERE id=?", (log_id,))
            row = cursor.fetchone()
            conn.close()

            if row and row[0]:
                self.send_response(200)
                self.send_header('Content-type', 'audio/ogg')
                self.send_header('Content-Length', str(len(row[0])))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                self.wfile.write(row[0])
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'{"error": "Audio file not found in Database"}')
            return

        self.send_response(404)
        self.end_headers()

def web_server_loop():
    port = 8000
    httpd = ThreadingHTTPServer(('', port), LightweightAPIHandler)
    tui_q.put({"sys_msg": f"[bold magenta]PWA & API Server running on http://127.0.0.1:{port}[/]"})
    httpd.serve_forever()
