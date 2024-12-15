import cv2
from vision import ObjectDetector
from vision import transform_coordinates

class CameraPosition:
    def __init__(self):
        self.detector = ObjectDetector()
        self.cap = None

    def capture_position(self):
        # Move the robot arm to the capture position
        pass

    def detect_object(self, min_length=100):
        # Open the camera
        self.cap = cv2.VideoCapture(0)

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
                    if result.boxes is not None:
                        for box in result.boxes:
                            bbox = box.xyxy[0].cpu().numpy()
                            bbox = [int(coord) for coord in bbox[:4]]
                            x_left = bbox[0]
                            y_middle = int((bbox[1] + bbox[3]) / 2)
                            width = bbox[2] - bbox[0]
                            height = bbox[3] - bbox[1]

                            # Calculate the length of the object blob
                            length = max(width, height)

                            # Check if the length is greater than or equal to the minimum length
                            if length >= min_length:
                                xd, yd = transform_coordinates(x_left, y_middle)
                                target_position = [xd, yd, 0.5297075288092719, -2.1926151354478987, -2.2424509339020156, 0.009950454521939689]

                                # Print the detected camera coordinates and the resulting TCP position
                                print(f"Detected (x, y): ({x_left}, {y_middle}) -> Calculated TCP Position: {target_position}")

                                # Return the x and y coordinates
                                return x_left, y_middle

            # If no object is detected, continue to the next frame
            continue

        # Release the camera
        self.cap.release()

        # Return default values if no object is detected after multiple frames
        return (0, 0)

#Test
if __name__ == "__main__":
    camera = CameraPosition()
    frame = camera.detect_object()
    if frame is not None:
        cv2.imshow("Detection", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Failed to detect object.")