import cv2
import pyrealsense2 as rs
import os
import logging
import math
import torch
import numpy as np
from ultralytics import YOLO
import threading
import time

# Suppress logging for this example
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# yolo log filter
class YoloLogFilter(logging.Filter):
    def filter(self, record):
        return not any(keyword in record.getMessage() for keyword in ['Speed:', 'per image', 'ms'])

# Suppress YOLO logging
yolo_logger = logging.getLogger("yolo_logger")
yolo_logger.addFilter(YoloLogFilter())

# uses camera to run yolo model and get x, y, and z coordinates of the parts
class CameraPosition:
    def __init__(self, robot, boxing_machine):
        self.detector = ObjectDetector()
        self.robot = robot
        self.boxing_machine = boxing_machine
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.pipeline.start(self.config)
        self.align = rs.align(rs.stream.color)
        self.labels = self.detector.labels

        self.last_frame = None                  #last frame storage so interface can show last frame
        self.frame_lock = threading.Lock()      #threading lock so no reading/writing lastframe at the same time
        self.display_thread_running = True      #display thread runs as long as this is true


        # Separate states for each row. makes sure parts are stationary when picking up
        self.previous_coordinates_row1 = None
        self.previous_coordinates_row2 = None
        self.last_stable_time_row1 = 0
        self.last_stable_time_row2 = 0

        self.row_threshold = 6  # Stability threshold in pixels
        self.row_gap_threshold = 50  # Distance to separate rows (adjust as necessary)



    # moves robot to capture position
    def capture_position(self, slow=False):
        capture_tcp = [-47.5 / 1000, -140 / 1000, 135 / 1000, math.radians(0), math.radians(0), math.radians(0)]
        self.robot.set_tcp(capture_tcp)

        target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
        if slow:
            logging.info("check part type, move to camera position")
            self.robot.move_l(target_position, 0.3, 0.3)
        else:
            self.robot.move_l(target_position, 3, 3)

    # transform camera coordinates to real world (robot) coordinates
    def transform_coordinates(self, xp, yp, zp):
        a, b, c = -0.0010677615453140213, 3.094561948991097e-05, -0.17959680557618776
        d, e, f = 2.482562688915765e-05, 0.0010493343791252749, -0.2507558317896495

        xd = a * xp + b * yp + c
        yd = d * xp + e * yp + f

        return xd, yd
    


    #function that detects box orientation
    def initialize_position(self):
        # Define the specific positions to check
        positions = [
            [-0.375, 0.415, 0.333, -2.195, -2.221, -0.004],  # Position 1
            [0.0457, 0.415, 0.333, -2.195, -2.221, -0.004],  # Position 2
        ]

        orientations = {}
        not_found = [True, True]
        frame_0 = None
        frame_1 = None

        for i, position in enumerate(positions):
            self.robot.move_l(position, 0.5, 3)
            time.sleep(0.3)

            while not_found[i]:
                frames = self.pipeline.wait_for_frames()
                aligned_frames = self.align.process(frames)
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()

                if not color_frame or not depth_frame:
                    continue

                frame = np.asanyarray(color_frame.get_data())
                results = self.detector.detect_objects(frame.copy())

                if results is not None:
                    highest_confidence = 0
                    best_bbox = None
                    best_label = None

                    for result in results:
                        for box in result.boxes:
                            bbox = box.xyxy[0].cpu().numpy()
                            bbox = [int(coord) for coord in bbox[:4]]
                            label = self.labels[int(box.cls[0])]
                            confidence = box.conf.item()
                            logging.info(f"Detected object: {label} with confidence {confidence} at position {i+1}")

                            # Only consider the detection with the highest confidence
                            if confidence > 0.3 and confidence > highest_confidence:
                                highest_confidence = confidence
                                best_bbox = bbox
                                best_label = label

                    if best_bbox and best_label:
                        # Assign orientation based on label
                        found = False
                        if 'horizontal' in best_label.lower():
                            orientations[f'box_{i}'] = 'horizontal'
                            color = (0, 255, 0)
                            found = True
                        elif 'vertical' in best_label.lower():
                            orientations[f'box_{i}'] = 'vertical'
                            color = (255, 0, 0)
                            found = True

                        if found:
                            # Annotate the frame with the best detection
                            cv2.rectangle(frame, (best_bbox[0], best_bbox[1]), (best_bbox[2], best_bbox[3]), color, 2)
                            annotation = f"Box {i + 1}: {best_label} ({highest_confidence:.2f})"
                            text_x = best_bbox[0]
                            text_y = max(best_bbox[1] - 10, 20)  # Ensure text is always visible
                            cv2.putText(frame, annotation, (text_x, text_y),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                            # Assign the annotated frame to the correct box
                            if i == 0:
                                frame_0 = frame
                            elif i == 1:
                                frame_1 = frame

                            not_found[i] = False

        # Ensure both frames have the same height for horizontal concatenation
        h_min = min(frame_0.shape[0], frame_1.shape[0])
        frame_0_resized = cv2.resize(frame_0, (int(frame_0.shape[1] * h_min / frame_0.shape[0]), h_min))
        frame_1_resized = cv2.resize(frame_1, (int(frame_1.shape[1] * h_min / frame_1.shape[0]), h_min))

        # Concatenate the frames horizontally
        combined_frame = cv2.hconcat([frame_1_resized, frame_0_resized])

        with self.frame_lock:
            self.last_frame = combined_frame

        logging.info(f"Orientation detection complete: {orientations}")
        return orientations



    # main function that detects objects and returns the object locations
    def detect_pickable_parts(self, min_length=170, slow=False):
        self.capture_position(slow)
        time.sleep(1)
        not_found = True
        logging.info("start capturing frames")

        while not_found:
            logging.info("not found yet")
            
            self.boxing_machine.wait_if_paused()

            logging.info("check if stopped")
            if self.boxing_machine.stop_main_loop:
                logging.info("camera position: stop main loop")
                return (0,0,0)
            
            try:
                frames = self.pipeline.wait_for_frames()
                aligned_frames = self.align.process(frames)
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()
            except Exception as e:
                logging.error(f"error with camera: {e}")
                continue #go back to start


            #we only want colorframe, if no colorframe, go to start
            if not color_frame or not depth_frame:
                continue

            frame = np.asanyarray(color_frame.get_data())
            with self.frame_lock:  # Update last_frame safely
                self.last_frame = frame
            results = self.detector.detect_objects(frame.copy())

        
            if results is not None:
                for result in results:
                    for box in result.boxes:
                        bbox = box.xyxy[0].cpu().numpy()
                        bbox = [int(coord) for coord in bbox[:4]]
                        x_left = bbox[0]
                        y_middle = int((bbox[1] + bbox[3]) / 2)
                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]
                        depth = depth_frame.get_distance(x_left, y_middle)
                        label = self.labels[int(box.cls[0])]
                        length = max(width, height)
                        
                        #check for bad parts 
                        if 'bad' in label.lower() and box.conf > 0.6:
                            current_coordinates = (x_left, y_middle)
                            bbox = box.xyxy[0].cpu().numpy()
                            bbox = [int(coord) for coord in bbox[:4]]
                            if self.is_stable(current_coordinates):
                                # Draw a thick red bounding box for 'bad' objects
                                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 4)  # Red color, thickness 4
                                text = f'{label} ({box.conf.item():.2f})'
                                cv2.putText(frame, text, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                with self.frame_lock:
                                    self.last_frame = frame

                                self.boxing_machine.pause()
                                self.boxing_machine.interface.start_button_pressed()
                                self.boxing_machine.interface.update_status("bad placement on conveyor: please fix and resume")

                                logging.info("Bad position detected!")
                                self.robot.set_digital_output(2, True)  # Turn output 2 to True (gate goes up)
                                time.sleep(5)  # Wait for 5 seconds
                                self.robot.set_digital_output(2, False)  # Turn output 2 to False (gate goes down)
                                continue    #go to start of while loop, wait for new parts


                        #check for pickable parts
                        min_length = 170
                        if label == 'Green' or label == 'Rubber' or label == 'Small-Blue': min_length += 20
                        #small parts need more parts on belt, otherwise they bukkle up
                        
                        if box.conf > 0.8 and label in ['Big-Blue', 'Green', 'Holed', 'Rubber', 'Small-Blue'] and length >= min_length and width * height < 75000:
                            current_coordinates = (x_left, y_middle)
                            logging.info("part found, checking if stable")
                            if self.is_stable(current_coordinates):
                                logging.info("stable")
                                xd, yd = self.transform_coordinates(x_left, y_middle, depth)
                                logging.info(f"Detected (x, y, z): ({x_left}, {y_middle}, {depth}) conf: {box.conf}")

                                if xd > -0.750 and  xd < -0.42 and yd > -0.152 and yd < 0.090: #maximium x value for safety purposes
                                    # Draw box and label on the frame
                                    cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                                    cv2.circle(frame, (x_left, y_middle), 5, (0, 0, 255), -1)
                                    text = f'X: {x_left}, Y: {y_middle}, Z: {depth:.2f}m'
                                    cv2.putText(frame, text, (x_left, y_middle - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                                    text = f'{label} ({box.conf.item():.2f})'
                                    cv2.putText(frame, text, (bbox[0], bbox[1] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                                    not_found = False       #parts found, so not_found = false. this will stop the while looop

                                    with self.frame_lock:  # Update last_frame safely
                                        self.last_frame = frame
                                    return (xd, yd, label)
                                else:
                                    logging.error("part out of reach")
                            else:
                                logging.info("not stable")

        return (0, 0, 0)


    #checks if parts are stationary. only pick up parts if they are stationary
    def is_stable(self, current_coordinates):
        """Check stability separately for two rows."""
        x, y = current_coordinates

        # Determine which row the point belongs to
        if self.previous_coordinates_row1 is None or abs(y - self.previous_coordinates_row1[1]) < self.row_gap_threshold:
            row = "row1"
            prev_coords = self.previous_coordinates_row1
            last_time = self.last_stable_time_row1
        else:
            row = "row2"
            prev_coords = self.previous_coordinates_row2
            last_time = self.last_stable_time_row2

        # Stability check for the chosen row
        if prev_coords is None:
            self.update_row_state(row, current_coordinates)
            return False

        distance = np.linalg.norm(np.array(current_coordinates) - np.array(prev_coords))
        if distance > self.row_threshold:
            self.update_row_state(row, current_coordinates)
            return False

        # Ensure it has been stable for 0.3 seconds
        if time.time() - last_time >= 0.3:
            return True

        return False

    def update_row_state(self, row, coordinates):
        """Update the state for a specific row."""
        if row == "row1":
            self.previous_coordinates_row1 = coordinates
            self.last_stable_time_row1 = time.time()
        else:
            self.previous_coordinates_row2 = coordinates
            self.last_stable_time_row2 = time.time()


    def check_bad_part_placement(self, bad_confidence=0.6):
        time.sleep(0.3)
        #try 4 times
        tries = 4
        for i in range(tries):
            #get frames and check if we have a color frame
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                logging.error("No color frame captured")
                break

            #get frame as np array and get results from yolo model
            frame = np.asanyarray(color_frame.get_data())
            results = self.detector.detect_objects(frame)

            #update frame on user interface
            with self.frame_lock:
                self.last_frame = frame


            #process the yolo results
            if results is not None:
                for result in results:
                    for box in result.boxes:
                        bbox = box.xyxy[0].cpu().numpy()
                        bbox = [int(coord) for coord in bbox[:4]]
                        label = self.labels[int(box.cls[0])]
                        confidence = box.conf.item()

                        if 'bad' in label.lower() and confidence > bad_confidence:
                            logging.info("Bad position detected!")

                            # Draw a thick red bounding box for 'bad' objects
                            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 4)  # Red color, thickness 4
                            text = f'{label} ({box.conf.item():.2f})'
                            cv2.putText(frame, text, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        
                            #update frame for interface
                            with self.frame_lock:
                                self.last_frame = frame
                            return True  # Bad position detected
            return False  # No bad position detected      




    #stop display thread
    def stop_display_thread(self):
        self.display_thread_running = False




# runs yolo model and detects objects
class ObjectDetector:
    def __init__(self):
        '''setup yolo model'''
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_directory, "best.pt")
        self.model = YOLO(model_path).to('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = YOLO(model_path)
        self.labels = self.model.names

    def detect_objects(self, frame):
        results = self.model.predict(source=frame, verbose=False, show=False)
        return results

