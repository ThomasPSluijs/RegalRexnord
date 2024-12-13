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



'''vision class. uses yolovision and camera classes and combines them to get the required results'''
class Vision():
    def __init__(self):
        self.yolo = YoloVision()
        self.camera = Camera()

        self.camera_stream_status = False


    #get image from camera, get yolo results, show results. to add: get x and y coordinates
    def do_vision(self):
        if not self.camera_stream_status: 
            self.camera.start_stream()
            self.camera_stream_status = True

        yolo_image = self.camera.get_color_frame()

        if isinstance(yolo_image, np.ndarray):  
            result = self.yolo.get_results(yolo_image)
            cv2.imshow("YOLOv11 RealSense Integration", result)  
        else: logging.warning("got no image to put in Yolo Model. ")
        

    #stop vision, for now: stop camera stream
    def stop(self):
        self.camera.stop_stream()


'''yolovision: get results from a camera frame using the Yolo model'''
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
        #run model
        results = self.model.predict(source=color_image,show=False)

        # Filter results based on confidence score
        filtered_boxes = [box for box in results[0].boxes if box.conf >= 0.7]

        #draw boxes
        result_image = self.draw_boxes(color_image, filtered_boxes, self.labels)
        return result_image

    def draw_boxes(self, frame, boxes, labels):
        logging.info("draw boxes an yolo image")
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



'''camera class: connects to camera and gets camera frames'''
class Camera():
    def __init__(self):
        '''setup camera'''
        self.pipeline = None
        self.config = None
        self.setup()        #start pipeling, config 

    #start camera stream/pipelin
    def setup(self):
        try:
            logging.info("setup camera")
            # Configure RealSense pipeline
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        except Exception as e:
            logging.error(f"problem setting up camera: {e}")

    #start camera stream
    def start_stream(self):
        try:
            self.pipeline.start(self.config)
        except Exception as e:
            logging.error(f"cannot start camera stream: {e}")

    #stop camera strema
    def stop_stream(self):
        try:
            self.pipeline.stop()
        except Exception as e:
            logging.error(f"cannot stop camera stream: {e}")


    #get frames etc
    def get_color_frame(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
    
        #convert color frame to numpy array
        color_image = np.asanyarray(color_frame.get_data())

        return color_image




'''used for testing this file. commend out later'''
vision = Vision()

try:
    while True:
        vision.do_vision()
            # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    vision.stop()
    cv2.destroyAllWindows()