import time
import logging
from configuration import*

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)



class Conveyor():
    def __init__(self):
        pass
        #self.running = False

    def run(self, robot):
        try:
            output_id = 0

            while True:
                logging.info("Turning conveyor ON")
                #self.running = False
                robot.set_digital_output(output_id, True)
                time.sleep(15)  # Conveyor ON for 15 seconds
                
                logging.info("Turning conveyor OFF")
                #self.running = False
                robot.set_digital_output(output_id, False)
                time.sleep(45)  # Conveyor OFF for 45 seconds

        except Exception as e:
            logging.error(f"Error controlling conveyor: {e}")
