import logging
from math import floor
import math
from UR5E_control import URControl
import time
import keyboard

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
    def __init__(self, box, part, robot):
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
        
        #robot
        self.robot = robot

   
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

            margin_y = 9/1000 #5mm marge y en x
            margin_x = 7/1000
 
            #for loop to go through total z parts to fill a box
            for z in range(total_z_parts):
                #array to place four parts per layer
                for i in range(4):  # Only 4 parts for now
                    if i == 0:
                        # First part (top left)
                        x_pos = box_center[0] - self.box_length / 2 + self.part_length / 2 + 0.012
                        y_pos = box_center[1] - self.box_width / 2 + self.part_width / 2 +0.000
                        rotation=0
                    elif i == 1:
                        # Second part (top right)
                        x_pos = box_center[0] + self.box_length / 2 - self.part_width / 2 + 0.000  
                        y_pos = box_center[1] - self.box_width / 2 + self.part_length / 2 + 0.008
                        rotation=-90
                    elif i == 2:        #works
                        # Third part (bottom left)
                        x_pos = box_center[0] - self.box_length / 2 + self.part_width / 2 + 0.012
                        y_pos = box_center[1] + self.box_width / 2 - self.part_length / 2 - 0.000
                        rotation=90
                    elif i == 3:
                        # Fourth part (bottom right)
                        x_pos = box_center[0] + self.box_length / 2 - self.part_length / 2 - 0.006
                        y_pos = box_center[1] + self.box_width / 2 - self.part_width / 2 - 0.012
                        rotation=180
   
                    # Store the positions
                    part_positions_box.append((x_pos, y_pos, z_pos, rotation))

                #layer has been filled, increase z_pos for next layer    
                z_pos += self.part_height

            #add filled box to total boxes
            self.filled_boxes.append(part_positions_box)

        return self.filled_boxes
    


    #place parts
    #1: move to proper z height (above box)
    #2: move above box center
    #3: move down (20mm above needed z level)
    #4: rotate tool
    #5: move to target x and y position
    #6: move to desired height
    #7: rotate ardound x axis of EOAT so parts can slide out
    #8: move x or y so parts can slide of
    #9: return to above box
    #10: move to safe x and y
    def place_part(self, part_position, box_index):
        #fast and slow speeds and accelerations. fast for general movements, slow for special movements. 
        speed_fast = 0.5
        acc_fast = 1

        speed_slow = 0.1   
        acc_slow = 0.5

        box_center = self.box.box_centers[box_index]
        logging.info(f"Box center: {box_center}")

        # TCP offsets
        pickup_tcp = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]  #edge of part (x=centerpart, y=edge)
        placement_tcp = [-47.5/1000,-52.5/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]  #center of part (x=center,y=center)




        start_rotation = [2.213, 2.215, -0.013]

        self.robot.set_tool_frame(pickup_tcp)
        start_pos = [-0.3968556411508649, 0.049047830881604054, 0.3, 2.213, 2.215, -0.013]  #only for testing
        self.robot.move_l(start_pos, speed_fast, acc_fast) 

        z_above_box = 0.3

        #step 1: move to proper z height (currently pos: just picked up parts)
        self.robot.set_tool_frame(placement_tcp)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[2] = z_above_box
        self.robot.move_l(cur_pos, speed_fast, acc_fast)



        # Step 2: Move above the box center and set proper rotation
#        self.robot.set_tool_frame(placement_tcp)
        cur_pos = [0,0,0,0,0,0] #self.robot.get_tcp_pos()  # Get current robot position 
        cur_pos[0] = box_center[0]     # Align x position with box center
        cur_pos[1] = box_center[1]     # Align y position with box center
        cur_pos[2] = z_above_box               # Set a safe z height above the box
        cur_pos[3] = start_rotation[0]
        cur_pos[4] = start_rotation[1]
        cur_pos[5] = start_rotation[2]
        logging.info(f"Step 2: Move to box center: {cur_pos}")
        self.robot.move_l(cur_pos, speed_fast, acc_fast)
        
        
        # Step 3: Move to the desired Z height for placement + 20mm
#        self.robot.set_tool_frame(placement_tcp)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[2] = part_position[2] + 40/1000  # Set Z height to target position within the box
        logging.info(f"Step 3: Move to placement height: {cur_pos}")
        self.robot.move_l(cur_pos, speed_slow, acc_slow)

    
        # Step 4: Adjust rotation around the Z-axis
        #WARNING: when using 180 degrees, it randomly rotates to 180 or -180, you will get to the same point but 
        # when rotating back the joint limit can be reached. this fucks up the program
#        self.robot.set_tool_frame(placement_tcp)

        #when angle=180, first do + 10 then do + 170
        rotation_angle = part_position[3]  # pick rotation from part info. convert to radians
        logging.info(f"Step 4: Set rotation around Z-axis to: {rotation_angle}")
        rotations = 1
        if rotation_angle == 180: 
            rotation_angle = 10
            rotations = 2
        for rotation in range(rotations):
            rotate = [0,0,0,math.radians(0),math.radians(0),math.radians(rotation_angle)]
            pose1 = self.robot.get_tcp_pos()
            pose2 = rotate
            result_pose = self.robot.pose_trans(pose1, pose2)
            self.robot.move_l(result_pose, speed_slow, acc_slow)
            if rotations == 2:
                rotation_angle = 170
        if rotations == 2: rotation_angle = 180
        
        
        # Step 5: Move to the part's target X, Y position
