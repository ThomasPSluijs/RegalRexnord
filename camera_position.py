import cv2
import pyrealsense2 as rs
import os
import logging
import math
import torch
import numpy as np
from UR5E_control import *
from ultralytics import YOLO
import threading
import time

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
    def __init__(self, robot):
        self.detector = ObjectDetector()
        self.robot = robot
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(self.config)
        self.align = rs.align(rs.stream.color)
        self.labels = self.detector.labels

        self.last_frame = None
        self.frame_lock = threading.Lock()
        self.display_thread_running = True
        self.previous_coordinates = None
        self.last_stable_time = 0

        # Define row positions (adjust as necessary for your setup)
        self.row1_y = 150  # Example y-coordinate for the first row
        self.row2_y = 300  # Example y-coordinate for the second row
        self.row_threshold = 6  # Stability threshold in pixels

    # moves robot to capture position
    def capture_position(self, slow=False):
        pickup_tcp = [-47.5 / 1000, -140 / 1000, 135 / 1000, math.radians(0), math.radians(0), math.radians(0)]
        self.robot.set_tcp(pickup_tcp)

        target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
        if slow:
            logging.info("check part type, move to camera position")
            self.robot.move_l(target_position, 0.3, 0.3)
        else:
            self.robot.move_l(target_position, 3, 3)

    # transform camera coordinates to real world (robot) coordinates
    def transform_coordinates(self, xp, yp, zp):
        a, b, c = -0.0010677615453140213, 3.094561948991097e-05, -0.17959680557618776
        d, e, f = 2.482562688915765e-05, 0.0010493343791252749, -0.2507558317896495

        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f

        return xd, yd

    # main function that detects objects and returns the object locations
    def detect_object_without_start(self, min_length=170, slow=False):
        self.capture_position(slow)
        time.sleep(1)
        not_found = True
        logging.info("start capturing frames")
        while not_found:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            frame = np.asanyarray(color_frame.get_data())
            with self.frame_lock:  # Update last_frame safely
                self.last_frame = frame
            results = self.detector.detect_objects(frame.copy())

            if results is not None:
                for result in results:
                    for box in result.boxes:
                        if box.conf > 0.8:
                            bbox = box.xyxy[0].cpu().numpy()
                            bbox = [int(coord) for coord in bbox[:4]]
                            x_left = bbox[0]
                            y_middle = int((bbox[1] + bbox[3]) / 2)
                            width = bbox[2] - bbox[0]
                            height = bbox[3] - bbox[1]
                            depth = depth_frame.get_distance(x_left, y_middle)
                            label = self.labels[int(box.cls[0])]
                            length = max(width, height)

                            if label in ['Big-Blue', 'Green', 'Holed', 'Rubber', 'Small-Blue'] and length >= min_length and width * height < 75000:
                                current_coordinates = (x_left, y_middle)
                                if self.is_stable(current_coordinates):
                                    logging.info("stable")
                                    xd, yd = self.transform_coordinates(x_left, y_middle, depth)
                                    logging.info(f"Detected (x, y, z): ({x_left}, {y_middle}, {depth}) conf: {box.conf}")

                                    # Draw box and label on the frame
                                    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                                    cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)
                                    text = f'X: {x_left}, Y: {y_middle}, Z: {depth:.2f}m'
                                    cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                    text = f'{label} ({box.conf.item():.2f})'
                                    cv2.putText(frame, text, (bbox[0], bbox[1] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                                    not_found = False

                                    with self.frame_lock:  # Update last_frame safely
                                        self.last_frame = frame
                                    return (xd, yd, label)
                                else:
                                    logging.info("not stable")

        return (0, 0, 0)

    def is_stable(self, current_coordinates):
        if self.previous_coordinates is None:
            self.previous_coordinates = current_coordinates
            self.last_stable_time = time.time()
            return False

        x_left, y_middle = current_coordinates

        # Determine the closest row
        row1_distance = abs(y_middle - self.row1_y)
        row2_distance = abs(y_middle - self.row2_y)

        if row1_distance < row2_distance:
            normalized_coordinates = (x_left, self.row1_y)
        else:
            normalized_coordinates = (x_left, self.row2_y)

        # Calculate distance from the last stable position
        distance = np.linalg.norm(np.array(normalized_coordinates) - np.array(self.previous_coordinates))
        if distance > self.row_threshold:
            self.previous_coordinates = normalized_coordinates
            self.last_stable_time = time.time()
            return False

        if time.time() - self.last_stable_time >= 0.3:
            return True

        return False

    def stop_display_thread(self):
        self.display_thread_running = False

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


