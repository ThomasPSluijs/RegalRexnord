import logging
import threading
from UR5E_control import URControl
from camera_position import CameraPosition         # used for scanning the belt for detected parts
from pick_parts import *                           # used for picking parts from belt. needs x and y coordinates
from place_parts import *                          # used for getting place locations and placing parts in boxes
import keyboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



#main class for the boxingmachine. this class will be controlled via the user interface
class BoxingMachine:
    def __init__(self, robot_ip, box_config, part_config):
        self.robot = URControl(robot_ip)
        self.robot.connect()

        # Setup box and part configurations
        self.base_z = -12 / 1000
        self.box = Box(**box_config)
        self.part = Part(**part_config)

        # Initialize pack box and pick parts classes
        self.pack_box = Pack_Box(box=self.box, part=self.part, robot=self.robot)
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
                    
                    logging.info("Pickup part")
                    self.wait_if_paused()  # Pause-safe
                    # self.pick_part.pick_parts(x, y)  # Uncomment when ready
                    
                    logging.info("Place part")
                    self.wait_if_paused()  # Pause-safe
                    # self.pack_box.place_part(part, part_type='wide')  # Uncomment when ready

                    count += 1
            box_index += 1

        self.stop()  # End operations




if __name__ == '__main__':
    logging.info("START")
    
    # Define configurations
    robot_ip = "192.168.0.1"
    box_config = {
        "total_boxes": 2,
        "box_pos": [
            (-230 / 1000, -575 / 1000, -12 / 1000), 	    #x center, y center, z 0 (bottom of box)
            (237 / 1000, -588 / 1000, -12 / 1000)           #x center, y center, z 0 (bottom of box)
        ],
        "box_size": (0.365, 0.365, 0.180),                  #width, lengt, height
    }
    part_config = {
        "part_dimensions": (0.187, 0.170, 0.009),           #only z should change (via vision if possible)
    }

    # Create and start BoxingMachine
    machine = BoxingMachine(robot_ip, box_config, part_config)

    # Start in a separate thread to allow pause/resume control
    threading.Thread(target=machine.start, daemon=True).start()

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
