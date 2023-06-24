import os

folder_path = "Coordinator/coord/data/"  # Replace with the folder path you want to delete files from
file_extension = ".npy"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)



folder_path = "Coordinator/coord/data/"  # Replace with the folder path you want to delete files from
file_extension = ".py"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)



folder_path = "Worker/worker/data/"  # Replace with the folder path you want to delete files from
file_extension = ".npy"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)



folder_path = "Worker/worker/data/"  # Replace with the folder path you want to delete files from
file_extension = ".py"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)


