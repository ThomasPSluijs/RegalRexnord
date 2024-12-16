# Setup and Initialization ########################################################################################################
from ultralytics import YOLO
import os
import pyrealsense2 as rs
import numpy as np
import cv2
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class Vision():
    def __init__(self):
        self.yolo = YoloVision()
        self.camera = Camera()
        self.camera_stream_status = False

    def do_vision(self):
        if not self.camera_stream_status: 
            self.camera.start_stream()
            self.camera_stream_status = True

        yolo_image = self.camera.get_color_frame()

        if isinstance(yolo_image, np.ndarray):  #check if image is correct instance/type
            result_image, coordinates = self.yolo.get_results(yolo_image)   #get yolo results
            cv2.imshow("YOLOv11 RealSense Integration", result_image)
            if coordinates:
                x_tcp, y_tcp = self.camera.transform_coordinates_to_tcp(coordinates[0])
                return x_tcp, y_tcp
            else:
                logging.warning("No objects detected.")
                return None, None
        else:
            logging.warning("Got no image to put in Yolo Model.")
            return None, None

    def stop(self):
        self.camera.stop_stream()

# YoloVision Class ########################################################################################
class YoloVision():
    def __init__(self):
        '''setup yolo model'''
        # Get the directory of the current script
        current_directory = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to best.pt
        model_path = os.path.join(current_directory, "vision stuff/best.pt")

        # Load the trained model
        self.model = YOLO(model_path)

        # Retrieve class labels from the model
        self.labels = self.model.names

    def get_results(self, color_image):
        logging.info("get yolo vision results")
        # Run model
        results = self.model.predict(source=color_image, show=False)

        # Filter results based on confidence score
        filtered_boxes = [box for box in results[0].boxes if box.conf >= 0.7]

        # Get coordinates of detected object
        coordinates = []
        for box in filtered_boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0][:4])
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            coordinates.append((center_x, center_y))

        # Draw boxes on the image
        result_image = self.draw_boxes(color_image, filtered_boxes, self.labels)
        return result_image, coordinates

    def draw_boxes(self, frame, boxes, labels):
        logging.info("draw boxes on yolo image")
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0][:4])
            class_id = int(box.cls.item())  # Get the class ID
            confidence = box.conf.item()
            label_text = f"{labels[class_id]}: {confidence:.2f}"
            
            # Draw the bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Put the label text above the bounding box
            cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame

# Camera Class ##################################################################################
class Camera():
    def __init__(self):
        '''setup camera'''
        self.pipeline = None
        self.config = None
        self.setup()        #start pipelining and config 

    #start camera stream/pipeline
    def setup(self):
        try:
            logging.info("setup camera")
            # Configure RealSense pipeline
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)  # Enable depth stream
        except Exception as e:
            logging.error(f"problem setting up camera: {e}")

    #start camera stream
    def start_stream(self):
        try:
            self.pipeline.start(self.config)
        except Exception as e:
            logging.error(f"cannot start camera stream: {e}")

    #stop camera stream
    def stop_stream(self):
        try:
            self.pipeline.stop()
        except Exception as e:
            logging.error(f"cannot stop camera stream: {e}")

    #get color frames from the camera
    def get_color_frame(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
    
        #convert color frame to numpy array
        color_image = np.asanyarray(color_frame.get_data())

        return color_image

    #get depth frames from the camera
    def get_depth_frame(self):
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        return depth_frame
    
    	
    #transform coordinates
    def transform_coordinates(self, xp, yp):
        a, b, c = -0.0959043379 / 100, -0.0040884899 / 100, -13.2387630728 / 100
        d, e, f = 0.0015836117 / 100, 0.1064093728 / 100, -26.4297290624 / 100
        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f
        return xd, yd

    # Transform camera coordinates to robot TCP coordinates
    def transform_coordinates_to_tcp(self, coordinates):
        center_x, center_y = coordinates
        depth_frame = self.get_depth_frame()
        depth = depth_frame.get_distance(center_x, center_y)

        # Convert to camera coordinates relative to the camera
        X_cm = (center_x - C_x) * depth / F_x * 100  # Convert to cm
        Y_cm = -(center_y - C_y) * depth / F_y * 100  # Convert to cm

        # Transform to robot TCP coordinates
        xd, yd = self.transform_coordinates(X_cm, Y_cm)
        return xd, yd

# Test ####################################################################################################
if __name__ == "__main__":
    vision = Vision()

    try:
        while True:
            x_tcp, y_tcp = vision.do_vision()
            if x_tcp is not None and y_tcp is not None:
                logging.info(f"Detected object TCP coordinates: X={x_tcp}, Y={y_tcp}")
                    
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        vision.stop()
        cv2.destroyAllWindows()


