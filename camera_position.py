import cv2
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

    #moves robot to capture position
    def capture_position(self):
        # Define the tool frame
        tool_frame = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]
        self.robot.set_tcp(tool_frame)

        # Define the target position and orientation
        target_position = [-0.5981433108063265, -0.10770597622051334, 0.5297075288092719, 2.222, 2.248, 0.004]

        #move
        self.robot.move_l(target_position, 1, 1)



    #transform camera coordinates to real world (robot) coordinates
    def transform_coordinates(self, xp, yp):
        a, b, c = -0.0959043379 / 100, -0.0040884899 / 100, -13.2387630728 / 100
        d, e, f = 0.0015836117 / 100, 0.1064093728 / 100, -26.4297290624 / 100
        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f
        return xd, yd



    #main function that detects opbjects and returns the object locations
    def detect_object(self, min_length=100):
        self.capture_position()
        # Open the camera
        self.cap = cv2.VideoCapture(2)

        while True:
            # Capture a frame from the camera
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break


            # Use the ObjectDetector to detect the object
            results = self.detector.detect_objects(frame)
            if results is not None:
                for result in results:
                    #if result.boxes is not None:
                    for box in result.boxes:
                        if box.conf > 0.7:
                            bbox = box.xyxy[0].cpu().numpy()
                            bbox = [int(coord) for coord in bbox[:4]]
                            x_left = bbox[0]
                            y_middle = int((bbox[1] + bbox[3]) / 2)
                            width = bbox[2] - bbox[0]
                            height = bbox[3] - bbox[1]
                            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)

                            # Calculate the length of the object blob
                            length = max(width, height)

                            # Check if the length is greater than or equal to the minimum length '''
                            if length >= min_length:
                                xd, yd = self.transform_coordinates(x_left, y_middle)
                                target_position = [xd, yd, 0.1297075288092719, 2.222, 2.248, 0.004]

                                # Print the detected camera coordinates and the resulting TCP position
                                print(f"Detected (x, y): ({x_left}, {y_middle}) -> Calculated TCP Position: {target_position}  conf: {box.conf}")

                                # Draw a red dot at the left-most middle part and print coordinates
                                cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)
                                text = f'X: {x_left}, Y: {y_middle}'
                                cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    

                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                
                                #plt.imshow(frame_rgb)
                                #plt.title("Detected Object")  # Set a title for the image
                                #plt.axis("off")  # Hide the axes for a cleaner look
                                #plt.show()
                

                                # Return the rounded x and y coordinate
                                return (xd, yd)
                            
                        else:
                            logging.info(f"not certain if there are parts: {box.conf}")

            # If no object is detected, continue to the next frame
            continue

        # Release the camera
        self.cap.release()

        # Return default values if no object is detected after multiple frames
        return (0, 0)
    


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
    frame = camera.detect_object()
    #if frame is not None:
    #    cv2.imshow("Detection", frame)
    #    cv2.waitKey(0)
    #    cv2.destroyAllWindows()
    ##else:
    #   print("Failed to detect object.") 

    robot.stop_robot_control()  