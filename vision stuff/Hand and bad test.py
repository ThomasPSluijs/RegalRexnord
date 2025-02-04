import cv2
import pyrealsense2 as rs
import os
import logging
import math
import torch
import numpy as np
import threading
import time
from ultralytics import YOLO
from UR5E_control import *

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

class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "test.pt")  # Your main model
        self.model = YOLO(model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.labels = self.model.names

        hand_model_path = os.path.join(current_directory, "hand_model.pt")  # Hand detection model
        self.hand_model = YOLO(hand_model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.hand_labels = self.hand_model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, verbose=False, show=False)
        return results

    def detect_hands(self, frame):
        hand_results = self.hand_model.predict(source=frame, verbose=False, show=False)
        return hand_results

    def is_bad_placement(self, label):
        if 'bad' in label.lower():
            return True
        return False

class CameraPosition:
    def __init__(self, robot, boxing_machine):
        self.detector = ObjectDetector()
        self.robot = robot
        self.boxing_machine= boxing_machine
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

        # Hand detection related attributes
        self.hand_detected = False
    
    def capture_position(self, slow=False):
        pickup_tcp = [-47.5 / 1000, -140 / 1000, 135 / 1000, math.radians(0), math.radians(0), math.radians(0)]
        self.robot.set_tcp(pickup_tcp)

        target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
        if slow:
            logging.info("check part type, move to camera position")
            self.robot.move_l(target_position, 0.3, 0.3)
        else:
            self.robot.move_l(target_position, 3, 3)

    def transform_coordinates(self, xp, yp, zp):
        a, b, c = -0.0010677615453140213, 3.094561948991097e-05, -0.17959680557618776
        d, e, f = 2.482562688915765e-05, 0.0010493343791252749, -0.2507558317896495

        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f

        return xd, yd

    def detect_object_without_start(self, min_length=170, slow=False):
        self.capture_position(slow)
        time.sleep(1)
        not_found = True
        logging.info("start capturing frames")
        while not_found:
            self.boxing_machine.wait_if_paused()
            '''Capture frames and detect objects'''
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            frame = np.asanyarray(color_frame.get_data())
            with self.frame_lock:
                self.last_frame = frame

            if self.check_for_hand(frame):
                logging.info("Hand detected! Pausing operations...")
                self.boxing_machine.pause()
                continue

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

                            if self.detector.is_bad_placement(label):
                                logging.info("Bad placement detected!")
                                return True

                            if label in ['Big-Blue', 'Green', 'Holed', 'Rubber', 'Small-Blue'] and length >= min_length and width * height < 75000:
                                current_coordinates = (x_left, y_middle)
                                if self.is_stable(current_coordinates):
                                    logging.info("Stable")
                                    xd, yd = self.transform_coordinates(x_left, y_middle, depth)
                                    logging.info(f"Detected (x, y, z): ({x_left}, {y_middle}, {depth}) conf: {box.conf}")

                                    if xd > -0.750 and xd < -0.41 and yd > -0.152 and yd < 0.095:
                                        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                                        text = f'X: {x_left}, Y: {y_middle}, Z: {depth:.2f}m'
                                        cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                        text = f'{label} ({box.conf.item():.2f})'
                                        cv2.putText(frame, text, (bbox[0], bbox[1] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                                        not_found = False
                                        with self.frame_lock:
                                            self.last_frame = frame
                                        return (xd, yd, label)
                                    else:
                                        logging.error("Part out of reach")
                                else:
                                    logging.info("Not stable")
        return (0, 0, 0)

    def check_for_hand(self, frame):
        hand_results = self.detector.detect_hands(frame)  # Use the model from ObjectDetector

        for result in hand_results:
            for box in result.boxes:
                if box.conf > 0.8:
                    bbox = box.xyxy[0].cpu().numpy()
                    label = self.detector.hand_labels[int(box.cls[0])]
                    if label == 'Hand':  # Label for hand
                        logging.info(f"Hand detected with confidence {box.conf}")
                        return True
        return False

    def is_stable(self, current_coordinates):
        """Check stability separately for two rows."""
        x, y = current_coordinates

        if self.previous_coordinates_row1 is None or abs(y - self.previous_coordinates_row1[1]) < self.row_gap_threshold:
            row = "row1"
            prev_coords = self.previous_coordinates_row1
            last_time = self.last_stable_time_row1
        else:
            row = "row2"
            prev_coords = self.previous_coordinates_row2
            last_time = self.last_stable_time_row2

        if prev_coords is None:
            self.update_row_state(row, current_coordinates)
            return False

        distance = np.linalg.norm(np.array(current_coordinates) - np.array(prev_coords))
        if distance > self.row_threshold:
            self.update_row_state(row, current_coordinates)
            return False

        if time.time() - last_time >= 0.3:
            return True

        return False

    def update_row_state(self, row, coordinates):
        """Update the state for a specific row."""
        if row == "row1":
            self.previous_coordinates_row1 = coordinates
            self.last_stable_time_row1 = time.time()
        else:
            self.previous_coordinates_row2 = coordinates
            self.last_stable_time_row2 = time.time()

    def stop_display_thread(self):
        self.display_thread_running = False

    def check_bad_placement(self):
        frame = self.last_frame
        if frame is None:
            logging.error("No frame available for bad placement check.")
            return False  # or raise an exception

        hand_results = self.detector.detect_objects(frame)  # Use the model from ObjectDetector

        for result in hand_results:
            for box in result.boxes:
                if box.conf > 0.8:
                    label = self.detector.labels[int(box.cls[0])]
                    if self.detector.is_bad_placement(label):
                        logging.info(f"Bad placement detected with label: {label} and confidence {box.conf}")
                        return True
        return False
