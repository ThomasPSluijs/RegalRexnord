#configuration

pickup_tcp = [-47.5/1000,-147/1000,135/1000,0,0,0]          #edge of part (x=centerpart, y=edge)
rotate_tcp = [-47.5/1000, 42/1000, 135/1000, 0, 0, 0]
placement_tcp = [-47.5/1000,-49/1000,135/1000,0,0,0]        #center of part (x=center,y=center)

speed_fast = 2.5
acc_fast = 2.5



import logging
from logging.handlers import TimedRotatingFileHandler

# Path to log file in the logs folder
log_file = 'logs/regalrexnord.log'

# Configure the TimedRotatingFileHandler to create a new log file each day and keep 7 days of logs
file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s'))

# Configure the StreamHandler to log to the terminal
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s'))

# Basic configuration for logging
logging.basicConfig(
    level=logging.INFO,  # Set global logging level
    handlers=[file_handler, console_handler]  # Add the handlers
)

# Example usage
logging.info("This is an info message.")
logging.warning("This is a warning message.")
