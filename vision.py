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
        results = self.model(frame)
        return results
    
    def transform_coordinates(self, xp, yp):
        a, b, c = -0.0959043379 / 100, -0.0040884899 / 100, -13.2387630728 / 100
        d, e, f = 0.0015836117 / 100, 0.1064093728 / 100, -26.4297290624 / 100
        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f
        return xd, yd

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
                    xd, yd = self.transform_coordinates(x_left, y_middle)
                    target_position = [xd, yd, 0.5297075288092719, -2.1926151354478987, -2.2424509339020156, 0.009950454521939689]

                    # Print the detected camera coordinates and the resulting TCP position
                    print(f"Detected (x, y): ({x_left}, {y_middle}) -> Calculated TCP Position: {target_position}")

                    # Draw a red dot at the left-most middle part and print coordinates
                    cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)
                    text = f'X: {x_left}, Y: {y_middle}'
                    cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        return frame
    

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