#        self.robot.set_tool_frame(placement_tcp)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[0] = part_position[0]  # Set X to the part's target position
        cur_pos[1] = part_position[1]  # Set Y to the part's target position
        logging.info(f"Step 5: Move to part placement position: {cur_pos}")
        self.robot.move_l(cur_pos, speed_slow, acc_slow)


        #step 5.1: rotate a bit about x of tcp
        rotate_x = [0,0,0,math.radians(-5),math.radians(0),math.radians(0)]
        self.robot.set_tool_frame(pickup_tcp)
        pose1 = self.robot.get_tcp_pos()
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, speed_slow, acc_slow)

    
        # Step 6: Move to the desired Z height for placement
#        self.robot.set_tool_frame(placement_tcp)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[2] = part_position[2] + 0.00  # Set Z height to target position within the box
        logging.info(f"Step 6: Move to placement height: {cur_pos}")
        self.robot.move_l(cur_pos, speed_slow, acc_slow)


        # Step 7: Slide part into place (rotates about x axis)
        logging.info("Step 7: Performing final placement adjustments")
        rotate_x = [0,0,0,math.radians(-20),math.radians(0),math.radians(0)]
        self.robot.set_tool_frame(pickup_tcp)
        pose1 = self.robot.get_tcp_pos()
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, speed_slow, acc_slow)

     
        #step 8: depending on rotation, move x or y
        logging.info("Step 8: depending on rotation, move x or y")
        self.robot.set_tool_frame(pickup_tcp)
        offset=175    #should be 170
        z_offset = 7
        if rotation_angle == 0:
            #move x positive
            offset= [offset/1000,0,z_offset/1000,0,0,0]
        elif rotation_angle == -90:
            #move y positive
            offset= [0,offset/1000,z_offset/1000,0,0,0]
        elif rotation_angle == 90:
            #move y negative
            offset= [0,-offset/1000,z_offset/1000,0,0,0]  
        elif rotation_angle == 180:
            #move y negatie
            offset= [-offset/1000,0,z_offset/1000,0,0,0]
        self.robot.move_add_l(offset, speed_slow, acc_slow) 

           
        # Step 9: Return above the box with pickup_tcp
        logging.info(f"Step 9: Resetting TCP to pickup position: {pickup_tcp}")
#        self.robot.set_tool_frame(pickup_tcp)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[2] = z_above_box  # Return to a safe Z height above the box
        self.robot.move_l(cur_pos, speed_fast, acc_fast)   

        #step 9.1: rotate a bit back if rotationangle=180
        if rotation_angle == 180:
            self.robot.set_tool_frame(placement_tcp)
            rotation_angle = -25
            rotate = [0,0,0,math.radians(0),math.radians(0),math.radians(rotation_angle)]
            pose1 = self.robot.get_tcp_pos()
            pose2 = rotate
            result_pose = self.robot.pose_trans(pose1, pose2)
            self.robot.move_l(result_pose, speed_slow, acc_slow)



        #step 10: move to safe x and y position
        logging.info("Step 10: Move to safe x and y")
        self.robot.set_tool_frame(placement_tcp)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[0] = -0.35
        cur_pos[1] = -0.30
        self.robot.move_l(cur_pos, speed_fast, acc_fast)


        self.robot.set_tool_frame(pickup_tcp)
        start_pos = [-0.3968556411508649, 0.049047830881604054, 0.3, 2.213, 2.215, -0.013]
        self.robot.move_l(start_pos, speed_fast, acc_fast) 

        #step 11:
        #done
        #probably move to take pic pos

    
    #put it in main loop
         
    #goes throug boxes and parts, then calls 'pickup part', 'place part'
    
    def pack_box(self):
        self.get_pack_pos()     #gets packing locations

        tot_parts = 12   #for testing, limit part amount
        count = 0
 
        box_index = 0
        for box in self.filled_boxes:
            for part in box:
                if count < tot_parts:
                    logging.info(f"part: {part}")
                    logging.info("pickup part")
                    logging.info("place part")
                    if count == 2: pack_box.place_part(part, box_index)
                    keyboard.wait('space')
                    
                    count  += 1
            box_index += 1



'''
code below is to test this file. should be commented.
'''


robot = URControl("192.168.0.1")
robot.connect()

if robot.rtde_ctrl and robot.rtde_rec:
    #set toolframe
    tool_frame=[-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]
    robot.set_tool_frame(tool_frame=tool_frame)

    #move to safe z height
    cur_pos = robot.get_tcp_pos()
    cur_pos[2] = 0.3
    robot.move_l(cur_pos, 0.1, 0.1)
           
    # Create instances for box and part.
    #neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z)
    box = Box(total_boxes=2, box_pos=[(-230/1000, -575/1000, -12/1000), [237/1000,-588/1000, -12/1000]], box_size=(0.365, 0.365, 0.170))
  
    #needs: part width, part length, part height
    part = Part((0.187, 0.170, 0.0085))

    # Initialize Pack_Box and get packing positions
    pack_box = Pack_Box(box=box, part=part, robot=robot)
    pack_box.pack_box()
else:
    logging.error("not connected to robot properly")


robot.stop_robot_control() 
