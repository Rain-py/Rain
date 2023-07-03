from Rain.Worker.CloudWorker import CloudWorker

if __name__ == '__main__':
    worker = CloudWorker(50051)
    worker.serve()