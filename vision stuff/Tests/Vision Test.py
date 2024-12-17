import cv2
import pyrealsense2 as rs
import os
import logging
import math
from UR5E_control import *
from ultralytics import YOLO
from matplotlib import pyplot as plt
import numpy as np

# Suppress logging for this example
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

#yolo log filter
class YoloLogFilter(logging.Filter):
    def filter(self, record):
        return not any(keyword in record.getMessage() for keyword in ['Speed:', 'per image', 'ms'])

# Suppress YOLO logging
yolo_logger = logging.getLogger("yolo_logger")
yolo_logger.addFilter(YoloLogFilter())

#uses camera to run yolo model and get x and y coordinates of the parts
class CameraPosition:
    def __init__(self, robot):
        self.detector = ObjectDetector()
        self.cap = None
        self.robot = robot
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    #moves robot to capture position
    def capture_position(self):
        # Define the target position and orientation
        target_position = [-0.5981433108063265, -0.10770597622051334, 0.5297075288092719, 2.222, 2.248, 0.004]

        #move
        self.robot.move_l(target_position, 1, 1)

#detect objects
    def detect_objects(self):
        # Start the camera pipeline
        self.pipeline.start(self.config)

        while True:
            # Wait for a frame
            frames = self.pipeline.wait_for_frames()

            # Get the color frame
            color_frame = frames.get_color_frame()

            # Convert the color frame to a numpy array
            color_image = np.asanyarray(color_frame.get_data())

            # Detect objects in the frame
            results = self.detector.detect_objects(color_image)

            # Draw bounding boxes around detected objects
            for result in results:
                scores, category = result

                # Draw a red dot on the detected object
                cv2.circle(color_image, (int(category), int(category)), 2, (0, 0, 255), -1)

                # Show x y and z coordinate of the detected object
                cv2.putText(color_image, f"X: {category}, Y: {category}, Z: {0}", (int(category), int(category - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Display the output
            cv2.imshow('Object Detection', color_image)

            # Wait for a key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Stop the camera pipeline
        self.pipeline.stop()

#runs yolo model and detects objects
class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "best.pt")
        self.model = YOLO(model_path)
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, show=False)
        return results


#for testing only
if __name__ == "__main__":      #only run if this file is run
    robot = URControl("192.168.0.1")
    robot.connect()

    camera = CameraPosition(robot)
    camera.capture_position()
    camera.detect_objects()

    robot.stop_robot_control()