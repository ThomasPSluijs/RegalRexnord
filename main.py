import logging
from UR5E_control import URControl
import math
#import pyrealsense2 as rs

from pick_parts import *
from box import *

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

    logging.info(f"current tcp pos: {robot.get_tcp_pos()}")

    #move to start pos
    #robot.move_l(start_pos, 0.1, 0.1)


#function that sets up camera
'''def setup_camera():
     try:
        # Configure RealSense pipeline
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start the camera stream
        pipeline.start(config)
        logging.info("succesfully connected to camera")

     except Exception as e:
        logging.error(f"problem connecting to camera: {e}")'''




#function to take picture: first move to take pic pos, then take picture etc
def take_picture():
    take_pick_pos = [-0.7891716074470788, -0.05873062914748386, 0.48092687604716666, 2.1252209148236973, 2.2821904119092338, 0.00206831311019891]
    robot.move_l(take_pick_pos, 1, 1)

    parts_pos = [-0.08793947845697403, 0.017009420320391655, 0.05, 2.1252209148236973, 2.2821904119092338, 0.00206831311019891]
    robot.move_l(parts_pos, 0.05)



def main_loop():
    while True:
            pass
    
    #robot.stop_robot_control()


logging.info("START")


''' setup robot '''
robot = URControl("192.168.0.1")   #defines robot. 
setup_robot()                      #connects to robot


''' setup boxes and parts '''
# Create instances for box and part.
#neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z) #box z should be 30/1000. 100 is used for safe testing
box = Box(total_boxes=2, box_pos=[(-224/1000, -588/1000, 100/1000), [237/1000,-588/1000, 100/1000]], box_size=(0.365, 0.365, 0.170))

#needs: part width, part length, part height
part = Part((0.187, 0.170, 0.013))


''' initializes pack box class '''
# Initialize Pack_Box and get packing positions
pack_box = Pack_Box(box=box, part=part)


''' initializes pick parts class '''
pick_part = Pick_parts(robot=robot)


main_loop()