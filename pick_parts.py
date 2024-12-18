from UR5E_control import URControl
import math
import logging
import time

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Pick_parts():
    def __init__(self, robot):
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
        belt_z = [0,0,-116/1000,0,0,0]                                            #belt z location (should be )
        rotate_x = [0,0,0,math.radians(-23),math.radians(0),math.radians(0)]   #rotation about x axis of tool  
        
        part_pos_x_offset = 0.03                                #x offset so gripper starts before parts and does not crash down when going down
        part_pos_x_offset_2 = -0.06                                #x offset so gripper does not go into wall #should be 0.017
        part_length = 0.185

        #total x movement when tool is rotated and aligned to pick up the parts. moves partlength + offset
        move_x = [-part_length-part_pos_x_offset+part_pos_x_offset_2,0,0,0,0,0]  


        #fast and slow speeds and accelerations. fast for general movements, slow for special movements. 
        speed_fast = 1
        acc_fast = 1

        speed_slow = 0.15
        acc_slow = 0.5

        pickup_tcp = [-47.5/1000,-140/1000,135/1000,0,0,0]  #edge of part (x=centerpart, y=edge)

        rotate_tcp = [-47.5/1000, 40/1000, 135/1000, 0, 0, 0]

        self.robot.set_tool_frame(pickup_tcp)


        start_rotation = [2.222, 2.248, 0.004]


        #step 1
        #move to part x and part y, apply a offset on the x so the gripper is a bit before the part. also rotate to start rotation(level and aligned)
        cur_pos = self.robot.get_tcp_pos()
        cur_pos[0] = part_x + part_pos_x_offset
        cur_pos[1] = part_y + 10/1000
        cur_pos[2] = belt_z[2] + 100/1000
        cur_pos[3] = start_rotation[0]
        cur_pos[4] = start_rotation[1]
        cur_pos[5] = start_rotation[2]
        self.robot.move_l(cur_pos, speed_fast, acc_fast)

        
        #step 2
        #rotate around x axis ~20 degrees
        logging.info(f"perform rotation about TCP axis: {rotate_x}")
        pose1 = self.robot.get_tcp_pos()
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, speed_fast, acc_fast)

        
        #step 3
        #move to determined z position (belt z) 
        cur_pos = self.robot.get_tcp_pos()  
        cur_pos[2] = belt_z[2] 
        logging.info(f"move to z pos: {cur_pos}")
        self.robot.move_l(cur_pos, speed_slow, acc_slow)

    
        #step 4
        #perform a relative x movement so parts get picked up
        logging.info(f"pickup parts with relative x movment: {move_x}")
        self.robot.move_add_l(move_x, speed_slow, acc_slow)


        #step 5
        #rotate back
        logging.info("rotate back so parts get picked up")
        pose1 = self.robot.get_tcp_pos()
        pose2 = rotate_x
        rotate_x[3] *= -1
        result_pose = self.robot.pose_trans(pose1, pose2)
        result_pose[0] += 10/1000                               #should be 10
        result_pose[2] += 5/1000
        self.robot.move_l(result_pose, speed_slow, acc_slow)


        #step 6
        #move back relative
        relative_move=[7/1000,0,0,0,0,0]
        logging.info(f"move up relative to current position: {relative_move}")
        self.robot.move_add_l(relative_move, speed_slow, acc_slow)


        #step 7
        #rotate back
        logging.info("rotate back so parts get picked up")
        self.robot.set_tcp(rotate_tcp)
        rotate_x = [0,0,0,math.radians(5),0,0]
        pose1 = self.robot.get_tcp_pos()
        pose2 = rotate_x
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, speed_slow, acc_slow)


        #step 8
        #move up relative.
        self.robot.set_tcp(pickup_tcp)
        relative_move=[0,0,0.15,0,0,0]
        logging.info(f"move up relative to current position: {relative_move}")
        self.robot.move_add_l(relative_move, speed_fast, acc_fast)


        #step 9
        #rotate around x axis and y so parts will stay in place
        relative_move = [0,0,0,math.radians(5),math.radians(-18),math.radians(0)]
        logging.info(f"rotate back around x and y of tcp: {relative_move}")
        pose1 = self.robot.get_tcp_pos()
        pose2 = relative_move
        result_pose = self.robot.pose_trans(pose1, pose2)
        self.robot.move_l(result_pose, 3, 3)

  



#for testing. only run if called directly
if __name__ == "__main__":
    #connect to robot
    robot = URControl("192.168.0.1")
    robot.connect()

    pick_part = Pick_parts(robot=robot)
    pick_part.pick_parts(0.1,0.2)

    robot.stop_robot_control()  