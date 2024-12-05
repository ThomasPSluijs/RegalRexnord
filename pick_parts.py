from UR5E_control import URControl
import math

def pick_parts():
    belt_z = [0,0,0.1,0,0,0]
    rotate_x = [0,0,0,math.radians(-20),math.radians(0),math.radians(0)]
    move_y = [200/1000,0,0,0,0,0]

    
    cur_pos = robot.get_tcp_pos()  #get current pos
    cur_pos[2] = belt_z
    robot.move_l(cur_pos, 0.1, 0.1)

    robot.move_add_l(move_y, 0.1, 0.1)
    pose1 = robot.get_tcp_pos()
    pose2 = rotate_x
    result_pose = robot.pose_trans(pose1, pose2)
    robot.move_l(result_pose, 0.1, 0.1)



robot = URControl("192.168.0.1")
robot.connect()


tool_frame=[-47.5/1000,-140/1000,102.6/1000,math.radians(0),math.radians(0),math.radians(0)]
robot.set_tool_frame(tool_frame=tool_frame)
print(robot.get_tcp_pos()) 


start_pos = [0.44, -0.0, 0.32, -2.258, 2.11, 0]
robot.move_j(start_pos, 0.1, 0.1)

pick_parts()

robot.stop_robot_control()