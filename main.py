import logging
import threading
from UR5E_control import URControl
from camera_position import CameraPosition         # used for scanning the belt for detected parts
from pick_parts import *                           # used for picking parts from belt. needs x and y coordinates
from place_parts import *                          # used for getting place locations and placing parts in boxes
import keyboard
import cv2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



#main class for the boxingmachine. this class will be controlled via the user interface
class BoxingMachine:
    def __init__(self, robot_ip):
        self.robot = URControl(robot_ip)
        self.robot.connect()


        '''SETUP PLACE BOX, PACK BOX AND PART DEFINITIONS'''
        base_z = -12/1000
        #neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z)
        box = Box(total_boxes=2, box_pos=[(-230/1000, -575/1000, base_z), [237/1000,-588/1000, base_z]], box_size=(0.365, 0.365, 0.180 ))
        #needs: part width, part length, part height
        part = Part((0.187, 0.170, 0.009))

 
        # Initialize pack box and pick parts classes
        self.pack_box = Pack_Box(box=box, part=part, robot=self.robot)
        self.pick_part = Pick_parts(robot=self.robot)

        # Initialize vision camera class
        self.camera = CameraPosition(robot=self.robot)

        # Pause control using threading Event
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused

    def pause(self):
        logging.info("Pausing operations...")
        self.pause_event.clear()

    def resume(self):
        logging.info("Resuming operations...")
        self.pause_event.set()

    def packing_mode(self):
        logging.info("move to packing mode")

    def normal_mode(self):
        logging.info("move to normal working mode")

    def wait_if_paused(self):
        logging.info("Waiting if paused...")
        self.pause_event.wait()  # Block if paused

    def start(self):
        logging.info("Starting Boxing Machine...")
        self.main_loop()

    def stop(self):
        logging.info("Stopping robot control and camera pipeline...")
        self.robot.stop_robot_control()
        self.camera.pipeline.stop()

    def main_loop(self):
        logging.info("In main loop")
        logging.info("Get all packing positions")
        filled_boxes = self.pack_box.get_pack_pos()

        tot_parts = 3  # For testing, limit part amount
        count = 0

        box_index = 0
        for box in filled_boxes:
            for part in box:
                if count < tot_parts:
                    logging.info(f"Processing part: {part}")

                    self.wait_if_paused()  # Pause-safe

                    logging.info("Do vision, first wait for space")
                    keyboard.wait('space')
                    x, y = self.camera.detect_object_without_start()  # Get actual coordinates from vision

                    #logging.info(self.camera.last_frame)
    
                    logging.info("Pickup part")
                    self.wait_if_paused()  # Pause-safe
                    # self.pick_part.pick_parts(x, y)  # Uncomment when ready
                    
                    logging.info("Place part")
                    self.wait_if_paused()  # Pause-safe
                    # self.pack_box.place_part(part, part_type='wide')  # Uncomment when ready

                    count += 1
            box_index += 1

        self.stop()  # End operations
  
 
def display_frames(camera_position):
    logging.info("Starting display thread...")
    frame = None
    while camera_position.display_thread_running:
        with camera_position.frame_lock:  # Access the frame safely
            if camera_position.last_frame is not None:
                frame = camera_position.last_frame.copy()
            #logging.info(f"frame: {frame}")
            #logging.info(frame)
        if frame is not None:
            cv2.imshow("RealSense Camera Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                break
        time.sleep(0.03)  # Limit display thread to ~30 FPS
    logging.info("Stopping display thread...")
    cv2.destroyAllWindows()


 

if __name__ == '__main__':
    logging.info("START")
    
    # Define configurations
    robot_ip = "192.168.0.1"

    # Create and start BoxingMachine
    machine = BoxingMachine(robot_ip)

    # Start in a separate thread to allow pause/resume control
    threading.Thread(target=machine.start, daemon=True).start()

    # Start display thread
    display_thread = threading.Thread(target=display_frames, args=(machine.camera,), daemon=True)
    display_thread.start() 

    # Listen for pause and resume commands
    while True:
        key = keyboard.read_event().name
        if key == 'p':  # Pause
            machine.pause()
        elif key == 'r':  # Resume
            machine.resume()
        elif key == 'q':  # Quit
            logging.info("Quitting...")
            break

machine.camera.stop_display_thread()
display_thread.join()
