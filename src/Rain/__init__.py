from Rain.Worker.WorkerAmbassador import WorkerAmbassador
BASE_PORT = 50151

def start_rain_worker():
    print(f"A worker will be instantiated...")
    worker = WorkerAmbassador(BASE_PORT)
    print(f"The worker will serve on port:{BASE_PORT}")
    worker.serve()
    print(f"The worker is serving on port:{BASE_PORT} now!")
    worker.wait_for_termination()
    print(f"The worker is terminated!")
