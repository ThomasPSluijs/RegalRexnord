from ultralytics import YOLO
import pyrealsense2 as rs
import numpy as np
import cv2

# Load the trained model
model = YOLO("C:/Users/jawar/Documents/Work/SMR2/Vision/YOLO/best.pt")  # Replace with the path to your trained weights

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start the camera stream
pipeline.start(config)

def draw_red_line(frame, results):
    for detection in results[0].boxes:  # Accessing boxes from the first result
        confidence = detection.conf
        if confidence >= 0.7:  # Filter detections based on confidence score
            x1, y1, x2, y2 = map(int, detection.xyxy[0][:4])
            
            # Draw a red line on the leftmost side of the object
            cv2.line(frame, (x1, y1), (x1, y2), (0, 0, 255), 2)

try:
    while True:
        # Get frames from the camera
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        # Convert the frame to a numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Run YOLOv11 inference
        results = model.predict(source=color_image, show=False)  # Set show=True to display bounding boxes

        # Draw a red line on the leftmost side of detected objects
        draw_red_line(color_image, results)

        # Show the frame with only the red lines
        cv2.imshow("YOLOv11 RealSense Integration", color_image)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # Stop the RealSense pipeline and close windows
    pipeline.stop()
    cv2.destroyAllWindows()
