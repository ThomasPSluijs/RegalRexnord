from ultralytics import YOLO

# Load the trained model
model = YOLO("C:/Users/jawar/Documents/Work/SMR2/Vision/YOLO/best.pt")  # Replace with the path to your trained weights

import pyrealsense2 as rs
import numpy as np
import cv2

#test commit

# Custom labels for your classes
labels = ["Bad-Wide-Blue", "Wide-Blue"]  # Swapped the labels

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start the camera stream
pipeline.start(config)

def draw_boxes(frame, boxes):
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0][:4])
        class_id = int(box.cls.item())  # Get the class ID
        confidence = box.conf.item()
        label_text = f"{labels[class_id]}: {confidence:.2f}"
        
        # Draw the bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Put the label text above the bounding box
        cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

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

        # Filter results based on confidence score
        filtered_boxes = [box for box in results[0].boxes if box.conf >= 0.7]

        # Draw detection boxes with labels and confidence scores
        draw_boxes(color_image, filtered_boxes)

        # Show the frame with detection boxes
        cv2.imshow("YOLOv11 RealSense Integration", color_image)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # Stop the RealSense pipeline and close windows
    pipeline.stop()
    cv2.destroyAllWindows()
