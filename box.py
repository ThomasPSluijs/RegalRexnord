import logging
from math import floor
import math
from UR5E_control import URControl

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



#class that stores information for the boxes:
#total boxes, box centers(in x,y) box bottom z, boxsize
class Box:
    def __init__(self, total_boxes, box_pos, box_size):
        self.total_boxes = total_boxes
        self.box_centers = box_pos # center x, center y, bottom z
        self.box_size = box_size  # (length, width, height)


#class that stores information about parts: 
#part size x, y and z
class Part:
    def __init__(self, product_size):
        self.product_size = product_size
        self.part_size_x = product_size[0]
        self.part_size_y = product_size[1]
        self.part_size_z = product_size[2]



#class that determines all the coordinates for the parts in the boxes. 
#in total 4 parts per box, two rotated 90 degrees
#total parts in height gets calculated
class Pack_Box:
    def __init__(self, box, part):
        #get box info
        self.box = box
        self.box_length, self.box_width, self.box_height = self.box.box_size
        
        #get part info
        self.part = part
        self.part_length = self.part.part_size_x
        self.part_width = self.part.part_size_y
        self.part_height = self.part.part_size_z


        #array with boxes and parts locations
        self.filled_boxes = []


    #get al packing positions in the boxes. These are the center coordinates of the parts, rotations of the parts and the z_height of the parts
    def get_pack_pos(self):
        #for loop to go throug boxes and fill boxes 1 by 1
        for box_index in range(self.box.total_boxes):
            #get box center
            box_center = self.box.box_centers[box_index]
            logging.info(f"Packing in Box {box_index + 1} at center {box_center}")

            #check total z parts per box
            total_z_parts = floor(self.box_height/self.part_height)
            logging.info(f"total z parts: {total_z_parts}")

            #set start z_pos at bototm of box
            z_pos = box_center[2]

            #array for adding part locations for this box
            part_positions_box = []

            #for loop to go through total z parts to fill a box
            for z in range(total_z_parts):
                #array to place four parts per layer
                for i in range(4):  # Only 4 parts for now
                    if i == 0:
                        # First part (top left)
                        x_pos = box_center[0] - self.box_length / 2 + self.part_length / 2
                        y_pos = box_center[1] - self.box_width / 2 + self.part_width / 2
                        rotation=0
                    elif i == 1:
                        # Second part (top right)
                        x_pos = box_center[0] + self.box_length / 2 - self.part_width / 2
                        y_pos = box_center[1] - self.box_width / 2 + self.part_length / 2
                        rotation=90
                    elif i == 2:
                        # Third part (bottom left)
                        x_pos = box_center[0] - self.box_length / 2 + self.part_width / 2
                        y_pos = box_center[1] + self.box_width / 2 - self.part_length / 2
                        rotation=270
                    elif i == 3:
                        # Fourth part (bottom right)
                        x_pos = box_center[0] + self.box_length / 2 - self.part_length / 2
                        y_pos = box_center[1] + self.box_width / 2 - self.part_width / 2
                        rotation=180

                    # Store the positions
                    part_positions_box.append((x_pos, y_pos, z_pos, rotation))

                #layer has been filled, increase z_pos for next layer    
                z_pos += self.part_height

            #add filled box to total boxes
            self.filled_boxes.append(part_positions_box)

        return self.filled_boxes
    


    def place_part(self, part_position, box_index):
        box_center = self.box.box_centers[box_index]
        logging.info(f"Box center: {box_center}")

        # TCP offsets
        pickup_tcp = [-47.5/1000,-140/1000,102.6/1000,math.radians(-1.2),math.radians(2),math.radians(-5)]  #edge of part (x=centerpart, y=edge)
        placement_tcp = [-47.5/1000,-46.5/1000,102.6/1000,math.radians(-1.2),math.radians(2),math.radians(-5)]  #center of part (x=center,y=center)


        # Step 1: Set TCP to plcament tcp for rotating about z axis and x/y movement
        logging.info(f"Setting TCP to pickup position: {placement_tcp}")
        robot.set_tool_frame(placement_tcp)


        #step 2: move to proper z height
        robot.get_tcp_pos()
        cur_pos[2] = 0.3
        robot.move_l(cur_pos, 0.1, 0.1)


        # Step 2: Move above the box center
        cur_pos = robot.get_tcp_pos()  # Get current robot position (x, y, z)
        cur_pos[0] = box_center[0]     # Align x position with box center
        cur_pos[1] = box_center[1]     # Align y position with box center
        cur_pos[2] = 0.3               # Set a safe z height above the box
        logging.info(f"Move to box center: {cur_pos}")
        robot.move_l(cur_pos, 0.1, 0.1)


        # Step 3: Adjust rotation around the Z-axis
        rotation_angle = part_position[3]  # pick rotation from part info. convert to radians
        logging.info(f"Set rotation around Z-axis to: {rotation_angle}")
        #robot.set_tcp_rotation(0, 0, rotation_angle)
        rotate = [0,0,0,math.radians(0),math.radians(0),math.radians(rotation_angle)]
        pose1 = robot.get_tcp_pos()
        pose2 = rotate
        result_pose = robot.pose_trans(pose1, pose2)
        robot.move_l(result_pose, 0.5, 0.5)

        
        # Step 4: Move to the desired Z height for placement
        cur_pos[2] = part_position[2]  # Set Z height to target position within the box
        logging.info(f"Move to placement height: {cur_pos}")
        robot.move_l(cur_pos, 0.1, 0.1)

        
        # Step 5: Move to the part's target X, Y position
        cur_pos[0] = part_position[0]  # Set X to the part's target position
        cur_pos[1] = part_position[1]  # Set Y to the part's target position
        logging.info(f"Move to part placement position: {cur_pos}")
        robot.move_l(cur_pos, 0.1, 0.1)

        '''
        # Step 6: Slide part into place (rotates about x axis)
        logging.info("Performing final placement adjustments")
        rotate_x = [0,0,0,math.radians(-15),math.radians(0),math.radians(0)]
        robot.set_tool_frame(pickup_tcp)
        pose1 = robot.get_tcp_pos()
        pose2 = rotate_x
        result_pose = robot.pose_trans(pose1, pose2)
        robot.move_l(result_pose, 0.5, 0.5)

        #step 7: depending on rotation, move x or y
        robot.set_tool_frame(pickup_tcp)
        if rotation_angle == 0:
            #move x positive
            offset= [187/1000,0,0,0,0,0]
        elif rotation_angle == 90:
            #move y positive
            offset= [0,187/1000,0,0,0,0]
        elif rotation_angle == 180:
            #move x negative
            offset= [-187/1000,0,0,0,0,0]
        elif rotation_angle == 270:
            #move y negatie
            offset= [0,-187/1000,0,0,0,0]
        robot.move_l(offset, 0.1, 0.1)

        # Step 7: Return above the box with pickup_tcp
        logging.info(f"Resetting TCP to pickup position: {pickup_tcp}")
        robot.set_tcp(pickup_tcp)
        cur_pos = robot.get_tcp_pos()
        cur_pos[2] = 0.2  # Return to a safe Z height above the box
        logging.info(f"Return above the box: {cur_pos}")
        robot.move_l(cur_pos, 0.1, 0.1)

        # Step 8: Reset rotation to level position
        logging.info("Reset rotation to level position (0 degrees)")
        robot.set_tcp_rotation(0, 0, 0) '''



