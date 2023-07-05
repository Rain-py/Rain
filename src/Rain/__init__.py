from Rain.Worker.WorkerAmbassador import WorkerAmbassador
import argparse

BASE_PORT = 50151

def start_rain_worker(port=BASE_PORT):
    print(f"A worker will be instantiated...")
    worker = WorkerAmbassador(port)
    print(f"The worker will serve on port: {port}")
    worker.serve()
    print(f"The worker is serving on port: {port} now!")
    worker.wait_for_termination()
    print(f"The worker is terminated!")

def main():
    parser = argparse.ArgumentParser(description="Rain Worker Starter")
    parser.add_argument("--port", type=int, default=BASE_PORT, help="Port number for the worker to serve on")
    args = parser.parse_args()
    start_rain_worker(args.port)
