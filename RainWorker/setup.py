import subprocess

PACKAGES = [
    "grpcio==1.56.0",
    "grpcio-tools==1.56.0",
    'protobuf>=4.21.6,<5.0',
    "dill==0.3.6",
    'numpy>=1.22,<1.24',
    "torch==2.0.1",
    'keras>=2.12,<2.13',
    "tensorflow==2.12.0",
    'azure-mgmt-compute==29.1.0',
    'azure-mgmt-core==1.4.0',
    'azure-mgmt-network==23.0.0',
    'azure-mgmt-resource==23.0.0',
    'azure-storage-blob==12.13.0',
    'azure-identity==1.12.0',
    'azure-common==1.1.28'
]


def install_packages():
    for package in PACKAGES:
        try:
            subprocess.check_call(["pip", "install", package])
            print(f"Successfully installed: {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install: {package}")
    try:
        # pip install -i https://test.pypi.org/simple/ Rain
        subprocess.check_call(["pip", "install", "-i", "https://test.pypi.org/simple/", "Rain"])
        print(f"Successfully installed: Rain")
    except subprocess.CalledProcessError:
        print(f"Failed to install: Rain")    

from Rain.Worker.WorkerAmbassador import WorkerAmbassador

BASE_PORT = 50151
CHUNK_SIZE = 1024*1024
 
def start_rain_worker(port=BASE_PORT, chunk_size=CHUNK_SIZE):
    print(f"A worker will be instantiated...")
    worker = WorkerAmbassador(port, chunk_size)
    print(f"The worker will serve on port: {port}")
    worker.serve()
    print(f"The worker is serving on port: {port} now!")
    worker.wait_for_termination()
    print(f"The worker is terminated!")

if __name__ == "__main__":
    install_packages()
    start_rain_worker()