robot = URControl("192.168.0.1")
robot.connect()

#set toolframe
tool_frame=[-47.5/1000,-140/1000,102.6/1000,math.radians(-1.2),math.radians(2),math.radians(-5)]
robot.set_tool_frame(tool_frame=tool_frame)

#move to safe z height
cur_pos = robot.get_tcp_pos()
if cur_pos: cur_pos[2] = 0.4
if cur_pos: robot.move_l(cur_pos, 0.1, 0.1)

#set safe start pos
start_pos = [-0.3968556411508649, 0.049047830881604054, 0.3, 2.1355663224764934, 2.288791439427752, -0.0]

logging.info(f"current tcp pos: {robot.get_tcp_pos()}")
robot.move_l(start_pos, 0.1, 0.1) 


# Create instances for box and part.
#neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z)
box = Box(total_boxes=2, box_pos=[(-224/1000, -588/1000, 100/1000), [237/1000,-588/1000, 100/1000]], box_size=(0.365, 0.365, 0.170))
    #box z should be 30/1000. 100 is used for safe testing


#needs: part width, part length, part height
part = Part((0.187, 0.170, 0.013))

# Initialize Pack_Box and get packing positions
pack_box = Pack_Box(box=box, part=part)
filled_boxes = pack_box.get_pack_pos()

tot_parts = 5
count = 0

box_index = 0
for box in filled_boxes:
    for part in box:
        if count < tot_parts:
            logging.info(f"part: {part}")
            logging.info("pickup part")
            logging.info("place part")
            #pack_box.place_part(part, box_index)
            count  += 1
    box_index += 1

robot.stop_robot_control()
