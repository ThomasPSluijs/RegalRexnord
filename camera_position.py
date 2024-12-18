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
    def __init__(self, robot):
        self.detector = ObjectDetector()
        self.robot = robot
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(self.config)
        self.align = rs.align(rs.stream.color)

    # moves robot to capture position
    def capture_position(self):
        tool_frame = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]
        self.robot.set_tcp(tool_frame)

        target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
        self.robot.move_l(target_position, 1, 1)

    # transform camera coordinates to real world (robot) coordinates
    def transform_coordinates(self, xp, yp, zp):
        a, b, c = -0.0959043379 / 100, -0.0040884899 / 100, -13.2387630728 / 100
        d, e, f = 0.0015836117 / 100, 0.1064093728 / 100, -26.4297290624 / 100
        g, h, i, j = 0.1, 0.2, 0.3, 0.4  # Example values, these need to be calibrated

        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f
        zd = g * xp + h * yp + i * zp + j

        return xd, yd, zd

    # main function that detects objects and returns the object locations
    def detect_object_without_start(self, min_length=170):
        self.capture_position()

        not_found = True
        while not_found:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            frame = np.asanyarray(color_frame.get_data())

            results = self.detector.detect_objects(frame)
            if results is not None:
                for result in results:
                    for box in result.boxes:
                        if box.conf > 0.65:
                            bbox = box.xyxy[0].cpu().numpy()
                            bbox = [int(coord) for coord in bbox[:4]]
                            x_left = bbox[0]
                            y_middle = int((bbox[1] + bbox[3]) / 2)
                            width = bbox[2] - bbox[0]
                            height = bbox[3] - bbox[1]

                            depth = depth_frame.get_distance(x_left, y_middle)

                            logging.info(f" width * height: {width * height}, depth: {depth}")
                            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)

                            length = max(width, height)


                            if length >= min_length:
                                xd, yd, zd = self.transform_coordinates(x_left, y_middle, depth)
                                target_position = [xd, yd, zd, 2.222, 2.248, 0.004]

                                print(f"Detected (x, y, z): ({x_left}, {y_middle}, {depth}) -> Calculated TCP Position: {target_position}  conf: {box.conf}")
## often crashes
                                cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)
 
                                text = f'X: {x_left}, Y: {y_middle}, Z: {depth:.2f}m'
                                cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
## often crashes
                                cv2.imshow('RealSense Camera Stream', frame)
                                if cv2.waitKey(1) & 0xFF == ord('q'):
                                    break

                                not_found = False
                                return (xd, yd, zd)

        return (0, 0, 0)

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
        results = self.model.predict(source=frame, show=False)
        return results

# for testing only
if __name__ == "__main__":
    cv2.namedWindow("RealSense Camera Stream", cv2.WINDOW_AUTOSIZE) 

    robot = URControl("192.168.0.1")
    robot.connect()

    camera = CameraPosition(robot)
    camera.capture_position()

    while True:
        _ = camera.detect_object_without_start()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.pipeline.stop()

    robot.stop_robot_control()
    cv2.destroyAllWindows()
