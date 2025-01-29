import logging
import threading
from UR5E_control import URControl
from camera_position import CameraPosition         # used for scanning the belt for detected parts
from pick_parts import *                           # used for picking parts from belt. needs x and y coordinates
from place_parts import *                          # used for getting place locations and placing parts in boxes
from configuration import *


             
#main class for the boxingmachine. this class will be controlled via the user interface
class BoxingMachine:
    def __init__(self, robot_ip,interface):
        self.interface = interface
        self.robot = URControl(robot_ip)
        self.robot.connect()

        logging.info(f"tcp pos: {self.robot.get_tcp_pos()}")
 
   
        '''SETUP PLACE BOX, PACK BOX AND PART DEFINITIONS'''
        base_z = 0/1000
        #neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z)
        self.box = Box(total_boxes=2, box_pos=[(-215/1000, 533.8/1000, base_z), [220/1000,525.8/1000, base_z]], box_size=(0.365, 0.365, 0.180 )) #should be 0.180
        #needs: part  width, part length, part height
        self.part = Part((0.184, 0.170, 0.01260))
 
   
        # Initialize pack box and pick parts classes
        self.pack_box = Pack_Box(box=self.box, part=self.part, robot=self.robot, boxing_machine=self)
        self.pick_part = Pick_parts(robot=self.robot, boxing_machine=self)

        # Initialize vision camera class
        self.camera = CameraPosition(robot=self.robot, boxing_machine=self)

        # Pause control using threading Event
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused

        self.current_part_number = 1
        self.last_part_box_0 = 0
        self.last_part_box_1 = 0
        self.total_parts = 0
        self.placements = 0
        self.current_box = 0
        self.boxes_are_full = False
        self.thread_lock = threading.Lock()

        self.stop_main_loop = False

    def pause(self):
        logging.info("Pausing operations...")
        self.pause_event.clear()

    def resume(self):
        logging.info("Resuming operations...")
        self.pause_event.set()

    def packing_mode(self):
        logging.info("move to packing mode")
        self.robot.set_tcp(pickup_tcp)
        logging.info(self.robot.get_tcp_pos())
        #first move to safe z pos
        target_position = [-0.3315005050673199, 0.08452186932980371, -0.07197736577529477, 2.166779782637334, 1.8998528338341554, 0.5314223354981934]
        self.robot.move_l(target_position, 0.3, 0.3)

    def normal_mode(self):
        logging.info("move to normal working mode")
        #move to take pic pos
        pickup_tcp = [-47.5/1000,-140/1000,135/1000,0,0,0]  #edge of part (x=centerpart, y=edge)
        self.robot.set_tcp(pickup_tcp)
        target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
        self.robot.move_l(target_position, 0.3, 0.3)

    def wait_if_paused(self):
        #logging.info("Waiting if paused...")
        if self.interface.stopped: 
            logging.info("interface stopped, stop main loop")
            self.stop_main_loop = True
            self.interface.stopped = False
            return
        self.pause_event.wait()  # Block if paused

    def start(self):
        logging.info("Starting Boxing Machine...")
        self.main_loop()

    def stop(self):
        logging.info("Stopping robot control and camera pipeline...")
        self.robot.stop_robot_control()
        self.camera.pipeline.stop()
 
 
    #checks parttype and adjusts part size y 
    def check_part_type(self, part_type):
        if part_type == 'Big-Blue':
            self.part.part_size_z = 0.01260
            self.pack_box.part_height = self.part.part_size_z
        elif part_type == 'Green':
            self.part.part_size_z = 0.009
            self.pack_box.part_height = self.part.part_size_z
        elif part_type == 'Holed':
            self.part.part_size_z = 0.0085 
            self.pack_box.part_height = self.part.part_size_z
        elif part_type == 'Rubber':
            self.part.part_size_z = 0.01055
            self.pack_box.part_height = self.part.part_size_z
        elif part_type == 'Small-Blue':
            self.part.part_size_z = 0.009
            self.pack_box.part_height = self.part.part_size_z



    def initialize_main_loop(self):
        #first move to safe normal working pos
        self.normal_mode()

        #initialization box position check
        box_orientations = {
            'box_0': 'horizontal',
            'box_1': 'horizontal'
        }
        box_orientations = self.camera.initialize_position()
        logging.info(f"box orientations: {box_orientations}")

        #check part type on belt
        x, y, item_type = self.camera.detect_pickable_parts(slow=False)  # Get actual coordinates from vision
        self.check_part_type(item_type)
        return item_type, box_orientations

  
    #main loop that fills all available boxes
    def main_loop(self):
        self.placements = 0
        run_mode = 1        #0 is normal mode, 1 is only packing
        self.last_part_box_0 = 0
        self.last_part_box_1 = 0

        logging.info("In main loop")

        item_type = 'Big-Blue'
        box_orientations = {
            'box_0': 'horizontal',
            'box_1': 'horizontal'
        }
        if run_mode == 0:
            #pass
            item_type, box_orientations = self.initialize_main_loop()


        #get packing positions
        filled_boxes = self.pack_box.get_pack_pos(item_type)


        #start for loop to go through all packing positions and fill the boxes
        self.boxes_are_full = False
        box_index = 0
        for box in filled_boxes:
            if self.stop_main_loop:  # Check if stop signal is set
                logging.info("Stopping main loop due to stop signal.")
                self.stop_main_loop = False
                return  # Exit the function immediately

            with self.thread_lock:
                self.current_box = box_index


            for part in box:
                if box_index >= 0 and part['layer_number'] >= 0:
                    if self.stop_main_loop:  # Check if stop signal is set
                        logging.info("Stopping main loop due to stop signal.")
                        self.stop_main_loop = False
                        return  # Exit the function immediately

                    logging.info(f"Processing part: {part}")

                    with self.thread_lock:
                        self.current_part_number = part['part_number']
                        self.total_parts = len(box)

                    
                    self.wait_if_paused()
                    if self.stop_main_loop:  # Check after potentially long operations
                        self.stop_main_loop = False
                        logging.info("Stopping main loop due to stop signal.")
                        return

                    #check pickable parts
                    if run_mode == 0:
                        #logging.info("check pickable parts with vision")
                        x, y, item_type = self.camera.detect_pickable_parts()  # Get actual coordinates from vision
                        logging.info(f"x: {x}   y: {y}   item_type: {item_type}")

                    
                    if self.stop_main_loop:  # Check after potentially long operations
                        self.stop_main_loop = False
                        logging.info("Stopping main loop due to stop signal.")
                        return
                    self.wait_if_paused()
                    if self.stop_main_loop:  # Check after potentially long operations
                        self.stop_main_loop = False
                        logging.info("Stopping main loop due to stop signal.")
                        return


                    #pickup parts
                    if run_mode == 0:
                        #logging.info("pickup part")
                        #pass
                        self.pick_part.pick_parts(x, y, part_type=item_type)  # Uncomment when ready


                    self.wait_if_paused()
                    if self.stop_main_loop:  # Check after potentially long operations
                        self.stop_main_loop = False
                        logging.info("Stopping main loop due to stop signal.")
                        return



                    #place parts
                    #logging.info("Place part")
                    box_orientation = box_orientations.get(f'box_{box_index}')  # Get the orientation for the current box
                    self.pack_box.place_part(part, part_type=item_type, box_rotation=box_orientation)  # Pass the box orientation

                    with self.thread_lock:
                        self.placements += 1
                        if box_index == 0:
                            self.last_part_box_0 = part
                        elif box_index == 1:
                            self.last_part_box_1 = part

                    

            box_index += 1

        with self.thread_lock:
            self.boxes_are_full = True
            
        self.stop_main_loop = False