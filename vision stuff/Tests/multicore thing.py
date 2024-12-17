import multiprocessing
import cv2
import pyrealsense2 as rs
import os
import logging
import math
from UR5E_control import *
from ultralytics import YOLO
from matplotlib import pyplot as plt

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

# uses camera to run yolo model and get x and y coordinates of the parts
class CameraPosition:
    def __init__(self, robot=None):
        self.detector = ObjectDetector()
        self.cap = None
        self.robot = robot
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # moves robot to capture position
    def capture_position(self):
        # Define the tool frame
        tool_frame = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]
        self.robot.set_tcp(tool_frame)

        # Define the target position and orientation
        target_position = [-0.6653950974172558, -0.0982792833217151, 0.5297078618906171, 2.222, 2.248, 0.004]

        # move
        self.robot.move_l(target_position, 1, 1)

    # transform camera coordinates to real world (robot) coordinates
    def transform_coordinates(self, xp, yp):
        a, b, c = -0.0959043379 / 100, -0.0040884899 / 100, -13.2387630728 / 100
        d, e, f = 0.0015836117 / 100, 0.1064093728 / 100, -26.4297290624 / 100
        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f
        return xd, yd

    # main function that detects objects and returns the object locations
    def detect_object_without_start(self, queue, min_length=170):
        while True:
            # Wait for a frame
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            # Convert the frame to a numpy array
            frame = np.asanyarray(color_frame.get_data())

            # Use the ObjectDetector to detect the object
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
                            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)

                            # Calculate the length of the object blob
                            length = max(width, height)

                            # Check if the length is greater than or equal to the minimum length
                            if length >= min_length:
                                xd, yd = self.transform_coordinates(x_left, y_middle)
                                target_position = [xd, yd, 0.1297075288092719, 2.222, 2.248, 0.004]

                                # Print the detected camera coordinates and the resulting TCP position
                                print(f"Detected (x, y): ({x_left}, {y_middle}) -> Calculated TCP Position: {target_position}  conf: {box.conf} length: {length}")

                                # Draw a red dot at the left-most middle part and print coordinates
                                cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)
                                text = f'X: {x_left}, Y: {y_middle}, Length: {length}'
                                cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                                # Send the target position and length to the main process
                                queue.put((target_position, length))

            # Display the frame
            cv2.imshow('RealSense Camera Stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# runs yolo model and detects objects
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

def object_detection_process(queue):
    camera = CameraPosition()

    # Start the pipeline
    camera.pipeline.start(camera.config)

    # Start detecting objects
    camera.detect_object_without_start(queue)

    # Stop the pipeline
    camera.pipeline.stop()
    cv2.destroyAllWindows()

# for testing only
if __name__ == "__main__":
    robot = URControl("192.168.0.1")
    robot.connect()

    # Move the robot to the capture position once
    camera = CameraPosition(robot)
    camera.capture_position()

    # Create a queue for communication
    queue = multiprocessing.Queue()

    # Start the object detection process in a separate process
    p = multiprocessing.Process(target=object_detection_process, args=(queue,))
    p.start()

    try:
        while True:
            target_position, length = queue.get()
            # Print the coordinates and length
            print(f"Object coordinates: {target_position}, Detected length: {length}")
    except KeyboardInterrupt:
        p.terminate()
        p.join()

    robot.stop_robot_control()
