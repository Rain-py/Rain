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

is_port_open(host, port)
