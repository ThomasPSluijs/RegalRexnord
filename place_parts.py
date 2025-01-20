import logging
from math import floor
import math
import numpy as np
from configuration import *


#Place parts in boxes check 

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
    def __init__(self, box, part, robot, boxing_machine):
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

        #boxing machine
        self.boxing_machine = boxing_machine

        #last layer
        self.last_layer = 0

   
        #get al packing positions in the boxes. These are the center coordinates of the parts, rotations of the parts and the z_height of the parts
    def get_pack_pos(self, item_type):
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

            if item_type == 'Big-Blue': place_extra_offset=4/1000
            else: place_extra_offset = 6/1000

            if item_type == 'Big-Blue' or item_type == 'Holed':
                z_pos_offset = -1/1000 #for differen parts, differen offset because box is not level
            else:
                z_pos_offset = -1/1000 #for differen parts, differen offset because box is not level


            # For loop to go through total z parts to fill a box
            for z in range(total_z_parts):
                # Array to place four parts per layer
                for i in range(4):  # Only 4 parts per layer
                    if i == 0:
                        # First part (top left)
                        if box_index == 0:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_length / 2 + 0.010 + place_extra_offset  # x positive for further away from place side was 
                            y_pos = box_center[1] - self.box_width / 2 + self.part_width / 2 + 0.009  # y positive for further away from box edge
                            rotation = 0
                        elif box_index == 1:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_length / 2 + 0.006 + place_extra_offset  # x positive for further away from place side
                            y_pos = box_center[1] - self.box_width / 2 + self.part_width / 2 + 0.015  # y positive for further away from box edge
                            rotation = 0
                    elif i == 1:
                        # Second part (top right)
                        if box_index == 0:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_width / 2 - 0.013   # x negative for further away from box edge
                            y_pos = box_center[1] - self.box_width / 2 + self.part_length / 2 + 0.004 + place_extra_offset  # y positive for further away from place side
                            if item_type == 'Small-Blue': x_pos -= 0.003
                            rotation = -90
                        elif box_index == 1:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_width / 2 - 0.009  # x negative for further away from box edge
                            y_pos = box_center[1] - self.box_width / 2 + self.part_length / 2 + 0.013 + place_extra_offset  # y positive for further away from place side
                            rotation = -90
                    elif i == 2:
                        if item_type == 'Big-Blue':
                            z_pos_offset = -4/1000
                        else:
                            z_pos_offset = -2/1000
                        # Third part (bottom left)
                        if box_index == 0:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_width / 2 + 0.010  # x positive for further away from box edge
                            y_pos = box_center[1] + self.box_width / 2 - self.part_length / 2 - 0.010 - place_extra_offset  # y negative for further away from place side
                            rotation = 90
                        elif box_index == 1:
                            x_pos = box_center[0] - self.box_length / 2 + self.part_width / 2 + 0.006  # x positive for further away from box edge
                            y_pos = box_center[1] + self.box_width / 2 - self.part_length / 2 - 0.007 - place_extra_offset  # y negative for further away from place side
                            rotation = 90
                    elif i == 3:
                        if item_type == 'Big-Blue':
                            z_pos_offset = -4/1000
                        else:
                            z_pos_offset = -2/1000
                        # Fourth part (bottom right)
                        if box_index == 0:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_length / 2 - 0.013 - place_extra_offset  # x negative for further away from place side
                            y_pos = box_center[1] + self.box_width / 2 - self.part_width / 2 - 0.015  # y negative for further away from box edge
                            rotation = 180
                        elif box_index == 1:
                            x_pos = box_center[0] + self.box_length / 2 - self.part_length / 2 - 0.008 - place_extra_offset # x negative for further away from place side
                            y_pos = box_center[1] + self.box_width / 2 - self.part_width / 2 - 0.006  # y negative for further away from box edge
                            rotation = 180

                    _z_pos = z_pos + z_pos_offset

                    # Store the positions with box number, part number, layer number
                    part_positions_box.append({
                        "box_number": box_index,
                        "part_number": part_number,
                        "layer_number": layer_number,
                        "position": (x_pos, y_pos, _z_pos),
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
    def place_part(self, part, part_type='Big-Blue',box_rotation='horizontal'):
        logging.info(f"given part type to place part: {part_type}")

        box_index = part['box_number']
        part_position = part['position']
        cur_layer = part['layer_number']

        #fast and slow speeds and accelerations. fast for general movements, slow for special movements. 
        if part_type == 'Big-Blue' or part_type == 'Holed':                          
            speed_slow = 2
            acc_slow = 1.5
        else:
            speed_slow = 0.6
            acc_slow = 0.6

        box_center = self.box.box_centers[box_index]

        #start rotation, this makes x,y,z aligned to the boxes
        start_rotation = [2.219, 2.227, -0.010]


        '''step 1 t/m 5 in 1 PATH'''
        '''STEP 1: currently just picked up parts, now move to proper Z height for travelling to boxes'''
        z_above_box = 0.4


        '''STEP 2: move to center box. no tuning here'''


        '''STEP 3: move to desired z height for placing + offset'''
        z_offset_step_3 = 27/1000


        '''STEP 4: rotate parts, no tuning here'''
        rotation_angle = part['rotation']  # pick rotation from part info. convert to radians


        '''STEP 5: move to x and y target position, no tuning here'''



        '''step 5.1 t/m step 10 in 1 PATH'''
        '''STEP 5.1: rotate a bit before fully going to proper z'''
        if part_type == 'Big-Blue' or part_type == 'Holed': rotate_x = -8
        elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': rotate_x = -2
        rotate_x_step_5_1 = [0,0,0,math.radians(rotate_x),math.radians(0),math.radians(0)]     #shouold be -5


        '''STEP 6: move to desired z height'''
        z_offset_step_6 = 0
        rotation = part['rotation']
        if box_rotation == 'horizontal':   #high side parrallel to belt
            if rotation == 90 or rotation == -90:    #low side. 
                if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue':
                    z_offset_step_6 = -2/1000    
                else: #big parts
                    z_offset_step_6 = 3/1000
            else:   #angled side. bit heigher than low side
                if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue':
                    z_offset_step_6 = 1/1000    
                else: #big parts
                    z_offset_step_6 = 6/1000

        elif box_rotation == 'vertical': #high side not parrallel to belt
            if rotation == 0 or rotation == 180:
                if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue':
                    z_offset_step_6 = -2/1000   
                else: #big parts
                    z_offset_step_6 = 3/1000
            else:   #angled side. bit heigher than low side
                if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue':
                    z_offset_step_6 = 1/1000    
                else: #big parts
                    z_offset_step_6 = 6/1000


        
        '''STEP 7: rotate about x so parts can be placed'''
        if part_type == 'Big-Blue' or part_type == 'Holed': rotate_x = -23
        elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': rotate_x = -18
        rotate_y = 0
        rotation = part['rotation']
        if part['layer_number'] < 7:
            if box_rotation == 'horizontal':
                if rotation == 0 or rotation == 180:
                    #logging.info("---rotate also around y wile placing!---")
                    rotate_y = 5    #rotate 5 degrees about y of tool. this way placing is parralle to the bottom of the box
            elif box_rotation == 'vertical':
                if rotation == 90 or rotation == -90:
                    #logging.info("---rotate also around y wile placing!---")
                    rotate_y = 5    #rotate 5 degrees about y of tool. this way placing is parralle to the bottom of the box

        else:
            if box_rotation == 'horizontal':
                if rotation == 0 or rotation == 180:
                    #logging.info("---rotate also around y wile placing!---")
                    rotate_y = 3    #rotate 5 degrees about y of tool. this way placing is parralle to the bottom of the box
            elif box_rotation == 'vertical':
                if rotation == 90 or rotation == -90:
                    #logging.info("---rotate also around y wile placing!---")
                    rotate_y = 3    #rotate 5 degrees about y of tool. this way placing is parralle to the bottom of the box     


        rotate_x_step_7 = [0,0,0,math.radians(rotate_x),math.radians(rotate_y),math.radians(0)]


        '''step 8: perform placing movement. because box higher in the middle, move z a bit up'''
        if part_type == 'Big-Blue' or part_type == 'Holed':
            offset_step_8=157    
        else:
            offset_step_8=157

        z_offset_step_8=0
        rotation = part['rotation']
        if part['layer_number'] < 7:
            if box_rotation == 'horizontal':       #high side parrallel to belt
                if rotation == 90 or rotation == -90: #move z up if moving to high side
                    if part_type == 'Big-Blue' or part_type == 'Holed': 
                        z_offset_step_8 = 5
                        #logging.info("---while placing move z up!!--")
                    elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': 
                        z_offset_step_8 = 6
                        #logging.info("---while placing move z up!!--")
            
            elif  box_rotation == 'vertical':    #high side not parrallel to belt
                if rotation == 0 or rotation == 180:   #move z up if moving to high side
                    if part_type == 'Big-Blue' or part_type == 'Holed': 
                        z_offset_step_8 = 5
                        #logging.info("while placing move z up!!")
                    elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': 
                        z_offset_step_8 = 6
                        #logging.info("while placing move z up!!")
        else:
            if box_rotation == 'horizontal':       #high side parrallel to belt
                if rotation == 90 or rotation == -90: #move z up if moving to high side
                    if part_type == 'Big-Blue' or part_type == 'Holed': 
                        z_offset_step_8 = 4
                        #logging.info("---while placing move z up!!--")
                    elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': 
                        z_offset_step_8 = 6
                        #logging.info("---while placing move z up!!--")
            
            elif  box_rotation == 'vertical':    #high side not parrallel to belt
                if rotation == 0 or rotation == 180:   #move z up if moving to high side
                    if part_type == 'Big-Blue' or part_type == 'Holed': 
                        z_offset_step_8 = 4
                        #logging.info("while placing move z up!!")
                    elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': 
                        z_offset_step_8 = 6
                        #logging.info("while placing move z up!!")




        '''STEP 9: rotate more about x for last placing movement'''
        if part_type == 'Big-Blue' or part_type == 'Holed': rotation = -10
        elif part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': rotation = -13
        rotate_x_step_9 = [0,0,0,math.radians(rotation),math.radians(0),math.radians(0)]


        '''STEP 10: perform last placing movement'''
        y_movement_step_10 = 0.03

        '''rest of movementents: no tuning'''



        '''start placement tcp'''
        '''PREPARTION MOVEMENTES: move to desired x,y. no placing in this part(STEP 1 t/m STEP 5)'''
        #set tcp and get current position to base movements off
        self.robot.set_tcp(placement_tcp)
        speed_acc_blend = [1,1,0.45]
        start_pos = self.robot.get_tcp_pos()
        for y in speed_acc_blend:
            start_pos.append(y)


        #step 1: move to proper z height (currently pos: just picked up parts)     
        cur_pos = start_pos.copy()
        cur_pos[2] = z_above_box

        x = 6
        path_step_1 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.2]
        for y in speed_acc_blend:
            path_step_1[x]=y
            x+=1


        # Step 2: Move above the box center 
        cur_pos = path_step_1.copy()
        cur_pos[0] = box_center[0]     # Align x position with box center
        cur_pos[1] = box_center[1]     # Align y position with box center
        cur_pos[2] = z_above_box               # Set a safe z height above the box

        x = 6
        path_step_2 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.1]       #
        for y in speed_acc_blend:
            path_step_2[x]=y
            x+=1
        

        # Step 3: Move to the desired Z height for placement + 30mm
        cur_pos = path_step_2.copy()
        cur_pos[2] = part_position[2] + z_offset_step_3 # Set Z height to target position within the box
        cur_pos[3] = start_rotation[0]
        cur_pos[4] = start_rotation[1]
        cur_pos[5] = start_rotation[2]

        x = 6
        path_step_3 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.0]       
        for y in speed_acc_blend:
            path_step_3[x]=y
            x+=1


        # Step 4: Adjust rotation around the Z-axis
        #when angle=180, first do + 10 then do + 170
        rotations = 1
        if rotation_angle == 180: 
            rotation_angle = 20
            rotations = 2
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

        x = 6
        path_step_5 = cur_pos.copy()
        speed_acc_blend = [1, 0.5, 0]
        for y in speed_acc_blend:
            path_step_5[x]=y
            x+=1

        
        #create path and move robot
        self.boxing_machine.wait_if_paused()
        path = [
            # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
            path_step_1,  # step 1: move up
            path_step_2,  # step 2: move to center box
            path_step_3,  # step 3: move down
            path_step_4,  # step 4: rotate around z
            path_step_5,  #step 5: move to target x and y
            # Voeg meer posities toe zoals nodig
        ]
        self.robot.move_l_path(path=path)
        '''end placement tcp'''



        '''PLACING SECTION: this section contains the path of the placement.'''
        '''start pickup tcp'''
        #set tcp and get start position with new tcp
        self.robot.set_tcp(pickup_tcp)
        cur_pos = self.robot.get_tcp_pos()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            cur_pos.append(y)


        #step 5.1: rotate a bit about x of tcp
        start_pos = cur_pos.copy()
        pose1 = start_pos
        pose1 = pose1[:-3]
        pose2 = rotate_x_step_5_1
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_5_1 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_5_1 = np.append(path_step_5_1, y)

       
        # Step 6: Move to the desired Z height for placement
        cur_pos = path_step_5_1.copy()
        cur_pos[2] = part_position[2] + z_offset_step_6   # Set Z height to target position within the box

        x = 6
        path_step_6 = cur_pos.copy()  
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_6[x]=y
            x+=1


        # Step 7: Slide part into place (rotates about x axis)     
        pose1 = path_step_6.copy()
        pose1 = pose1[:-3]
        pose2 = rotate_x_step_7
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_7 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_7 = np.append(path_step_7, y)

           
        #step 8: depending on rotation, move x or y or a bit of z
        if rotation_angle == 0:
            #move x positive
            offset= [offset_step_8/1000,0,z_offset_step_8/1000,0,0,0]
        elif rotation_angle == -90:
            #move y positive
            offset= [0,offset_step_8/1000,z_offset_step_8/1000,0,0,0]
        elif rotation_angle == 90:
            #move y negative
            offset= [0,-offset_step_8/1000,z_offset_step_8/1000,0,0,0]  
        elif rotation_angle == 180:
            #move y negatie
            offset= [-offset_step_8/1000,0,z_offset_step_8/1000,0,0,0]

        cur_pos = path_step_7.copy()
        cur_pos = cur_pos[:-3]
        new_pos = [cur_pos[i] +  offset[i] for i in range(6)]

        path_step_8 = new_pos.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_8 = np.append(path_step_8, y)


        #step 9 #rotatate more at last part
        pose1 = path_step_8.copy()
        pose1 = pose1[:-3]
        pose2 = rotate_x_step_9
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_9 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_9 = np.append(path_step_9, y)


        #step 10 #move y relative to the axiis to the tool, so last part can be pushed of and there is clearance for other parts already laying in the boxs
        relative_from_tcp = [0,y_movement_step_10,0,0,math.radians(0),math.radians(0),math.radians(0)]
        pose1 = path_step_9.copy()
        pose1 = pose1[:-3]
        pose2 = relative_from_tcp
        result_pose = self.robot.pose_trans(pose1, pose2)

        path_step_10 = result_pose.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0]
        for y in speed_acc_blend:
            path_step_10 = np.append(path_step_10, y)


        self.boxing_machine.wait_if_paused()

        path = [
            # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
            path_step_5_1,
            path_step_6,  # step 6: move to correct z height (x and y are already correct)
            path_step_7,  # step 7: rotate parts
            path_step_8,  # step 8: move so parts fall off
            path_step_9,  # step 9: rotate more at end
            path_step_10,  #step 10: move the rest
            # Voeg meer posities toe zoals nodig
        ]
        self.robot.move_l_path(path=path)
        '''end placing movement'''


         
        '''END FASE: parts have been placed. move up, rotate and move to proper x and y and z 
        for checking if parts are properly placed, move to take pic pos at the dn '''
        '''start pickup tcp'''
        if rotation_angle != 180:
            '''start pickup tcp'''
            self.robot.set_tcp(pickup_tcp)
            cur_pos = self.robot.get_tcp_pos()
            speed_acc_blend = [speed_slow, acc_slow, 0]
            for y in speed_acc_blend:
                cur_pos.append(y)

            # Step 11: Return above the box 
            cur_pos = cur_pos.copy()
            cur_pos = cur_pos[:-3]
            cur_pos[2] = z_above_box   # Return to a safe Z height above the box
            
            path_step_11 = cur_pos.copy()
            speed_acc_blend = [speed_fast, acc_fast, 0.2]   #was 0.2
            for y in speed_acc_blend:
                path_step_11 = np.append(path_step_11, y)

            #move to take pic pos
            target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
            path_step_12 = target_position.copy()
            speed_acc_blend = [speed_fast, acc_fast, 0.0]
            for y in speed_acc_blend:
                path_step_12 = np.append(path_step_12, y)

            self.boxing_machine.wait_if_paused()

            #placement tcp 
            path = [
                # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
                path_step_11,  # step 1: move up
                path_step_12,   #move to take pic pos
            ]
            self.robot.move_l_path(path=path)
            '''end placement tcp'''


        #joint rotatation if needed
        elif rotation_angle == 180:
            #move up first
            cur_pos = self.robot.get_tcp_pos()
            cur_pos[2] = z_above_box
            self.robot.move_l(cur_pos, speed_fast, acc_fast)

            #move joint 6 to safe angle
            cur_joint_pos = self.robot.get_joint_pos()
            cur_joint_pos[5] = math.radians(-70)
            self.robot.move_j(cur_joint_pos, 3, 3)

            #rotate more for checking
            x_offset=-133/1000
            y_offset=-100/1000
            z_height=0.6
            check_placement_pos = [box_center[0]+x_offset, box_center[1] + y_offset, z_height, 2.222,2.248,0.004]
            self.robot.move_l(check_placement_pos, speed_fast, acc_fast) #slow for testing !!! 

            bad_detected = self.boxing_machine.camera.check_bad_part_placement()
            if bad_detected:
                logging.info("bad placement detected")
                self.boxing_machine.pause()
                self.boxing_machine.interface.start_button_pressed()
                self.boxing_machine.interface.update_status("please fix placement position, then press resume")
            else:
                logging.info("no bad position detected")

            #self.boxing_machine.wait_if_paused()

            #move to take pic pos
            target_position = [-0.6639046352765678, -0.08494527187802497, 0.529720350746548, 2.222, 2.248, 0.004]
            self.robot.move_l(target_position, speed_fast, acc_fast)

            self.boxing_machine.wait_if_paused()