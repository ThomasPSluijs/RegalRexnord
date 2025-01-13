import cv2
import pyrealsense2 as rs
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
        self.pipeline = None

        if use_realsense:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            self.pipeline.start(self.config)
            self.align = rs.align(rs.stream.color)
            logging.info("RealSense Camera initialized")
        else:
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

        # Create the table for detections
        columns = ('Label', 'Confidence')
        table = ttk.Treeview(root, columns=columns, show='headings')
        table.heading('Label', text='Label')
        table.heading('Confidence', text='Confidence')
        table.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        cv2.namedWindow("Camera Stream", cv2.WINDOW_AUTOSIZE)

        try:
            while True:
                if self.use_realsense:
                    frames = self.pipeline.wait_for_frames()
                    aligned_frames = self.align.process(frames)
                    color_frame = aligned_frames.get_color_frame()
                    depth_frame = aligned_frames.get_depth_frame()

                    if not color_frame or not depth_frame:
                        continue

                    frame = np.asanyarray(color_frame.get_data())
                else:
                    ret, frame = self.cap.read()  # Capture frame from webcam
                    if not ret:
                        continue
                    
                results = self.detector.detect_objects(frame.copy())
                self.currently_detected.clear()  # Clear previous detections
                
                if results is not None:
                    for result in results:
                        for box in result.boxes:
                            if box.conf > 0.8:
                                bbox = box.xyxy[0].cpu().numpy()
                                bbox = [int(coord) for coord in bbox[:4]]

                                # Draw box around detected part
                                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)

                                # Put label (item_type) and confidence on the screen
                                label = self.labels[int(box.cls[0])]
                                confidence = box.conf.item()
                                self.currently_detected.append((label, confidence))
                                text = f'{label} ({confidence:.2f})'
                                cv2.putText(frame, text, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
                # Convert the frame to an image for tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)  # Use PIL's Image.fromarray
                img = img.resize((640, 480))
                imgtk = ImageTk.PhotoImage(image=img)
                camera_frame.config(image=imgtk)
                camera_frame.image = imgtk  # Hold a reference

                # Update the table with the current detections
                for item in table.get_children():
                    table.delete(item)
                for label, confidence in self.currently_detected:
                    table.insert('', tk.END, values=(label, f'{confidence:.2f}'))

                root.update_idletasks()
                root.update()

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            if self.use_realsense:
                self.pipeline.stop()
            else:
                self.cap.release()
            cv2.destroyAllWindows()

class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "test.pt")  # Changed to test.pt
        self.model = YOLO(model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = YOLO(model_path)
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, verbose=False, show=False)
        return results

if __name__ == "__main__":
    use_realsense = False  # Set to True to use RealSense, or False to use the webcam
    camera = CameraPosition(use_realsense=use_realsense)
    camera.stream_and_detect()
