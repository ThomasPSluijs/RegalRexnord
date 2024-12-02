import rtde_control # For controlling the robot
import rtde_receive # For receiving data from the robot
import rtde_io # For robot IO

import time
import logging
import math

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class URControl:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip

        self.rtde_ctrl = None
        self.rtde_rec = None
        self.rtde_inout = None



    #connect to robot
    def connect(self):
        try:
            self.rtde_ctrl = rtde_control.RTDEControlInterface(self.robot_ip) 
            self.rtde_rec = rtde_receive.RTDEReceiveInterface(self.robot_ip)
            self.rtde_inout = rtde_io.RTDEIOInterface(self.robot_ip)
            logging.info(f"Connected to robot: {self.robot_ip}")
        except Exception as e:
            logging.error(f"Error connecting to robot: {e}")

    #stop connection to robot
    def stop_robot_control(self):
        self.rtde_ctrl.stopScript()
        logging.info("stopped connection with robot")



    #set userframe (not working currently)
    def set_user_frame(self, user_frame):
        ur_script = f"set_user_frame(p{user_frame})"
        try:
            self.rtde_ctrl.sendCustomScript(ur_script)
            logging.info(f"set userframe: {user_frame}")
        except Exception as e:
            logging.error(f"Error sending user frame: {e}")

    #set tool frame
    def set_tool_frame(self, tool_frame):
        try:
            self.rtde_ctrl.setTcp(tool_frame)
            logging.info(f"succesfully setted toolframe: {tool_frame}")
        except Exception as e:
            logging.error(f"error setting toolframe: {e}")

    #set payload (not tested). needs payload(kg), center of gravity (CoGx, CoGy, CoGz)
    def set_payload(self, payload, cog):
        try:
            self.rtde_ctrl.setPayLoad(payload, cog)
        except Exception as e:
            logging.error(f"can not set COG or/and payload: {e}")    
            


    #set digital output
    def set_digital_output(self, output_id, state):
        if not self.rtde_ctrl:
            logging.error("error: no connection with robot")
        try:
            self.rtde_inout.setStandardDigitalOut(output_id, state)
            logging.info(f"digital output {output_id} is {state}")
        except Exception as e:
            logging.error(f"Eror setting digital output {output_id}: {e}")

    #pulse digital output. duration in seconds
    def pulse_digital_output(self, output_id, duration):
        self.set_digital_output(output_id=output_id, state=True)
        time.sleep(duration)
        self.set_digital_output(output_id=output_id, state=False)



    #move L
    def move_l(self, pos, speed=0.5, acceleration=0.5, corner_smoothing=0):
        try:
            self.rtde_ctrl.moveL(pos, speed, acceleration, corner_smoothing)
        except Exception as e:
            logging.error(f"can not move: {e}")

            
    #move L
    def move_l_path(self, path):
        try:
            self.rtde_ctrl.moveL(path)
        except Exception as e:
            logging.error(f"can not move: {e}")


    #move j (not tested yet)
    def move_j(self, pos, speed=0.5, acceleration=0.5, corner_smoothing=0):
        try:
            self.rtde_ctrl.moveL(pos, speed, acceleration, corner_smoothing)
        except Exception as e:
            logging.error(f"can not move: {e}")

    #move add (relative movement based of current position
    def move_add_l(self, relative_move, speed=0.5, acceleration=0.5, corner_smoothing=0):
        try:
            current_tcp_pos = self.get_tcp_pos()
            new_linear_move = [current_tcp_pos[i] +  relative_move[i] for i in range(6)]
            self.move_l(new_linear_move, speed, acceleration, corner_smoothing)
        except Exception as e:
            logging.error(f"cannot do relative move: {e}")

    #move add j (relative movement based of current position
    def move_add_j(self, relative_move, speed=0.5, acceleration=0.5, corner_smoothing=0):
        try:
            current_tcp_pos = self.get_tcp_pos()
            new_linear_move = [current_tcp_pos[i] +  relative_move[i] for i in range(6)]
            self.move_j(new_linear_move, speed, acceleration, corner_smoothing)
        except Exception as e:
            logging.error(f"cannot do relative move: {e}")


    #return actual TCP position
    def get_tcp_pos(self):
        try:
            return self.rtde_rec.getActualTCPPose()
        except Exception as e:
            logging.error(f"cannot return actual tcp pose: {e}")



robot_ip = "192.168.0.1" #robot ip
ur_control = URControl(robot_ip=robot_ip)
ur_control.connect()

#ur_control.pulse_digital_output(output_id=0, duration=2)\
#user_frame=[0,0,0,0,0,0]
#ur_control.set_user_frame(user_frame=user_frame)
tool_frame=[0,0,0,0,0,0]
ur_control.set_tool_frame(tool_frame=tool_frame)


safe_pos = [0.38, 0.38, 0.165, 1.5694986535657232, 2.708608418199369, 0.09789163536624904]
#ur_control.move_l(safe_pos, 0.5)


def speed_test():
    #create box_pos_down. other positions will be based of this position
    box_pos_down = [0.38, 0.38, -0.30, 1.5694986535657232, 2.708608418199369, 0.09789163536624904]
    ur_control.move_l(box_pos_down, 1, 1)
    box_pos_down = [0.38, 0.38, -0.30, 1.5694986535657232, 2.708608418199369, 0.09789163536624904,3,3,0]


    #create pos_box_up
    speed_acc_blend = [3,3,0.45]
    pos_box_up = box_pos_down.copy()
    pos_box_up[2] = pos_box_up[2] + 500/1000
    x = 6
    for y in speed_acc_blend:
        pos_box_up[x]=y
        x+=1
    print(pos_box_up)


    #create pos_belt_up
    speed_acc_blend = [3,3,0.09]
    pos_belt_up = pos_box_up.copy()
    pos_belt_up[1] = pos_belt_up[1] - 1100/1000
    x = 6
    for y in speed_acc_blend:
        pos_belt_up[x]=y
        x+=1
    print(pos_belt_up)


    #create pos_belt_down
    speed_acc_blend = [3,3,0.00]
    pos_belt_down = pos_belt_up.copy()
    pos_belt_down[2] = pos_belt_down[2] + -100/1000
    x = 6
    for y in speed_acc_blend:
        pos_belt_down[x]=y
        x+=1


    path = [
        # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
        box_pos_down,  # Eerste positie
        pos_box_up,  # Tweede positie
        pos_belt_up,  # Derde positie
        pos_belt_down,  # Vierde positie
        # Voeg meer posities toe zoals nodig
    ]
    ur_control.move_l_path(path=path)

    path = [
        # Positie 1: [X, Y, Z, RX, RY, RZ, snelheid, versnelling, blend]
        pos_belt_down,  # Eerste positie
        pos_belt_up,  # Tweede positie
        pos_box_up,  # Derde positie
        box_pos_down,  # Vierde positie
        # Voeg meer posities toe zoals nodig
    ]
    ur_control.move_l_path(path=path)
    

speed_test()

ur_control.stop_robot_control()
