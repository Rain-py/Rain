import os
import shutil
from Rain.LogService.LogService import LogService
import Rain

class TemporaryFilesManager:
    __instance = None

    @staticmethod
    def get_instance(temp_dir : str = None) -> Rain.TemporaryFilesManager:
        """
        Function to get the instance of the TemporaryFilesManager.

        Args:
            temp_dir (str, optional): Temporary file storage directory. Defaults to None.
        
        Returns:
            Rain.TemporaryFilesManager: the instance of the TemporaryFilesManager.
        """
        if TemporaryFilesManager.__instance is None:
            TemporaryFilesManager(temp_dir)
        return TemporaryFilesManager.__instance

    def __init__(self, temp_dir : str):
        """
        Function to initialize the TemporaryFilesManager it must be initialized once.

        Args:
            temp_dir (str): Temporary file storage directory. (if None, it will be set to the default temp directory)

        Raises:
            Exception: if the TemporaryFilesManager is already initialized.
        """
        if TemporaryFilesManager.__instance is not None:
            raise Exception("TemporaryFileManager is a singleton class. Use get_instance() to retrieve the instance.")
        else:
            TemporaryFilesManager.__instance = self
            self.temp_dir = os.getenv('TEMP') if os.name == 'nt' else '/tmp'
            self.temp_dir = temp_dir if temp_dir is not None else self.temp_dir
            self.temp_dir = f'{self.temp_dir}/RainData'
            self.temp_dirs = []

            # create a logger for the TemporaryFilesManager.
            self.logger = LogService(f"TemporaryFilesManager")
    
    def __del__(self):
        """
        Function to clean the temp directory and delete the TemporaryFilesManager's logger befor deleting instance.
        """
        try:
            self.logger.info("TemporaryFilesManager is destroyed")
            self.cleanup_temp_dirs()
            del self.logger
            return
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return


    def cleanup_temp_dirs(self):
        """
        Function to clean the Temporary directories and delete it.
        """
        for temp_dir in self.temp_dirs:
            # if dir exists
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()
        self.logger.log('debug', f"Temporary directories are cleaned up")

    # def create_temp_dir(self, dir_name):
    #     temp_dir_path = os.path.join(self.temp_dir, dir_name)
    #     os.makedirs(temp_dir_path, exist_ok=True)
    #     self.logger.log('debug', f"Created temporary directory {temp_dir_path}")
    #     self.temp_dirs.append(temp_dir_path)
    #     return temp_dir_path

# Usage example
# if __name__ == "__main__":
#     temp_manager = TemporaryFilesManager.get_instance()

#     temp_dir_path = temp_manager.create_temp_dir('mydir/data/')

#     temp_file_path = os.path.join(temp_dir_path, 'temp_file.txt')
#     print ('Creating temporary file at: ' + temp_file_path)
#     with open(temp_file_path, 'w') as temp_file:
#         temp_file.write('This is a temporary file.')

#     # Use the temporary file
#     with open(temp_file_path, 'r') as temp_file:
#         content = temp_file.read()
#         print(content)

#     temp_manager.cleanup_temp_dirs()
