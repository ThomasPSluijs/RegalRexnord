import os
import cv2
import torch
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO
from collections import deque

class CameraPosition:
    def __init__(self, use_realsense=True):
        self.use_realsense = use_realsense
        self.detector = ObjectDetector()
        self.tracked_objects = deque(maxlen=60)  # Keep track of objects over the last 10 frames

        if use_realsense:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            self.pipeline.start(self.config)
            self.align = rs.align(rs.stream.color)
            print("RealSense Camera initialized")
        else:
            self.cap = cv2.VideoCapture(0)  # Open the default webcam
            print("Webcam initialized")

        self.labels = self.detector.labels

    def stream_and_detect(self):
        cv2.namedWindow("Camera Stream", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera Stream", 1280, 720)  # Resize the window to be larger

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
                
                if results is not None:
                    seen_objects = []
                    for result in results:
                        for box in result.boxes:
                            bbox = box.xyxy[0].cpu().numpy()
                            bbox = [int(coord) for coord in bbox[:4]]
                            label = self.labels[int(box.cls[0])]
                            confidence = box.conf.item()

                            # Draw bounding box
                            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                            text = f'{label} ({confidence:.2f})'
                            cv2.putText(frame, text, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                            seen_objects.append((label, confidence))

                    self.tracked_objects.append(seen_objects)
                    stable_objects = self.get_stable_objects()

                    frame = self.display_table(frame, stable_objects)

                # Display the frame
                cv2.imshow('Camera Stream', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            if self.use_realsense:
                self.pipeline.stop()
            else:
                self.cap.release()
            cv2.destroyAllWindows()

    def get_stable_objects(self):
        # Aggregate detections over the last few frames
        object_counts = {}
        for objects in self.tracked_objects:
            for label, confidence in objects:
                if label not in object_counts:
                    object_counts[label] = []
                object_counts[label].append(confidence)

        stable_objects = []
        for label, confidences in object_counts.items():
            avg_confidence = sum(confidences) / len(confidences)
            stable_objects.append((label, avg_confidence))

        return stable_objects

    def display_table(self, frame, seen_objects):
        table_width = 200
        table_start_x = frame.shape[1]
        table_start_y = 50
        row_height = 20

        # Create a white background for the table
        table_frame = np.ones((frame.shape[0], table_width, 3), dtype=np.uint8) * 255

        # Draw table header
        cv2.putText(table_frame, "Objects", (10, table_start_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        # Draw table rows
        for i, (label, confidence) in enumerate(seen_objects):
            text = f'{label}: {confidence:.2f}'
            cv2.putText(table_frame, text, (10, table_start_y + 15 + row_height * (i + 1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        # Concatenate the original frame with the table frame
        combined_frame = np.hstack((frame, table_frame))

        return combined_frame

class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "best.pt")
        self.model = YOLO(model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, verbose=False, show=False)
        return results

if __name__ == "__main__":
    use_realsense = True  # Set to True to use RealSense, or False to use the webcam
    camera = CameraPosition(use_realsense=use_realsense)
    camera.stream_and_detect()