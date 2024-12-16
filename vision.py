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

# Suppress YOLO logging
yolo_logger = logging.getLogger("yolo_logger")
yolo_logger.addFilter(YoloLogFilter())



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
    
    def transform_coordinates(self, xp, yp):
        a, b, c = -0.0959043379 / 100, -0.0040884899 / 100, -13.2387630728 / 100
        d, e, f = 0.0015836117 / 100, 0.1064093728 / 100, -26.4297290624 / 100
        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f
        return xd, yd



#Test
'''
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
    '''