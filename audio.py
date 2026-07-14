import time
import queue
import sounddevice as sd
import numpy as np
import soundfile as sf
from collections import deque
from scipy.signal import resample_poly

from config import audio_q, command_q, db_q, tui_q

def audio_server():
    DEVICE_SAMPLE_RATE = 44100
    MODEL_SAMPLE_RATE = 32000
    CHUNK_DUR = 1.0
    DEVICE_CHUNK_SAMPLES = int(DEVICE_SAMPLE_RATE * CHUNK_DUR)

    PAST_SECONDS = 15
    FUTURE_SECONDS = 15
    cache = deque(maxlen=PAST_SECONDS)
    internal_q = queue.Queue()

    def resample_audio(audio):
        return resample_poly(audio, 320, 441).astype(np.float32)

    def audio_callback(indata, frames, time_info, status):
        chunk_44k = indata.copy().flatten().astype(np.float32)
        chunk_32k = resample_audio(chunk_44k)
        internal_q.put(chunk_32k)

    stream = sd.InputStream(
        device=0, samplerate=DEVICE_SAMPLE_RATE, channels=1,
        dtype='float32', blocksize=DEVICE_CHUNK_SAMPLES, callback=audio_callback
    )

    active_alert_recordings = []
    debug_recording = False
    debug_chunks_left = 0
    debug_buffer = []

    with stream:
        while True:
            while not internal_q.empty():
                chunk = internal_q.get()
                cache.append(chunk)

                if not audio_q.full():
                    audio_q.put_nowait(chunk)

                # Process Time-Machine alerts
                finished_alerts = []
                for rec in active_alert_recordings:
                    rec['chunks'].append(chunk)
                    rec['left'] -= 1
                    if rec['left'] <= 0:
                        finished_alerts.append(rec)

                for rec in finished_alerts:
                    active_alert_recordings.remove(rec)
                    final_audio = np.concatenate(rec['chunks'])
                    db_q.put({'audio': final_audio, 'info': rec['info']})

                # Process Debug Mic recording
                if debug_recording:
                    debug_buffer.append(chunk)
                    debug_chunks_left -= 1
                    if debug_chunks_left <= 0:
                        debug_recording = False
                        audio_data = np.concatenate(debug_buffer)
                        filename = f"debug_mic_{int(time.time())}.wav"
                        sf.write(filename, audio_data, MODEL_SAMPLE_RATE)
                        if not tui_q.full():
                            tui_q.put_nowait({"sys_msg": f"[bold blue]Debug complete! Saved to {filename}[/]"})

            # Check commands
            while not command_q.empty():
                cmd = command_q.get()

                if cmd.get('action') == 'alert_capture':
                    past_chunks = list(cache)
                    active_alert_recordings.append({
                        'chunks': past_chunks,
                        'left': FUTURE_SECONDS,
                        'info': cmd['info']
                    })
                    if not tui_q.full():
                        tui_q.put_nowait(
                            {"sys_msg": f"[blue]Anomaly detected. Capturing 15s future audio context...[/]"})

                elif cmd.get('action') == 'record_next':
                    dur = cmd.get('duration', 15)
                    debug_recording = True
                    debug_chunks_left = int(dur / CHUNK_DUR)
                    debug_buffer = []
                    if not tui_q.full():
                        tui_q.put_nowait({"sys_msg": f"[blue]Started {dur}s forward debug recording...[/]"})

            time.sleep(0.05)
