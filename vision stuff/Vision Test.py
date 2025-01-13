import cv2
import os
import logging
import math
import torch
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk  # Import the necessary modules from PIL
from UR5E_control import *
from ultralytics import YOLO

# Suppress logging for this example
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# yolo log filter
class YoloLogFilter(logging.Filter):
    def filter(self, record):
        return not any(keyword in record.getMessage() for keyword in ['Speed:', 'per image', 'ms'])

# Suppress YOLO logging
yolo_logger = logging.getLogger("yolo_logger")
yolo_logger.addFilter(YoloLogFilter())

class CameraPosition:
    def __init__(self, use_realsense=True):
        self.detector = ObjectDetector()
        self.use_realsense = use_realsense

        self.cap = cv2.VideoCapture(0)  # Open the default webcam
        logging.info("Webcam initialized")

        self.labels = self.detector.labels
        self.currently_detected = []  # List to store currently detected items and confidence

    def stream_and_detect(self):
        root = tk.Tk()
        root.title("Camera Stream and Detections")

        # Create the camera stream window
        camera_frame = tk.Label(root)
        camera_frame.pack(side=tk.LEFT)

        def update_frame():
            ret, frame = self.cap.read()
            if ret:
                results = self.detector.detect_objects(frame.copy())
                if results is not None:
                    for result in results:
                        for box in result.boxes:
                            if box.conf > 0.8:
                                bbox = box.xyxy[0].cpu().numpy()
                                bbox = [int(coord) for coord in bbox[:4]]
                                label = self.labels[int(box.cls[0])]
                                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                                text = f'{label} ({box.conf.item():.2f})'
                                cv2.putText(frame, text, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                # Convert the frame to a format suitable for Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                camera_frame.imgtk = imgtk
                camera_frame.configure(image=imgtk)

            camera_frame.after(10, update_frame)

        update_frame()
        root.mainloop()

class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "test.pt")
        self.model = YOLO(model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, verbose=False, show=False)
        return results

if __name__ == "__main__":
    use_realsense = False  # Set to True to use RealSense, or False to use the webcam
    camera = CameraPosition(use_realsense=use_realsense)
    camera.stream_and_detect()