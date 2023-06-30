import os

def clean():
    folder_paths = ["Coordinator/coord/data/", "Worker/worker/data/", "Divider/divider/data"]  # Replace with the folder path you want to delete files from
    file_extensions = [".npy", ".py", ".pkl"]  # Replace with the file extension you want to delete
    for folder_path in folder_paths:
        for filename in os.listdir('../../'+folder_path):
            for file_extension in file_extensions:
                if filename.endswith(file_extension):
                    file_path = os.path.join('../../'+folder_path, filename)
                    os.remove(file_path)


