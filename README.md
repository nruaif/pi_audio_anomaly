# Pi Audio Anomaly

mn10 Audio Anomaly Detection System featuring a Rich TUI and an integrated PWA Dashboard.

## Features
- **Real-Time Inference:** Continuous audio anomaly detection using the `mn10_scene_embed` ONNX model.
- **Time-Machine Recording:** Automatically captures 15 seconds of past audio and 15 seconds of future audio when an anomaly is detected.
- **SQLite BLOB Storage:** Stores 30-second evidence clips fully compressed (OGG Vorbis) directly into a lightweight SQLite (WAL) database.
- **Rich TUI:** A responsive Terminal User Interface for live monitoring of anomaly scores and system memory.
- **PWA Dashboard:** A built-in web server (port 8000) providing a Progressive Web App with Server-Sent Events (SSE) for real-time browser alerts and audio playback.
- **Coreset Subsampling:** Automatically builds a memory bank baseline during the first 30 seconds of execution.

## Requirements
- Python 3.8+
- Active microphone/audio input device

## Installation
Install the necessary Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the System
You can start the server using the provided bash script:
```bash
bash run.sh
```
Or run the python module directly:
```bash
python main.py
```

*Note: The system requires approximately 30 seconds to warm up and build the baseline memory bank. You can press `k` in the terminal to trigger a 15-second manual debug recording.*
