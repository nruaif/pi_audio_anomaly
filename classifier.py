import os
import time
import gc
import numpy as np
import onnxruntime as ort
from config import audio_q, command_q, tui_q, memory_info
from utils import get_memory_mb, pairwise_distances_np, extract_features_onnx  # coreset import removed

def classifier_loop():
    onnx_path = os.path.join(os.path.dirname(__file__), 'mn10_scene_embed.onnx')
    if not os.path.exists(onnx_path):
        tui_q.put({"sys_msg": f"[bold red]ONNX model {onnx_path} not found![/]"})
        return
    tui_q.put({"status": f"Loading ONNX model {os.path.basename(onnx_path)}..."})
    try:
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        onnx_session = ort.InferenceSession(onnx_path, opts)
        tui_q.put({"sys_msg": f"[bold green]Successfully loaded ONNX model[/]"})
    except Exception as e:
        tui_q.put({"sys_msg": f"[bold red]ONNX load failed: {e}[/]"})
        return

    COOLDOWN_SEC = 30
    last_alert_time = 0
    WARMUP_CHUNKS = 30
    history_embeddings = []
    memory_bank = None
    baseline_mean = 0.0
    baseline_std = 1.0
    is_warming_up = True

    while not audio_q.empty():
        try:
            audio_q.get_nowait()
        except:
            break

    while True:
        chunk = audio_q.get()
        memory_info["mem_mb"] = get_memory_mb()
        embed = extract_features_onnx(chunk, onnx_session)
        embed_flat = embed.flatten()
        score = 0.0

        if is_warming_up:
            history_embeddings.append(embed_flat)
            if not tui_q.full():
                tui_q.put_nowait({"anomaly_score": 0.0, "warmup": True,
                                  "status": f"Building Memory Bank ({len(history_embeddings)}/{WARMUP_CHUNKS})"})
            if len(history_embeddings) >= WARMUP_CHUNKS:
                memory_bank = np.array(history_embeddings, dtype=np.float32)

                # Calibrate baseline using bank-vs-bank NN distances (self excluded)
                dists = pairwise_distances_np(memory_bank, memory_bank)
                np.fill_diagonal(dists, np.inf)
                min_dists = np.min(dists, axis=1)
                baseline_mean = float(np.mean(min_dists))
                baseline_std = float(np.std(min_dists)) + 1e-6

                is_warming_up = False
                del history_embeddings
                gc.collect()
                tui_q.put_nowait({"status": "Monitoring Anomaly Score..."})
        else:
            query = np.expand_dims(embed_flat, axis=0)
            dists = pairwise_distances_np(query, memory_bank)
            min_dist = np.min(dists, axis=1)[0]
            score_normalized = (min_dist - baseline_mean) / baseline_std
            score = max(0.0, float(score_normalized))
            if not tui_q.full():
                tui_q.put_nowait({"anomaly_score": score, "warmup": False, "status": "Monitoring..."})

            ALERT_THRESHOLD = 3.0
            now = time.time()
            if score >= ALERT_THRESHOLD and (now - last_alert_time > COOLDOWN_SEC):
                alert_data = {'class_name': "Anomaly Detected", 'score': score, 'timestamp': now}
                command_q.put({'action': 'alert_capture', 'info': alert_data})
                if not tui_q.full():
                    tui_q.put_nowait({"alert": alert_data})
                last_alert_time = now