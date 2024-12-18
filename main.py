import logging
from UR5E_control import URControl
from camera_position import CameraPosition         #used for scanning the belt for detected parts
from pick_parts import *                           #used for picking parts from belt. needs x and y coordinates
from place_parts import *                          #used for getting place locations and placing parts in boxes
import keyboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
   



#main loop: gets partlocations, then starts a for loop to fill all the boxes
def main_loop():
    logging.info("in main loop")

    logging.info("get all packing positions")
    filled_boxes = pack_box.get_pack_pos()
     
    tot_parts = 3  # for testing, limit part amount
    count = 0

    box_index = 0
    for box in filled_boxes:
        for part in box:
            if count < tot_parts:
                logging.info(f"part: {part}")
                keyboard.wait('space')
                logging.info("do vision, first wait for space")  # -> result x and y for part
                x, y = camera.detect_object_without_start()  # get actual coordinates from vision
                 
                logging.info("pickup part")
                #pick_part.pick_parts(x, y)  # pick part at given location
                
                logging.info("place part")
                #pack_box.place_part(part, part_type='wide')  # place part at correct box and place. part contains location data in box. box_index is box 0 or 1 etc
                count += 1
        box_index += 1
 
    # end
    robot.stop_robot_control()
    camera.pipeline.stop()



logging.info("START")

'''SETUP ROBOT'''
# setup robot
robot = URControl("192.168.0.1")  # defines robot.
robot.connect()


'''SETUP PLACE BOX, PACK BOX AND PART DEFINITIONS'''
base_z = -12/1000
#neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z)
box = Box(total_boxes=2, box_pos=[(-230/1000, -575/1000, base_z), [237/1000,-588/1000, base_z]], box_size=(0.365, 0.365, 0.180 ))

#needs: part width, part length, part height
part = Part((0.187, 0.170, 0.009))

# initializes pack box class
pack_box = Pack_Box(box=box, part=part, robot=robot)

# initializes pick parts class
pick_part = Pick_parts(robot=robot)


''' SETUP VISION SYSTEM'''
# initialize vision camera class
camera = CameraPosition(robot=robot)



# start main loop
if __name__ == '__main__':
    main_loop()
