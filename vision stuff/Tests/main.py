from camera_position import CameraPosition

def main():
    # Initialize the camera position
    camera = CameraPosition()

    # Move the robot arm to the capture position
    camera.capture_position()

    # Detect the object
    x, y = camera.detect_object()
    if x == 0 and y == 0:
        print("Failed to detect object.")
        return

    # Print the detected object's coordinates
    print(f"Detected object at ({x}, {y})")

if __name__ == "__main__":
    main()

