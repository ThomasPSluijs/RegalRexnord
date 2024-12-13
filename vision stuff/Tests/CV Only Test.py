import cv2
import numpy as np
import os
from ultralytics import YOLO

class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        # Get the directory of the current script
        current_directory = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to best.pt
        model_path = os.path.join(current_directory, "best.pt")

        # Load the trained model
        self.model = YOLO(model_path)

        # Retrieve class labels from the model
        self.labels = self.model.names

    def detect_objects(self, frame):
        # Perform the object detection
        results = self.model(frame)
        return results

    def calculate_distance(self, bbox):
        # Assume some camera parameters and object dimensions for distance calculation
        # This is a placeholder; you need actual camera calibration and object size data
        fx = 640  # focal length in pixels
        real_object_width = 0.3  # width of the object in meters
        pixel_object_width = bbox[2] - bbox[0]  # width of the object in pixels

        distance = (real_object_width * fx) / pixel_object_width
        return distance

    def draw_dot(self, frame, bbox, depth_frame):
        # Calculate the coordinates of the left-most middle part of the bbox
        x_left = bbox[0]
        y_middle = int((bbox[1] + bbox[3]) / 2)

        # Get depth value at the x_left and y_middle coordinates
        depth = depth_frame[y_middle, x_left]

        # Draw a red dot at the left-most middle part
        cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)

        # Put text of the depth and coordinates near the dot in the specified format
        text = f'X: {x_left}\nY: {y_middle}\nZ: {depth:.2f}m'
        
        # Split text into lines
        for i, line in enumerate(text.split('\n')):
            cv2.putText(frame, line, (x_left, y_middle - 30 + i * 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)


    def process_frame(self, frame, depth_frame):
        results = self.detect_objects(frame)
        
        # Iterate through detected objects, if any
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    bbox = box.xyxy[0].cpu().numpy()  # Convert box coordinates to NumPy array and move to CPU
                    bbox = [int(coord) for coord in bbox[:4]]  # Convert bounding box coordinates to integers
                    self.draw_dot(frame, bbox, depth_frame)

                    # Draw the bounding box
                    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)

        return frame


def main():
    # Initialize the object detector
    detector = ObjectDetector()

    # Open a connection to the RealSense camera
    cap = cv2.VideoCapture(0)  # Adjust the index if needed

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Assuming we have a way to get the depth frame
        # For now, let's use a dummy depth frame with all ones (1 meter depth everywhere)
        depth_frame = np.ones((frame.shape[0], frame.shape[1]))  # Placeholder depth frame

        # Process the frame
        frame = detector.process_frame(frame, depth_frame)

        # Display the frame
        cv2.imshow('RealSense Camera Stream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
