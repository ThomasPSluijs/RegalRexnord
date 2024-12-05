from UR5E_control import URControl
import math

def pick_parts():
    belt_z = [0,0,-0.085-6/1000,0,0,0]
    rotate_x = [0,0,0,math.radians(-20),math.radians(0),math.radians(0)]
    move_x = [175/1000,0,0,0,0,0]

    

    
    
    #rotate around x axis ~20 degrees
    pose1 = robot.get_tcp_pos()
    pose2 = rotate_x
    result_pose = robot.pose_trans(pose1, pose2)
    robot.move_l(result_pose, 0.1, 0.1)

    #move to determined z position (belt z)
    cur_pos = robot.get_tcp_pos()  
    cur_pos[2] = belt_z[2]
    robot.move_l(cur_pos, 0.1, 0.1)

    robot.move_add_l(move_x, 0.1, 0.1)



#connect to robot
robot = URControl("192.168.0.1")
robot.connect()


#set toolframe
tool_frame=[-47.5/1000,-140/1000,102.6/1000,math.radians(0),math.radians(0),math.radians(-5)]
robot.set_tool_frame(tool_frame=tool_frame)
print(robot.get_tcp_pos()) 


#set safe start pos
start_pos = [0.44, -0.04, 0.1, -2.258, 2.11 - math.radians(2), 0]
robot.move_l(start_pos, 0.1, 0.1)

pick_parts()

robot.stop_robot_control()