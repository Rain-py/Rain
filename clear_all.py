import os

folder_path = "coord/X_train/"  # Replace with the folder path you want to delete files from
file_extension = ".npy"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)



folder_path = "coord/Y_train/"  # Replace with the folder path you want to delete files from
file_extension = ".npy"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)


folder_path = "coord/"  # Replace with the folder path you want to delete files from
file_extension = ".py"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)

folder_path = "coord/"  # Replace with the folder path you want to delete files from
file_extension = ".h5"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)


folder_path = "worker/X_train/"  # Replace with the folder path you want to delete files from
file_extension = ".npy"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)



folder_path = "worker/Y_train/"  # Replace with the folder path you want to delete files from
file_extension = ".npy"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)


folder_path = "worker/"  # Replace with the folder path you want to delete files from
file_extension = ".py"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)

folder_path = "worker/"  # Replace with the folder path you want to delete files from
file_extension = ".h5"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)


folder_path = "divider/"  # Replace with the folder path you want to delete files from
file_extension = ".h5"  # Replace with the file extension you want to delete

for filename in os.listdir(folder_path):
    if filename.endswith(file_extension):
        file_path = os.path.join(folder_path, filename)
        os.remove(file_path)