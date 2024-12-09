import logging
from UR5E_control import URControl
import math
import pyrealsense2 as rs

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



def setup_robot():
    #connect to robot
    robot = URControl("192.168.0.1")
    robot.connect()


    #set toolframe
    tool_frame=[-47.5/1000,-140/1000,102.6/1000,math.radians(-1.2),math.radians(2),math.radians(-5)]
    robot.set_tool_frame(tool_frame=tool_frame)

    #set safe start pos
    start_pos = [-0.3968556411508649, 0.049047830881604054, 0.1, 2.1355663224764934, 2.288791439427752, -0.0]
    fold_up_pos = [0.21806621866470055, -0.08845418646768148, 0.5716754446825703, 0.2011446368010403, -1.0833366225923702, 2.7864552788165944]

    #move to start pos
    robot.move_l(start_pos, 0.1, 0.1)


def setup_camera():
     try:
        # Configure RealSense pipeline
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start the camera stream
        pipeline.start(config)
        logging.info("succesfully connected to camera")

     except Exception as e:
        logging.error(f"problem connecting to camera: {e}")



def start():
    #setup_robot()
    setup_camera()




def main_loop():
    while True:
            pass
    
    #robot.stop_robot_control()




if __name__ == "main":
    start()