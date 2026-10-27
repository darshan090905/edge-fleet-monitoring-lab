import os
import sys
import time
import cv2
import numpy as np
from prometheus_client import start_http_server, Gauge, Counter, Histogram

# Configuration from Environment
RTSP_URL = os.getenv("RTSP_URL", "rtsp://cam:8554/cam")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8005"))
TARGET_FPS = float(os.getenv("TARGET_FPS", "1.5"))
FRAME_INTERVAL = 1.0 / TARGET_FPS

# Prometheus Telemetry Definitions
PEOPLE_COUNT = Gauge(
    "people_count",
    "Current number of people detected in the surveillance stream"
)
FRAMES_PROCESSED_TOTAL = Counter(
    "frames_processed_total",
    "Total video frames analyzed by the AI detector"
)
INFERENCE_LATENCY = Gauge(
    "inference_latency_seconds",
    "Time taken to run person detection on the last frame in seconds"
)
STREAM_CONNECTED = Gauge(
    "stream_connected",
    "Status of connection to the RTSP camera stream (1 = connected, 0 = disconnected)"
)

# Initialize starting values
PEOPLE_COUNT.set(0)
STREAM_CONNECTED.set(0)
INFERENCE_LATENCY.set(0.0)

def init_detector():
    """Initializes OpenCV's built-in HOG People Detector."""
    print("[AI DETECTOR] Loading OpenCV HOG Person Detector model...", flush=True)
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return hog

def main():
    print(f"[AI DETECTOR] Starting Edge AI Telemetry Service on port {METRICS_PORT}...", flush=True)
    start_http_server(METRICS_PORT)
    print(f"[AI DETECTOR] Prometheus metrics live at http://0.0.0.0:{METRICS_PORT}/metrics", flush=True)

    hog = init_detector()

    while True:
        print(f"[AI DETECTOR] Connecting to RTSP video stream: {RTSP_URL}...", flush=True)
        cap = cv2.VideoCapture(RTSP_URL)

        if not cap.isOpened():
            STREAM_CONNECTED.set(0)
            print("[AI DETECTOR WARNING] Failed to connect to RTSP stream. Retrying in 5 seconds...", flush=True)
            time.sleep(5)
            continue

        STREAM_CONNECTED.set(1)
        print("[AI DETECTOR SUCCESS] Connected to RTSP stream. Processing frames...", flush=True)

        last_processed_time = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[AI DETECTOR WARNING] Stream connection dropped or frame empty.", flush=True)
                STREAM_CONNECTED.set(0)
                break

            current_time = time.time()
            # Throttle to 1-2 FPS to maintain low edge CPU usage
            if (current_time - last_processed_time) < FRAME_INTERVAL:
                continue

            last_processed_time = current_time

            # Resize frame to standard 640px width for fast edge inference
            height, width = frame.shape[:2]
            target_width = 640
            scale = target_width / float(width)
            resized = cv2.resize(frame, (target_width, int(height * scale)), interpolation=cv2.INTER_AREA)

            # Run inference and measure latency
            start_infer = time.time()
            # detectMultiScale with standard parameters
            boxes, weights = hog.detectMultiScale(
                resized,
                winStride=(8, 8),
                padding=(4, 4),
                scale=1.05
            )
            duration = time.time() - start_infer

            # Update Prometheus metrics
            detected_count = len(boxes)
            PEOPLE_COUNT.set(detected_count)
            FRAMES_PROCESSED_TOTAL.inc()
            INFERENCE_LATENCY.set(duration)

            # Privacy Guarantee: No frames are written to disk. Only metrics are recorded.
            if FRAMES_PROCESSED_TOTAL._value.get() % 10 == 0:
                print(f"[AI TELEMETRY] Frames: {int(FRAMES_PROCESSED_TOTAL._value.get())} | People Count: {detected_count} | Latency: {duration*1000:.1f}ms", flush=True)

        cap.release()
        STREAM_CONNECTED.set(0)
        print("[AI DETECTOR] Reconnecting to camera stream in 3 seconds...", flush=True)
        time.sleep(3)

if __name__ == "__main__":
    main()
