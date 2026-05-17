import sqlite3
import time
import io
import queue
import soundfile as sf

from .config import db_q, tui_q, sse_clients, sse_lock

def database_writer():
    db_path = "security_logs_v2.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incident_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            detected_class TEXT,
            confidence_score REAL,
            audio_data BLOB
        )
    ''')
    conn.commit()

    while True:
        item = db_q.get()
        audio_array = item['audio']
        alert = item['info']

        buf = io.BytesIO()
        sf.write(buf, audio_array, 32000, format='OGG', subtype='VORBIS')
        compressed_blob = buf.getvalue()

        cursor.execute('''
            INSERT INTO incident_logs (detected_class, confidence_score, audio_data)
            VALUES (?, ?, ?)
        ''', (alert['class_name'], alert['score'], sqlite3.Binary(compressed_blob)))
        conn.commit()

        inserted_id = cursor.lastrowid

        event_payload = {
            "id": inserted_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(alert['timestamp'])),
            "detected_class": alert['class_name'],
            "confidence_score": round(alert['score'], 2),
            "audio_url": f"/api/audio/{inserted_id}"
        }

        with sse_lock:
            for sse_queue in sse_clients:
                try:
                    sse_queue.put_nowait(event_payload)
                except queue.Full:
                    pass

        kb_size = len(compressed_blob) / 1024
        if not tui_q.full():
            tui_q.put_nowait(
                {"sys_msg": f"[bold green]Saved 30s Alert Clip to DB (ID: {inserted_id}, {kb_size:.1f} KB)[/]"})
