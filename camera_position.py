import cv2
from vision import ObjectDetector


class CameraPosition:
    def __init__(self, robot):
        self.detector = ObjectDetector()
        self.cap = None
        self.robot = robot

    def capture_position(self):
        import logging
        import math

        # Suppress logging for this example
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Define the tool frame
        tool_frame = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]
        self.robot.set_tcp(tool_frame)

        # Define the target position and orientation
        target_position = [-0.5981433108063265, -0.10770597622051334, 0.5297075288092719, 2.222, 2.248, 0.004]

        #move
        self.robot.move_l(target_position, 0.1, 0.1)


    def detect_object(self, min_length=100):
        self.capture_position()
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
                                xd, yd = self.detector.transform_coordinates(x_left, y_middle)
                                target_position = [xd, yd, 0.1297075288092719, 2.222, 2.248, 0.004]

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

'''
#Test
if __name__ == "__main__":
    camera = CameraPosition()
    frame = camera.detect_object()
    if frame is not None:
        cv2.imshow("Detection", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Failed to detect object.") '''