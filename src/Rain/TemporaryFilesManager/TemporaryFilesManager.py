import os
import shutil
from Rain.LogService.LogService import LogService

class TemporaryFilesManager:
    __instance = None

    @staticmethod
    def get_instance(temp_dir=None):
        if TemporaryFilesManager.__instance is None:
            TemporaryFilesManager(temp_dir)
        return TemporaryFilesManager.__instance

    def __init__(self, temp_dir):
        if TemporaryFilesManager.__instance is not None:
            raise Exception("TemporaryFileManager is a singleton class. Use get_instance() to retrieve the instance.")
        else:
            TemporaryFilesManager.__instance = self
            self.temp_dir = os.getenv('TEMP') if os.name == 'nt' else '/tmp'
            self.temp_dir = temp_dir if temp_dir is not None else self.temp_dir
            self.temp_dir = f'{self.temp_dir}/RainData'
            self.temp_dirs = []
            self.logger = LogService(f"TemporaryFilesManager")
    
    def __del__(self):
        try:
            self.logger.info("TemporaryFilesManager is destroyed")
            self.cleanup_temp_dirs()
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return

    def create_temp_dir(self, dir_name):
        temp_dir_path = os.path.join(self.temp_dir, dir_name)
        os.makedirs(temp_dir_path, exist_ok=True)
        self.logger.log('debug', f"Created temporary directory {temp_dir_path}")
        self.temp_dirs.append(temp_dir_path)
        return temp_dir_path

    def cleanup_temp_dirs(self):
        for temp_dir in self.temp_dirs:
            # if dir exists
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()
        self.logger.log('debug', f"Temporary directories are cleaned up")


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
