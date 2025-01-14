import socket
import logging

class URControl:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        self.robot_socket = None

    def connect(self):
        try:
            self.robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.robot_socket.connect((self.robot_ip, 29999))
            logging.info(f"Connected to robot: {self.robot_ip}")
        except Exception as e:
            logging.error(f"Failed to connect to robot: {e}")
            raise

    def set_operational_mode(self, mode):
        try:
            command = f"set operational mode {mode}\n"
            self.robot_socket.sendall(command.encode())
            data = self.robot_socket.recv(1024)
            data = data.decode('utf-8').strip()
            logging.info(f"Set operational mode response: {data}")

            if "Failed" in data:
                logging.error(f"Failed setting operational mode: {mode}")
                return False
            logging.info(f"Successfully set operational mode: {mode}")
            return True
        except Exception as e:
            logging.error(f"Error setting operational mode: {e}")
            return False

    def close_connection(self):
        if self.robot_socket:
            self.robot_socket.close()
            logging.info("Closed socket connection with robot")

def main():
    robot_ip = "192.168.0.1"  # Replace with your robot's IP address
    ur_control = URControl(robot_ip)

    try:
        ur_control.connect()
        if ur_control.set_operational_mode("automatic"):
            print("Successfully set operational mode to automatic.")
        else:
            print("Failed to set operational mode to automatic.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ur_control.close_connection()

if __name__ == "__main__":
    main()