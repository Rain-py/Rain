import logging

class LogService:
    """
    The LogService class follows the Singleton pattern,
    by ensuring that only one instance of LogService is created and shared.
    """
    __instance = None

    @staticmethod
    def get_instance():
        """
        Static method to retrieve the instance of the LogService.
        If an instance doesn't exist, it creates one.
        """
        if LogService.__instance is None:
            LogService()
        return LogService.__instance

    def __init__(self):
        """Private constructor to create the LogService instance."""
        if LogService.__instance is not None: # To prevent multiple instances of LogService from being created
            raise Exception("LogService is a Singleton class. Use get_instance() to retrieve the instance.")
        else:
            LogService.__instance = self
            self.logger = logging.getLogger("RainLogger")
            self.logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(module)s] %(message)s')
            handler = logging.StreamHandler()  # Output logs to the console
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

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

# Usage example
if __name__ == "__main__":
    log_service = LogService.get_instance()
    log_service2 = LogService.get_instance()
    log_service2 = LogService.get_instance()
    id = 1
    log_service.log('info', f'This is an informational message {id}')
    log_service.log('error', 'An error occurred.')

