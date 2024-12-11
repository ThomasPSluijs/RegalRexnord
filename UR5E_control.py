import rtde_control # For controlling the robot
import rtde_receive # For receiving data from the robot
import rtde_io # For robot IO

import time
import logging
import numpy as np



logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


##########################
#class for controlling UR robot with UR_RDTE. gives easy way to use the library. 
# you need to enter the robot ip. us connect() for connecting etc.
##########################
class URControl:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip

        self.rtde_ctrl = None
        self.rtde_rec = None
        self.rtde_inout = None



    # Connect to robot with retry logic
    def connect(self):
        max_retries = 10
        retry_delay = 0.5  # Delay in seconds between retries


        for attempt in range(1, max_retries + 1):
            try:
                self.rtde_ctrl = rtde_control.RTDEControlInterface(self.robot_ip)
                self.rtde_rec = rtde_receive.RTDEReceiveInterface(self.robot_ip)
                self.rtde_inout = rtde_io.RTDEIOInterface(self.robot_ip)
                logging.info(f"Connected to robot: {self.robot_ip} on attempt {attempt}")
                return  # Exit the method upon successful connection
            except Exception as e:
                logging.error(f"Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)  # Wait before retrying
                else:
                    logging.error("Max retries reached. Unable to connect to the robot.")
                    raise

    #stop connection to robot
    def stop_robot_control(self):
        if self.rtde_ctrl.isConnected():
            self.rtde_ctrl.stopScript()
            logging.info("stopped connection with robot")
        else:
            logging.warning("not connected to robot")



    #set tool frame (TCP frame)
    def set_tool_frame(self, tool_frame):
        if self.rtde_ctrl.isConnected():
            try:
                self.rtde_ctrl.setTcp(tool_frame)
                logging.info(self.rtde_ctrl.getTCPOffset())
                logging.info(f"succesfully setted toolframe: {tool_frame}")
            except Exception as e:
                logging.error(f"error setting toolframe: {e}")
        else:
            logging.warning("not connected to robot")

    #set payload (not tested). needs payload(kg), center of gravity (CoGx, CoGy, CoGz)
    def set_payload(self, payload, cog):
        if self.rtde_ctrl:
            try:
                self.rtde_ctrl.setPayLoad(payload, cog)
            except Exception as e:
                logging.error(f"can not set COG or/and payload: {e}")    
        else:
            logging.warning("not connected to robot")
            


    #set digital output
    def set_digital_output(self, output_id, state):
        if self.rtde_inout:
            try:
                self.rtde_inout.setStandardDigitalOut(output_id, state)
                logging.info(f"digital output {output_id} is {state}")
            except Exception as e:
                logging.error(f"Eror setting digital output {output_id}: {e}")
        else:
            logging.warning("not connected to robot")

    #pulse digital output. duration in seconds
    def pulse_digital_output(self, output_id, duration):
        self.set_digital_output(output_id=output_id, state=True)
        time.sleep(duration)
        self.set_digital_output(output_id=output_id, state=False)



    #move L
    def move_l(self, pos, speed=0.5, acceleration=0.5):
        if self.rtde_ctrl.isConnected():
            try:
                self.rtde_ctrl.moveL(pos, speed, acceleration)
            except Exception as e:
                logging.error(f"can not move: {e}")
        else:
            logging.warning("not connected to robot")

    #move L path
    def move_l_path(self, path):
        if self.rtde_ctrl.isConnected():
            try:
                self.rtde_ctrl.moveL(path)
            except Exception as e:
                logging.error(f"can not move: {e}")
        else:
            logging.warning("not connected to robot")

    #move j (not tested yet)
    def move_j(self, pos, speed=0.5, acceleration=0.5):
        if self.rtde_ctrl.isConnected():
            try:
                self.rtde_ctrl.moveJ(pos, speed, acceleration)
            except Exception as e:
                logging.error(f"can not move: {e}")
        else:
            logging.warning("not connected to robot")

    #move add (relative movement based of current position
    def move_add_l(self, relative_move, speed=0.5, acceleration=0.5):
        if self.rtde_ctrl.isConnected():
            try:
                current_tcp_pos = self.get_tcp_pos()
                new_linear_move = [current_tcp_pos[i] +  relative_move[i] for i in range(6)]
                self.move_l(new_linear_move, speed, acceleration)
            except Exception as e:
                logging.error(f"cannot do relative move: {e}")
        else:
            logging.warning("not connected to robot")

    #move add j (relative movement based of current position
    def move_add_j(self, relative_move, speed=0.5, acceleration=0.5):
        if self.rtde_ctrl.isConnected():
            try:
                current_tcp_pos = self.get_tcp_pos()
                new_linear_move = [current_tcp_pos[i] +  relative_move[i] for i in range(6)]
                self.move_j(new_linear_move, speed, acceleration)
            except Exception as e:
                logging.error(f"cannot do relative move: {e}")
        else:
            logging.warning("not connected to robot")


    #help functions for pose_trans
    def rodrigues_to_rotation_matrix(self,r):
        """Converteer een rodrigues-vector naar een rotatiematrix."""
        theta = np.linalg.norm(r)
        if theta < 1e-6:  # Geen rotatie
            return np.eye(3)
        k = r / theta
        K = np.array([
            [0, -k[2], k[1]],
            [k[2], 0, -k[0]],
            [-k[1], k[0], 0]
        ])
        return np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * np.dot(K, K)

    def pose_to_matrix(self,pose):
        """Converteer een 6D-pose naar een 4x4 transformatie-matrix."""
        R = self.rodrigues_to_rotation_matrix(pose[3:])  # Rotatie
        t = np.array(pose[:3])  # Translatie
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t
        return T

    def matrix_to_pose(self,matrix):
        """Converteer een 4x4 transformatie-matrix terug naar een 6D-pose."""
        R = matrix[:3, :3]
        t = matrix[:3, 3]
        theta = np.arccos((np.trace(R) - 1) / 2)
        if theta < 1e-6:
            r = np.zeros(3)
        else:
            r = theta / (2 * np.sin(theta)) * np.array([
                R[2, 1] - R[1, 2],
                R[0, 2] - R[2, 0],
                R[1, 0] - R[0, 1]
            ])
        return np.concatenate((t, r))

    def pose_trans(self,pose1, pose2):
        """Combineer twee poses met behulp van matrixvermenigvuldiging."""
        T1 = self.pose_to_matrix(pose1)
        T2 = self.pose_to_matrix(pose2)
        T_result = np.dot(T1, T2)
        return self.matrix_to_pose(T_result)


    #return actual TCP position
    def get_tcp_pos(self):
        if self.rtde_rec.isConnected():
            try:
                return self.rtde_rec.getActualTCPPose()
            except Exception as e:
                logging.error(f"cannot return actual tcp pose: {e}")
        else:
            logging.warning("not connected to robot")


    def set_tcp_rotation(self,rx, ry, rz,speed=0.1,acc=0.1):
        if self.rtde_ctrl.isConnected():
            """
            Sets the rotation of the tool center point (TCP).

            Args:
                rx (float): Rotation around the X-axis in degrees.
                ry (float): Rotation around the Y-axis in degrees.
                rz (float): Rotation around the Z-axis in degrees.

            Returns:
                None
            """
            # Get the current TCP pose
            current_pose = self.get_tcp_pose()  # Assume this returns [x, y, z, rx, ry, rz]

            # Update the rotation components
            current_pose[3] = rx  # Set rotation around X-axis
            current_pose[4] = ry  # Set rotation around Y-axis
            current_pose[5] = rz  # Set rotation around Z-axis

            # Move the robot to the new rotation
            self.move_l(current_pose, speed, acc)  # Execute a linear move to the updated pose

