from UR5E_control import URControl
import math
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Pick_parts():
    def __init__(self, robot):
        self.belt_z = [0,0,-0.089,0,0,0]                                            #belt z location (should be )
        self.rotate_x = [0,0,0,math.radians(-15),math.radians(0),math.radians(0)]   #rotation about x axis of tool  
        
        self.part_pos_x_offset = 0.02                                #x offset so gripper starts before parts and does not crash down when going down
        part_length = 0.187
        self.move_x = [-part_length-self.part_pos_x_offset,0,0,0,0,0]         #total x movement when tool is rotated and aligned to pick up the parts. moves partlength + offset

        self.robot = robot  #robot class


    #picks parts from given x and y coordinate. y = center of part along y axis. x = edge of part closest to the robot
    #1: move to safe z height
    #2: move to part x and part y, apply a offset on the x so the gripper is a bit before the part
    #3: rotate around x so parts can be picked up
    #4: move to belt z height
    #5: perform a relative x movement so parts get picked up
    #6: rotate back
    #7 rotate a bit so parts are better located
    #8: move up
    #9: rotate parts into gripper
    #done
    def pick_parts(self, part_x, part_y):
        #fast and slow speeds and accelerations. fast for general movements, slow for special movements. 
        speed_fast = 0.5
        acc_fast = 1

        speed_slow = 0.1   
        acc_slow = 0.5

        pickup_tcp = [-47.5/1000,-140/1000,135/1000,math.radians(0),math.radians(0),math.radians(0)]  #edge of part (x=centerpart, y=edge)
        self.robot.set_tool_frame(pickup_tcp)


        start_rotation = [2.222, 2.248, 0.004]


        #step 2
        #move to part x and part y, apply a offset on the x so the gripper is a bit before the part. also rotate to start rotation(level and aligned)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[0] = part_x + self.part_pos_x_offset
        cur_pos[1] = part_y
        cur_pos[3] = start_rotation[0]
        cur_pos[4] = start_rotation[1]
        cur_pos[5] = start_rotation[2]
        self.robot.moveL(cur_pos, speed_fast, acc_fast)


        #step 3
        #rotate around x axis ~20 degrees
        logging.info(f"perform rotation about TCP axis: {self.rotate_x}")
        pose1 = self.robot.get_tcp_pos()
        pose2 = self.rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, speed_fast, acc_fast)


        #step 4
        #move to determined z position (belt z)
        cur_pos = self.robot.get_tcp_pos()  
        cur_pos[2] = self.belt_z[2]
        logging.info(f"move to z pos: {cur_pos}")
        self.robot.move_l(cur_pos, speed_slow, acc_slow)


        #step 5
        #perform a relative x movement so parts get picked up
        logging.info(f"pickup parts with relative x movment: {self.move_x}")
        self.robot.move_add_l(self.move_x, speed_slow, acc_slow)


        #step 6
        #rotate back
        logging.info("rotate back so parts get picked up")
        pose1 = self.robot.get_tcp_pos()
        pose2 = self.rotate_x
        self.rotate_x[3] *= -1
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, speed_slow, acc_slow)


        #step 7
        #move a bit up and away so parts and rotate a bit so parts are better in the gripper
        logging.info("move a bit")
        pose1 = self.robot.get_tcp_pos()
        pose2 = self.rotate_x
        self.rotate_x[3] = math.radians(5)
        result_pose = self.robot.pose_trans(pose1, pose2)
        result_pose[2] += 10/1000
        result_pose[0] += 5/1000
        self.robot.move_l(result_pose, speed_slow, acc_slow)


        #step 8
        #move up relative.
        relative_move=[0,0,0.15,0,0,0]
        logging.info(f"move up relative to current position: {relative_move}")
        self.robot.move_add_l(relative_move, speed_fast, acc_fast)


        #step 9
        #rotate around x axis and y so parts will stay in place
        relative_move = [0,0,0,math.radians(20),math.radians(-20),math.radians(0)]
        logging.info(f"rotate back around x and y of tcp: {relative_move}")
        pose1 = self.robot.get_tcp_pos()
        pose2 = relative_move
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, speed_fast, acc_fast)


        #done


'''
code below is to test this file. should be commented.
'''

#connect to robot
robot = URControl("192.168.0.1")
robot.connect()

#set toolframe
tool_frame=[-47.5/1000,-140/1000,102.6/1000,math.radians(-1.2),math.radians(2),math.radians(-5)]
robot.set_tool_frame(tool_frame=tool_frame)

pick_part = Pick_parts(robot=robot)
pick_part.pick_parts(0.1,0.2)

robot.stop_robot_control() 