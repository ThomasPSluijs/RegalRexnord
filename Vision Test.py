import cv2
import pyrealsense2 as rs
import os
import logging
import math
import torch
import numpy as np
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

# uses camera to run yolo model and get x, y, and z coordinates of the parts
class CameraPosition:
    def __init__(self):
        self.detector = ObjectDetector()
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(self.config)
        self.align = rs.align(rs.stream.color)
        self.labels = self.detector.labels

    # main function that streams the camera feed and detects objects
    def stream_and_detect(self):
        cv2.namedWindow("RealSense Camera Stream", cv2.WINDOW_AUTOSIZE) 
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                aligned_frames = self.align.process(frames)
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()

                if not color_frame or not depth_frame:
                    continue

                frame = np.asanyarray(color_frame.get_data())
                results = self.detector.detect_objects(frame.copy())
                
                if results is not None:
                    for result in results:
                        for box in result.boxes:
                            if box.conf > 0.8:
                                bbox = box.xyxy[0].cpu().numpy()
                                bbox = [int(coord) for coord in bbox[:4]]
                                x_left = bbox[0]
                                y_middle = int((bbox[1] + bbox[3]) / 2)

                                # Draw box around detected part and draw circle at pickup point
                                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                                cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)

                                # Put label (item_type) and confidence on the screen
                                label = self.labels[int(box.cls[0])]
                                confidence = box.conf.item()
                                text = f'{label} ({confidence:.2f})'
                                cv2.putText(frame, text, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # Display the frame
                cv2.imshow('RealSense Camera Stream', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            self.pipeline.stop()
            cv2.destroyAllWindows()

# runs yolo model and detects objects
class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "best.pt")
        self.model = YOLO(model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = YOLO(model_path)
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, verbose=False, show=False)
        return results

if __name__ == "__main__":
    camera = CameraPosition()
    camera.stream_and_detect()
