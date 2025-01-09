from UR5E_control import URControl
import math
import logging
import numpy as np
import keyboard

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Pick_parts():
    def __init__(self, robot, boxing_machine):
        self.robot = robot  #robot class
        self.boxing_machine = boxing_machine


    #picks parts from given x and y coordinate. y = center of part along y axis. x = edge of part closest to the robot
    def pick_parts(self, part_x, part_y,part_type='Green'):
        #fast and slow speeds and accelerations. fast for general movements, slow for special movements. 
        speed_fast = 3
        acc_fast = 3

        speed_middle = 1
        acc_middle = 1

        speed_slow = 0.3
        acc_slow = 0.3


        #part_x offset, one side needs a little bit more than the other side (or tune the camera calibration)
        if part_y > 0.05: part_x += 16/1000 
        else: part_x += 20/1000



        #part length, some parts are a bit shorter so robot has to move less
        if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': part_length = 0.172
        elif part_type == 'Big-Blue': part_length = 0.176
        else: part_length = 0.174



        '''STEP 1 MOVE TO PART X,Y AND Z A BIT ABOVE THE PART'''
        part_y_offset = 10/1000 + 25/1000 #y offset so there is a bit of clearance.
        part_pos_x_offset = 0.010  #x offset so gripper starts before parts and does not crash down when going down. also used in step 4
        part_z_offset = 100/1000  #z offset so gripper starts a bit above the part


        '''STEP 2 ROTATION'''
        #rotation about x of tool, for narrow parts the rotation needs to be a bit more
        if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': rotate = -30
        else: rotate = -23
        rotate_x = [0,0,0,math.radians(rotate),math.radians(0),math.radians(0)]   


        '''STEP 3 Z LOCATION'''
        #belt z location, for some parts the gripper needs to be a little bit higher or lower
        if part_type == 'Green' or part_type == 'Rubber' or part_type == 'Small-Blue': belt_z = [0,0,-124/1000,0,0,0]
        elif part_type == 'Big-BLue': belt_z = [0,0,-116/1000,0,0,0]
        else: belt_z = [0,0,-122/1000,0,0,0]   
        logging.info(f"belt z: {belt_z} {part_type}") 

        #one side needs to be a little bit higher
        if part_type == 'Big-Blue' and part_y > 0.05: belt_z = [0,0,-116/1000,0,0,0]                 
        

        '''STEP 4 PICKUP MOVEMENT'''
        #total x movement when tool is rotated and aligned to pick up the parts. moves partlength + offset
        move_x = [-part_length-part_pos_x_offset,0,0,0,0,0]  


        '''STEP 5 MOVE BACK A BIT WHILE ROTATING BACK'''
        #small x offset for narrow parts
        if part_type != 'Big-BLue' and part_type != 'Holed': step_5_x_back = 5/1000                               
        step_5_x_back = 0/1000


        '''STEP 6 MOVE BACK A BIT MORE'''
        if part_type != 'Big-Blue' and part_type != 'Holed': step_6_x_back=[7/1000,0,0,0,0,0]
        else: step_6_x_back=[2/1000,0,0,0,0,0]




        #tcp section
        pickup_tcp = [-47.5/1000,-140/1000,135/1000,0,0,0]  #edge of part (x=centerpart, y=edge)
        rotate_tcp = [-47.5/1000, 42/1000, 135/1000, 0, 0, 0]
        self.robot.set_tool_frame(pickup_tcp)



        #start rotation, this is aligned to the belt
        start_rotation = [2.230, 2.209, 0.013]



        #get current robot position
        self.robot.set_tcp(pickup_tcp)
        speed_acc_blend = [1,1,0.45]
        start_pos = self.robot.get_tcp_pos()
        for y in speed_acc_blend:
            start_pos.append(y)



        '''start moving etc'''
        #step 1
        #move to part x and part y, apply a offset on the x so the gripper is a bit before the part. also rotate to start rotation(level and aligned)
        cur_pos = start_pos.copy()
        cur_pos[0] = part_x + part_pos_x_offset
        cur_pos[1] = part_y + part_y_offset
        cur_pos[2] = belt_z[2] + part_z_offset
        cur_pos[3] = start_rotation[0]
        cur_pos[4] = start_rotation[1]
        cur_pos[5] = start_rotation[2]
        path_step_1 = cur_pos.copy()
        path_step_1 = path_step_1[:-3]

        speed_acc_blend = [speed_fast, acc_fast, 0.00]
        for y in speed_acc_blend:
            path_step_1 = np.append(path_step_1, y)

        
        #step 2
        #rotate around x axis ~20 degrees
        pose1 = path_step_1.copy()
        pose1 = pose1[:-3]
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)
        path_step_2 = result_pose.copy()

        speed_acc_blend = [speed_fast, acc_fast, 0.0]
        for y in speed_acc_blend:
            path_step_2 = np.append(path_step_2, y)

        
        #step 3
        #move to determined z position (belt z) 
        cur_pos = path_step_2.copy() 
        cur_pos[2] = belt_z[2] 

        path_step_3 = cur_pos.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.00]
        for y in speed_acc_blend:
            path_step_3 = np.append(path_step_3, y)

        logging.info(f"pick pos: {cur_pos}")

    
        #step 4
        #perform a relative x movement so parts get picked up
        cur_pos = path_step_3.copy()
        cur_pos = cur_pos[:-3]
        new_linear_move = [cur_pos[i] +  move_x[i] for i in range(6)]

        path_step_4 = new_linear_move.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0.0]
        for y in speed_acc_blend:
            path_step_4 = np.append(path_step_4, y)


        #step 5
        #rotate back
        pose1 = path_step_4.copy()
        pose1 = pose1[:-3]
        pose2 = rotate_x
        rotate_x[3] *= -1
        result_pose = self.robot.pose_trans(pose1, pose2)
        result_pose[0] += step_5_x_back

        path_step_5 = result_pose.copy()
        speed_acc_blend = [speed_middle, acc_middle, 0.0]
        for y in speed_acc_blend:
            path_step_5 = np.append(path_step_5, y)


        #step 6
        #move back relative
        cur_pos = path_step_5.copy()
        cur_pos = cur_pos[:-3]
        new_linear_move = [cur_pos[i] +  step_6_x_back[i] for i in range(6)]

        path_step_6 = new_linear_move.copy()
        speed_acc_blend = [speed_middle, 0.1, 0.0]
        for y in speed_acc_blend:
            path_step_6 = np.append(path_step_6, y)


        #move path 1 till 6 with pickup tcp
        path = [
            path_step_1,
            path_step_2,
            path_step_3,
            path_step_4,
            path_step_5,
            path_step_6,
        ]
        self.robot.move_l_path(path=path)
        '''end pickup tcp'''
  
        #self.boxing_machine.self.interface.start_button_pressed()

        '''
        #move path 1 till 6 with pickup tcp
        path = [
            #path_step_1,
            #path_step_2,
            #path_step_3,
            path_step_4,
            path_step_5,
            path_step_6,
        ]
        self.robot.move_l_path(path=path) '''
        '''end pickup tcp'''


        #move up a bit
        relative_z = [0,0,10/1000,0,0,0]
        self.robot.move_add_l(relative_z)

        '''rotate tcp'''
        #step 7
        #rotate back
        self.robot.set_tcp(rotate_tcp)
        rotate_x = [0,0,0,math.radians(5),0,0]
        pose1 = self.robot.get_tcp_pos()
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)
        if part_type == 'Big-Blue': self.robot.move_l(result_pose, speed_slow, acc_slow)
        '''end rotate tcp'''


        '''start pickup tcp'''
        self.robot.set_tcp(pickup_tcp)
        speed_acc_blend = [1,1,0.45]
        start_pos = self.robot.get_tcp_pos()
        for y in speed_acc_blend:
            start_pos.append(y)
        
        #step 8
        #move up relative.
        relative_move=[0,0,0.15,0,0,0]
        cur_pos = start_pos.copy()
        cur_pos = cur_pos[:-3]
        new_linear_move = [cur_pos[i] +  relative_move[i] for i in range(6)]

        path_step_8 = new_linear_move.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0.05]
        for y in speed_acc_blend:
            path_step_8 = np.append(path_step_8, y)



        #step 9
        #move to safe y
        cur_pos = path_step_8.copy()
        cur_pos = cur_pos[:-3]
        cur_pos[1] = -0.01964148815131326

        path_step_9 = cur_pos.copy()
        speed_acc_blend = [speed_slow, acc_slow, 0.0]
        for y in speed_acc_blend:
            path_step_9 = np.append(path_step_9, y)



        #step 10
        #rotate around x axis and y so parts will stay in place
        relative_move = [0,0,0,math.radians(10),math.radians(-20),math.radians(0)]
        pose1 = path_step_9.copy()
        pose1 = pose1[:-3]
        pose2 = relative_move
        result_pose = self.robot.pose_trans(pose1, pose2)
        
        path_step_10 = result_pose.copy()
        speed_acc_blend = [speed_fast, acc_fast, 0.0]
        for y in speed_acc_blend:
            path_step_10 = np.append(path_step_10, y)


        path = [
            path_step_8,
            path_step_9,
            path_step_10
        ]
        self.robot.move_l_path(path=path)
        '''end pickup tcp'''

  