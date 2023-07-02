import logging
from logging.handlers import RotatingFileHandler
import os

class LogService:

    def __init__(self, name='RainLog'):
        """Private constructor to create the LogService instance."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s')
        console_handler = logging.StreamHandler()  # Output logs to the console
        console_handler.setFormatter(formatter)
        log_file_path = f"./logs/{name}.log"
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path) 
        file_handler = RotatingFileHandler(log_file_path, maxBytes=1024*20, backupCount=0)  # Output logs to a rotating file
        file_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def log(self, level, message):
        """Log a message with the specified log level."""
        if level == 'debug':
            self.logger.debug(message)
        elif level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'critical':
            self.logger.critical(message)
        else:
            raise ValueError("Invalid log level specified.")

# # Usage example
# if __name__ == "__main__":
#     log_service = LogService()
#     log_service2 = LogService()
#     log_service2 = LogService()
#     id = 1
#     log_service.log('info', f'This is an informational message {id}')
#     log_service.log('error', 'An error occurred.')
#     log_service2.log('warning', 'This is a warning message.')
