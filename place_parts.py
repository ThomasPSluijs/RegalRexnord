import logging
from math import floor
import math
from UR5E_control import URControl
import time
import keyboard
import numpy as np

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
        # For loop to go through boxes and fill them one by one
        for box_index in range(self.box.total_boxes):
            # Get box center
            box_center = self.box.box_centers[box_index]
            logging.info(f"Packing in Box {box_index + 1} at center {box_center}")

            # Check total z parts per box
            total_z_parts = floor(self.box_height / self.part_height)
            logging.info(f"Total z parts: {total_z_parts}")

            # Set start z_pos at the bottom of the box
            z_pos = box_center[2]

            # Array for adding part locations for this box
            part_positions_box = []

            # Part number tracker (resets for each box)
            part_number = 1

            # Layer number tracker (increments for each z layer)
            layer_number = 1

            # For loop to go through total z parts to fill a box
            for z in range(total_z_parts):
                # Array to place four parts per layer
                for i in range(4):  # Only 4 parts per layer
                    if i == 0:
                        # First part (top left)
                        if box_index == 0:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_length / 2 + 0.009  # x positive for further away from place side was 
                            y_pos = box_center[1] - self.box_width / 2 + self.part_width / 2 + 0.000  # y positive for further away from box edge
                            rotation = 0
                        elif box_index == 1:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_length / 2 + 0.00  # x positive for further away from place side
                            y_pos = box_center[1] - self.box_width / 2 + self.part_width / 2 + 0.000  # y positive for further away from box edge
                            rotation = 0
                    elif i == 1:
                        # Second part (top right)
                        if box_index == 0:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_width / 2 - 0.006   # x negative for further away from box edge
                            y_pos = box_center[1] - self.box_width / 2 + self.part_length / 2 + 0.007  # y positive for further away from place side
                            rotation = -90
                        elif box_index == 1:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_width / 2 - 0.000  # x negative for further away from box edge
                            y_pos = box_center[1] - self.box_width / 2 + self.part_length / 2 + 0.000  # y positive for further away from place side
                            rotation = -90
                    elif i == 2:
                        # Third part (bottom left)
                        if box_index == 0:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_width / 2 + 0.005  # x positive for further away from box edge
                            y_pos = box_center[1] + self.box_width / 2 - self.part_length / 2 - 0.012  # y negative for further away from place side
                            rotation = 90
                        elif box_index == 1:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_width / 2 + 0.000  # x positive for further away from box edge
                            y_pos = box_center[1] + self.box_width / 2 - self.part_length / 2 - 0.000  # y negative for further away from place side
                            rotation = 90
                    elif i == 3:
                        # Fourth part (bottom right)
                        if box_index == 0:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_length / 2 - 0.010  # x negative for further away from place side
                            y_pos = box_center[1] + self.box_width / 2 - self.part_width / 2 - 0.007  # y negative for further away from box edge
                            rotation = 180
                        elif box_index == 1:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_length / 2 - 0.000  # x negative for further away from place side
                            y_pos = box_center[1] + self.box_width / 2 - self.part_width / 2 - 0.000  # y negative for further away from box edge
                            rotation = 180


                    # Store the positions with box number, part number, layer number
                    part_positions_box.append({
                        "box_number": box_index,
                        "part_number": part_number,
                        "layer_number": layer_number,
                        "position": (x_pos, y_pos, z_pos),
                        "rotation": rotation
                    })

                    # Increment the part number
                    part_number += 1

                # Layer has been filled, increase z_pos for the next layer
                z_pos += self.part_height
                # Increment the layer number
                layer_number += 1

            # Add filled box to total boxes
            self.filled_boxes.append(part_positions_box)

        return self.filled_boxes
    


    #place parts
    def place_part(self, part, part_type='Big-Blue'):
        logging.info(f"given part type to place part: {part_type}")

        box_index = part['box_number']
        part_position = part['position']

        #fast and slow speeds and accelerations. fast for general movements, slow for special movements. 
        speed_fast = 3
        acc_fast = 3
                                                     
        speed_slow = 0.4
        acc_slow = 0.5

        box_center = self.box.box_centers[box_index]
        logging.info(f"Box center: {box_center}")

        # TCP offsets
        pickup_tcp = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]  #edge of part (x=centerpart, y=edge)
        placement_tcp = [-47.5/1000,-52.5/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]  #center of part (x=center,y=center)

        #start rotation, this makes x,y,z aligned to the boxes
        start_rotation = [2.219, 2.227, -0.010]


        self.robot.set_tcp(placement_tcp)
        speed_acc_blend = [1,1,0.45]
        start_pos = self.robot.get_tcp_pos()
        for y in speed_acc_blend:
            start_pos.append(y)


        '''start placement tcp'''
        #step 1: move to proper z height (currently pos: just picked up parts)
        z_above_box = 0.4       
        cur_pos = start_pos.copy()
        cur_pos[2] = z_above_box

        x = 6
        path_step_1 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.0]
        for y in speed_acc_blend:
            path_step_1[x]=y
            x+=1

        #step 12: move to safe x and y position
        #cur_pos = path_step_1.copy()
        #cur_pos = cur_pos[:-3]
        #cur_pos[0] = -0.357
        #cur_pos[1] = 0.490

        #path_step_1_1 = cur_pos.copy()
        #speed_acc_blend = [speed_fast, acc_fast, 0.0]
        #for y in speed_acc_blend:
        #    path_step_1_1 = np.append(path_step_1_1, y)



        # Step 2: Move above the box center and set proper rotation
        cur_pos = path_step_1.copy()
        cur_pos[0] = box_center[0]     # Align x position with box center
        cur_pos[1] = box_center[1]     # Align y position with box center
        cur_pos[2] = z_above_box               # Set a safe z height above the box
        logging.info(f"Step 2: Move to box center: {cur_pos}")

        x = 6
        path_step_2 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.2]       #WAS 0.0
        for y in speed_acc_blend:
            path_step_2[x]=y
            x+=1
        
        
        # Step 3: Move to the desired Z height for placement + 30mm
        cur_pos = path_step_2.copy()
        cur_pos[2] = part_position[2] + 30/1000  # Set Z height to target position within the box
        cur_pos[3] = start_rotation[0]
        cur_pos[4] = start_rotation[1]
        cur_pos[5] = start_rotation[2]
        logging.info(f"Step 3: Move to placement height: {cur_pos}")

        x = 6
        path_step_3 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.0]       #was 0.4
        for y in speed_acc_blend:
            path_step_3[x]=y
            x+=1

    
        # Step 4: Adjust rotation around the Z-axis
        #when angle=180, first do + 10 then do + 170
        rotation_angle = part['rotation']  # pick rotation from part info. convert to radians
        logging.info(f"Step 4: Set rotation around Z-axis to: {rotation_angle}")
        rotations = 1
        if rotation_angle == 180: 
            rotation_angle = 20
            rotations = 2
            logging.info(f"rotations: {rotations}  rotationangel: {rotation_angle}")
        for rotation in range(rotations):
            rotate = [0,0,0,math.radians(0),math.radians(0),math.radians(rotation_angle)]
            pose1 = path_step_3.copy()
            pose1 = pose1[:-3]
            pose2 = rotate
            result_pose = self.robot.pose_trans(pose1, pose2)

            path_step_4 = result_pose.copy()
            speed_acc_blend = [speed_fast, acc_fast, 0.0]
            for y in speed_acc_blend:
                path_step_4 = np.append(path_step_4, y)
                path_step_3 = path_step_4.copy()
            if rotations == 2:
                rotation_angle = 160

        if rotations == 2: rotation_angle = 180


        
        
        # Step 5: Move to the part's target X, Y position
        cur_pos = path_step_4.copy()
        cur_pos[0] = part_position[0]  # Set X to the part's target position
        cur_pos[1] = part_position[1]  # Set Y to the part's target position
        logging.info(f"Step 5: Move to part placement position: {cur_pos}")

        x = 6
        path_step_5 = cur_pos.copy()
        speed_acc_blend = [1, 0.5, 0]
        for y in speed_acc_blend:
            path_step_5[x]=y
            x+=1

        '''end placement tcp'''

        #self.robot.set_tool_frame(placement_tcp)
        path = [
            # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
            path_step_1,  # step 1: move up
            #path_step_1_1,
            path_step_2,  # step 2: move to center box
            path_step_3,  # step 3: move down
            path_step_4,  # step 4: rotate around z
            path_step_5,  #step 5: move to target x and y
            # Voeg meer posities toe zoals nodig
        ]
        self.robot.move_l_path(path=path)



        self.robot.set_tcp(pickup_tcp)
        cur_pos = self.robot.get_tcp_pos()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            cur_pos.append(y)


        '''start pickup tcp'''
        #step 5.1: rotate a bit about x of tcp
        start_pos = cur_pos.copy()
        if part_type == 'Big-Blue' or part_type == 'Holed': rotate_x = -10
        elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': rotate_x = -2
        rotate_x = [0,0,0,math.radians(rotate_x),math.radians(0),math.radians(0)]     #shouold be -5
        
        pose1 = start_pos
        pose1 = pose1[:-3]
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_5 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_5 = np.append(path_step_5, y)

       
        # Step 6: Move to the desired Z height for placement
        cur_pos = path_step_5.copy()
        z_offset = 0
        if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue':
            if part['layer_number'] == 0: z_offset = -4    #layer 0: negative z offset for pressing down the box a bit
            elif part['layer_number'] > 0: z_offset = 0   #rest of the layers: normal height
        cur_pos[2] = part_position[2] + z_offset   # Set Z height to target position within the box

        x = 6
        path_step_6 = cur_pos.copy()  
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_6[x]=y
            x+=1



        if part_type == 'Big-Blue' or part_type == 'Holed': rotate_x = -15
        elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': rotate_x = -30
        # Step 7: Slide part into place (rotates about x axis)     
        rotate_x = [0,0,0,math.radians(rotate_x),math.radians(0),math.radians(0)]
        pose1 = path_step_6.copy()
        pose1 = pose1[:-3]
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_7 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_7 = np.append(path_step_7, y)


           
        #step 8: depending on rotation, move x or y or a bit of z
        offset=157    #should be 175
        if part_type == 'Big-Blue' or part_type == 'Holed': z_offset = 4
        elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': z_offset = 2
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

        cur_pos = path_step_7.copy()
        cur_pos = cur_pos[:-3]
        new_pos = [cur_pos[i] +  offset[i] for i in range(6)]

        path_step_8 = new_pos.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_8 = np.append(path_step_8, y)


        #step 9
        #rotatate more at last part
        if part_type == 'Big-Blue' or part_type == 'Holed': rotation = -10
        elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': rotation = -5
        rotate_x = [0,0,0,math.radians(rotation),math.radians(0),math.radians(0)]
        pose1 = path_step_8.copy()
        pose1 = pose1[:-3]
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_9 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_9 = np.append(path_step_9, y)


        #step 10
        #move y relative to the axiis to the tool, so last part can be pushed of and there is clearance for other parts already laying in the boxs
        relative_from_tcp = [0,0.03,0,math.radians(0),math.radians(0),math.radians(0)]
        pose1 = path_step_9.copy()
        pose1 = pose1[:-3]
        pose2 = relative_from_tcp
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_10 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_10 = np.append(path_step_10, y)



        self.robot.set_tcp(pickup_tcp)  
        path = [
            # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
            path_step_6,  # step 1: move up
            path_step_7,  # step 2: move to center box
            path_step_8,  # step 3: move down
            path_step_9,  # step 4: rotate around z
            path_step_10,  #step 5: move to target x and y
            # Voeg meer posities toe zoals nodig
        ]
        self.robot.move_l_path(path=path)

        '''
        keyboard.wait('space')    

        self.robot.set_tcp(pickup_tcp)  
        path = [
            # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
            #path_step_6,  # step 1: move up
            path_step_7,  # step 2: move to center box
            path_step_8,  # step 3: move down
            path_step_9,  # step 4: rotate around z
            path_step_10,  #step 5: move to target x and y
            # Voeg meer posities toe zoals nodig
        ]
        self.robot.move_l_path(path=path) '''
        '''end pickup tcp'''

        '''start pickup tcp'''
        self.robot.set_tcp(pickup_tcp)
        cur_pos = self.robot.get_tcp_pos()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            cur_pos.append(y)


        # Step 11: Return above the box 
        cur_pos = cur_pos.copy()
        cur_pos = cur_pos[:-3]
        cur_pos[2] = z_above_box  # Return to a safe Z height above the box
        
        blend = 0.0
        path_step_11 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, blend]   #was 0.2
        for y in speed_acc_blend:
            path_step_11 = np.append(path_step_11, y)


        #move to take pic pos
        target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
        path_step_13 = target_position.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.0]
        for y in speed_acc_blend:
            path_step_13 = np.append(path_step_13, y)

        
        #placement tcp 
        path = [
            # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
            path_step_11,  # step 1: move up
            #path_step_12,  # step 2: move to center box
            path_step_13,
        ]
        self.robot.move_l_path(path=path)
        '''end placement tcp'''


        #step 12 rotate a bit back if rotationangle=180
        if rotation_angle == 180:
            #logging.info(f"joint pos: {}")
            cur_joint_pos = self.robot.get_joint_pos()
            cur_joint_pos[5] = -math.radians(0)
            self.robot.move_j(cur_joint_pos, 0.3, 0.3)



        



#only run if run from file
if __name__ == '__main__':
    robot = URControl("192.168.0.1")
    robot.connect()



    base_z_wide_parts = -12/1000
    base_z_narrow_parts = -16/1000 
    base_z = -12/1000
        
    # Create instances for box and part.
    #neeeds: total boxes, box pos (x and y center, z bottom), box dimensions: (x, y, z)
    box = Box(total_boxes=2, box_pos=[(-230/1000, -575/1000, base_z), [237/1000,-588/1000, base_z]], box_size=(0.365, 0.365, 0.180 ))

    #needs: part width, part length, part height
    part = Part((0.187, 0.170, 0.009))
    

    #gray parts: z= 0.0085                                              
    #big blue parts: z=0.01260
    #other parts: idk yet


    # Initialize Pack_Box and get packing positions
    pack_box = Pack_Box(box=box, part=part, robot=robot)
    pack_box.pack_box(part_type='wide')


    robot.stop_robot_control()  
