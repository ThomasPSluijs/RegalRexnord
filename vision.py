import cv2
import numpy as np
import os
from ultralytics import YOLO
import logging

class YoloLogFilter(logging.Filter):
    def filter(self, record):
        return not any(keyword in record.getMessage() for keyword in ['Speed:', 'per image', 'ms'])

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for detailed logs
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

        if isinstance(yolo_image, np.ndarray):  
            result_image, coordinates = self.yolo.get_results(yolo_image)
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
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "best.pt")
        self.model = YOLO(model_path)
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model(frame)
        return results

    def process_frame(self, frame):
        logging.debug("Processing frame...")
        results = self.detect_objects(frame)
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    logging.debug(f"Detected object with bbox: {box.xyxy}")
                    bbox = box.xyxy[0].cpu().numpy()
                    bbox = [int(coord) for coord in bbox[:4]]
                    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)

                    x_left = bbox[0]
                    y_middle = int((bbox[1] + bbox[3]) / 2)
                    xd, yd = transform_coordinates(x_left, y_middle)
                    target_position = [xd, yd, 0.5297075288092719, -2.1926151354478987, -2.2424509339020156, 0.009950454521939689]

                    # Print the detected camera coordinates and the resulting TCP position
                    print(f"Detected (x, y): ({x_left}, {y_middle}) -> Calculated TCP Position: {target_position}")

                    # Draw a red dot at the left-most middle part and print coordinates
                    cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)
                    text = f'X: {x_left}, Y: {y_middle}'
                    cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

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

    # Transform camera coordinates to robot TCP coordinates
    def transform_coordinates_to_tcp(self, coordinates):
        center_x, center_y = coordinates
        depth_frame = self.get_depth_frame()
        depth = depth_frame.get_distance(center_x, center_y)

        # Convert to camera coordinates relative to the camera
        X_cm = (center_x - C_x) * depth / F_x * 100  # Convert to cm
        Y_cm = -(center_y - C_y) * depth / F_y * 100  # Convert to cm

        # Transform to robot TCP coordinates
        xd, yd = transform_coordinates(X_cm, Y_cm)
        return xd, yd

# Test ####################################################################################################
if __name__ == "__main__":
    detector = ObjectDetector()
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = detector.process_frame(frame)
        cv2.imshow("Detected Object", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()