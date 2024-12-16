import logging
from UR5E_control import URControl
import math
from camera_position import CameraPosition         #used for scanning the belt for detected parts
from pick_parts import *                           #used for picking parts from belt. needs x and y coordinates
from place_parts import *                          #used for getting place locations and placing parts in boxes


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



#function that connects to robot, sets TCP and moves robot to a safe start position
def setup_robot():
    #connect to robot
    robot.connect()

    #set toolframe
    tool_frame=[-47.5/1000,-140/1000,102.6/1000,math.radians(-1.2),math.radians(2),math.radians(-5)]
    robot.set_tool_frame(tool_frame=tool_frame)

    #set safe start pos
    start_pos = [-0.3968556411508649, 0.049047830881604054, 0.1, 2.1355663224764934, 2.288791439427752, -0.0]

    #move to start pos
    #robot.move_l(start_pos, 0.1, 0.1)


#main loop: gets partlocations, then starts a for loop to fill all the boxes
def main_loop():
    logging.info("in main loop")

    logging.info("get all packing positions")
    filled_boxes = pack_box.get_pack_pos()
     
    tot_parts = 5  # for testing, limit part amount
    count = 0

    box_index = 0
    for box in filled_boxes:
        for part in box:
            if count < tot_parts:
                logging.info(f"part: {part}")
                logging.info("do vision")  # -> result x and y for part
                camera = CameraPosition()
                x, y = camera.detect_object()  # get actual coordinates from vision
                
                logging.info("pickup part")
                pick_part.pick_parts(x, y)  # pick part at given location
                
                logging.info("place part")
                pack_box.place_part(part, box_index)  # place part at correct box and place. part contains location data in box. box_index is box 0 or 1 etc
                count += 1
        box_index += 1
 
    # end
    robot.stop_robot_control()

# initialize vision class
vision = Vision()

logging.info("START")

# setup robot
robot = URControl("192.168.0.1")  # defines robot.
setup_robot()  # connects to robot

# setup boxes and parts
# Create instances for box and part.
box = Box(total_boxes=2, box_pos=[(-224 / 1000, -588 / 1000, 100 / 1000), [237 / 1000, -588 / 1000, 100 / 1000]], box_size=(0.365, 0.365, 0.170))

# needs: part width, part length, part height
part = Part((0.187, 0.170, 0.013))

# initializes pack box class
pack_box = Pack_Box(box=box, part=part, robot=robot)

# initializes pick parts class
pick_part = Pick_parts(robot=robot)

# start main loop
if __name__ == '__main__':
    main_loop()
