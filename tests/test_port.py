import socket



def is_port_open(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # Set a timeout value for the connection attempt
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"Port {port} is open on {host}")
        else:
            print(f"Port {port} is closed on {host}")
        sock.close()
    except socket.error as e:
        print(f"Error: {e}")

# Usage example
host = '4.246.210.118'  # Replace with the target host or IP address
port = 50151  # Replace with the target port

# is_port_open(host, port)

tf_lib = 0 == 0
torch_lib = 1 == 0
setup_script = "#cloud-config\n\nruncmd:\n  - sudo apt-get update\n  - sudo apt-get install -y apache2\n  - sudo apt install -y python3-pip\n  - sudo git clone https://gist.github.com/Mostafa-wael/ebd011579b7120e336e58671e5239248\n  - echo 'Installing...' > /var/www/html/index.html\n  - cd /ebd011579b7120e336e58671e5239248\n  - sudo chmod 777 setup.sh\n  - sudo ./setup.sh\n  - echo 'Done Installing ..' > /var/www/html/index.html\n"
install_tf_script = "  - sudo pip install keras>=2.12,<2.13\n  - sudo pip install tensorflow==2.12.0\n"
install_torch_script = "  - sudo pip install torch==2.0.1\n"
start_rain_worker = "  - sudo start_rain_worker\n"
custom_data_script = setup_script + install_tf_script * tf_lib + install_torch_script * torch_lib + start_rain_worker

print(custom_data_script)
