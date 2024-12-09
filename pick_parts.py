from UR5E_control import URControl
import math

def pick_parts():
    belt_z = [0,0,-0.089,0,0,0]
    rotate_x = [0,0,0,math.radians(-15),math.radians(0),math.radians(0)]
    move_x = [-197/1000,0,0,0,0,0]

    
    #move x
    relative_move = [-257/1000 - 23/1000,0,0,0,0,0]
    robot.move_add_l(relative_move, 0.5, 0.5)
    
    #rotate around x axis ~20 degrees
    pose1 = robot.get_tcp_pos()
    pose2 = rotate_x
    result_pose = robot.pose_trans(pose1, pose2)
    robot.move_l(result_pose, 0.5, 0.5)

    #move to determined z position (belt z)
    cur_pos = robot.get_tcp_pos()  
    cur_pos[2] = belt_z[2]
    robot.move_l(cur_pos, 1, 3)

    #move x
    robot.move_add_l(move_x, 0.2, 3)


    #rotate back
    pose1 = robot.get_tcp_pos()
    pose2 = rotate_x
    rotate_x[3] *= -1
    result_pose = robot.pose_trans(pose1, pose2)
    result_pose[2] += 6/1000
    result_pose[0] += 5/1000
    robot.move_l(result_pose, 0.5, 3)

    pose1 = robot.get_tcp_pos()
    pose2 = rotate_x
    rotate_x[3] = math.radians(5)
    result_pose = robot.pose_trans(pose1, pose2)
    result_pose[2] += 10/1000
    result_pose[0] += 5/1000
    robot.move_l(result_pose, 0.5, 3)

    #move up
    relative_move=[0,0,200/1000,0,0,0]
    robot.move_add_l(relative_move)


    #rotate around x axis and y
    relative_move = [0,0,0,math.radians(20),math.radians(-20),math.radians(0)]
    pose1 = robot.get_tcp_pos()
    pose2 = relative_move
    result_pose = robot.pose_trans(pose1, pose2)
    robot.move_l(result_pose, 0.1, 0.1)

    #move fast
    relative_move=[0.1,-0.4,0,0,0,0]
    #robot.move_add_l(relative_move, 3, 3)



#connect to robot
robot = URControl("192.168.0.1")
robot.connect()


#set toolframe
tool_frame=[-47.5/1000,-140/1000,102.6/1000,math.radians(-1.2),math.radians(2),math.radians(-5)]
robot.set_tool_frame(tool_frame=tool_frame)
print(robot.get_tcp_pos()) 


#set safe start pos
start_pos = [-0.3968556411508649, 0.049047830881604054, 0.1, 2.1355663224764934, 2.288791439427752, -0.0]
start_pos_2 = [0.21806621866470055, -0.08845418646768148, 0.5716754446825703, 0.2011446368010403, -1.0833366225923702, 2.7864552788165944]

robot.move_l(start_pos, 0.1, 0.1)

pick_parts()

robot.stop_robot_control()