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

    # moves robot to capture position
    def capture_position(self):
        pickup_tcp = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]
        self.robot.set_tcp(pickup_tcp)

        target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
        self.robot.move_l(target_position, 3, 3)

    # transform camera coordinates to real world (robot) coordinates
    def transform_coordinates(self, xp, yp, zp):
        a, b, c = -0.0010677615453140213, 3.094561948991097e-05, -0.17959680557618776
        d, e, f = 2.482562688915765e-05, 0.0010493343791252749, -0.2507558317896495


        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f

        return xd, yd

    # main function that detects objects and returns the object locations
    def detect_object_without_start(self, min_length=170):
        self.capture_position()

        time.sleep(1)

        not_found = True
        logging.info("start capturing frames")
        while not_found:
            logging.info("not found parts yet")
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue


            logging.info("Processing frames...")
            frame = np.asanyarray(color_frame.get_data())
            with self.frame_lock:  # Update last_frame safely
                self.last_frame = frame
            results = None
            results = self.detector.detect_objects(frame.copy())
            
            #logging.info(f"Detection results 1: {results}")
            if results is not None:
                #logging.info(f"Detection results 2: {results}")
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

                            logging.info(f" width * height: {width * height}, depth: {depth}")


                            #draw box around detected part and draw circle at pickup point
                            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                            cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)

                            #put text with coordiantes at the circle
                            text = f'X: {x_left}, Y: {y_middle}, Z: {depth:.2f}m'
                            cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                            #put label (item_type) on screen
                            label = self.labels[int(box.cls[0])]
                            confidence = box.conf.item()
                            text = f'{label} ({confidence:.2f})'
                            cv2.putText(frame, text, (bbox[0], bbox[1] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                            logging.info(f"item type: {label}")

                            with self.frame_lock:  # Update last_frame safely
                                self.last_frame = frame
                            
                            #length check and area check and label
                            length = max(width, height)
                            if label == 'Big-Blue' or label == 'Green' or label == 'Holed' or label == 'Rubber' or label == 'Small-Blue':
                                if length >= min_length and width * height < 75000:
                                    xd, yd = self.transform_coordinates(x_left, y_middle, depth)
                                    target_position = [xd, yd, -0.0705907482294739, 2.222, 2.248, 0.004]

                                    print(f"Detected (x, y, z): ({x_left}, {y_middle}, {depth}) -> Calculated TCP Position: {target_position}  conf: {box.conf}")

                                    not_found = False
                                
                                    with self.frame_lock:  # Update last_frame safely
                                        self.last_frame = frame
                                    return (xd, yd, label)

        return (0, 0, 0)
    
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
