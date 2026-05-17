import os
import psutil
import numpy as np

_process = psutil.Process(os.getpid())

def get_memory_mb():
    return _process.memory_info().rss / 1024 / 1024

def pairwise_distances_np(A, B):
    A_sq = np.sum(A ** 2, axis=1, keepdims=True)
    B_sq = np.sum(B ** 2, axis=1)
    dists = A_sq + B_sq - 2 * np.dot(A, B.T)
    return np.sqrt(np.maximum(dists, 0))

def greedy_coreset_subsampling(features, fraction=0.2):
    num_samples = features.shape[0]
    target_size = max(1, int(num_samples * fraction))
    coreset_idx = [np.random.randint(0, num_samples)]
    min_distances = pairwise_distances_np(features, features[coreset_idx]).flatten()
    for _ in range(1, target_size):
        farthest = np.argmax(min_distances)
        coreset_idx.append(farthest)
        new_dist = pairwise_distances_np(features, features[farthest:farthest + 1]).flatten()
        min_distances = np.minimum(min_distances, new_dist)
    return features[coreset_idx]

def extract_features_onnx(chunk, onnx_session):
    audio_np = np.expand_dims(chunk, axis=0).astype(np.float32)
    input_name = onnx_session.get_inputs()[0].name
    embed = onnx_session.run(None, {input_name: audio_np})[0]
    return embed
