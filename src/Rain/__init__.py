from Rain.Worker.WorkerAmbassador import WorkerAmbassador
import argparse

BASE_PORT = 50151
CHUNK_SIZE = 1024*1024
 
def start_rain_worker(port=BASE_PORT, chunk_size=CHUNK_SIZE, setup='ML'):
    print(f"A worker will be instantiated...")
    worker = WorkerAmbassador(port, chunk_size, setup)
    print(f"The worker will serve on port: {port}")
    worker.serve()
    print(f"The worker is serving on port: {port} now!")
    worker.wait_for_termination()
    print(f"The worker is terminated!")

def main():
    parser = argparse.ArgumentParser(description="Rain Worker Starter")
    parser.add_argument("--port", type=int, default=BASE_PORT, help="Port number for the worker to serve on")
    parser.add_argument("--chunk_size", type=int, default=CHUNK_SIZE, help="chunk size for file transmission")
    parser.add_argument("--setup", type=str, default="ML", help="The setup of the worker: ML, TF, PT")
    args = parser.parse_args()
    start_rain_worker(args.port, args.chunk_size, args.setup)
