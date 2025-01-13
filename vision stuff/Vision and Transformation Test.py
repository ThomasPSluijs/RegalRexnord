import os
import cv2
import numpy as np
import torch
from ultralytics import YOLO
import pyrealsense2 as rs

class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "test.pt")
        self.model = YOLO(model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, verbose=False, show=False)
        return results

class CameraPosition:
    def __init__(self, use_realsense=True):
        self.use_realsense = use_realsense
        self.detector = ObjectDetector()
        if self.use_realsense:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            self.pipeline.start(self.config)
            self.align = rs.align(rs.stream.color)
        else:
            self.cap = cv2.VideoCapture(0)

    def transform_coordinates(self, xp, yp, depth, intrinsics):
        a, b, c = -0.0010677615453140213, 3.094561948991097e-05, -0.17959680557618776
        d, e, f = 2.482562688915765e-05, 0.0010493343791252749, -0.2507558317896495

        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f
        zd = depth  # Use the depth value directly

        return xd, yd, zd

    def stream_and_detect(self):
        try:
            while True:
                if self.use_realsense:
                    frames = self.pipeline.wait_for_frames()
                    aligned_frames = self.align.process(frames)
                    color_frame = aligned_frames.get_color_frame()
                    depth_frame = aligned_frames.get_depth_frame()

                    if not color_frame or not depth_frame:
                        continue

                    frame = np.asanyarray(color_frame.get_data())
                    depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
                    depth_image = np.asanyarray(depth_frame.get_data())
                else:
                    ret, frame = self.cap.read()
                    if not ret:
                        break

                results = self.detector.detect_objects(frame.copy())

                if results is not None:
                    for result in results:
                        for box in result.boxes:
                            if box.conf > 0.8:
                                bbox = box.xyxy[0].cpu().numpy()
                                bbox = [int(coord) for coord in bbox[:4]]
                                x_left = bbox[0]
                                y_middle = int((bbox[1] + bbox[3]) / 2)
                                
                                if self.use_realsense:
                                    depth = depth_frame.get_distance(x_left, y_middle)  # Get depth value
                                    xd, yd, zd = self.transform_coordinates(x_left, y_middle, depth, depth_intrin)  # Transform coordinates
                                else:
                                    depth = 0  # Placeholder value for depth
                                    xd, yd, zd = self.transform_coordinates(x_left, y_middle, depth, None)  # Transform coordinates

                                label = self.detector.labels[int(box.cls[0])]
                                print(f"Detected (x, y, z): ({xd}, {yd}, {zd})")

                                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                                text = f'X: {x_left}, Y: {y_middle}, Z: {depth:.2f}m'
                                cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                text = f'{label} ({box.conf.item():.2f})'
                                cv2.putText(frame, text, (bbox[0], bbox[1] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                cv2.imshow('frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            if self.use_realsense:
                self.pipeline.stop()
            else:
                self.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    use_realsense = False  # Set to True to use RealSense, or False to use the webcam
    camera = CameraPosition(use_realsense=use_realsense)
    camera.stream_and_detect()