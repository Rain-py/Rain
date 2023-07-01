from concurrent import futures # indicates the num of workers (threads)
import grpc
import sys
sys.path.append('../')
from protos import provisioner_pb2, provisioner_pb2_grpc
sys.path.pop()


class GlueProvisioner(provisioner_pb2_grpc.provisionerServicer):
    def __init__(self):
        self.ips = [] 
        self.statuses = []
        self.ports = []
        self.ids = []
        self.workers = []
        self.num_workers = 0
        self.server = None

    def __del__(self):
        self.stop_serving()
     # sendStatus() returns (WorkerStatus) {}
    def SendStatus(self, request, context):
        try:
            print("Received request from the coordinator to send status", request)            
            print(f"Status\n IPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")
            return provisioner_pb2.WorkerStatus(IPs = self.ips, statuses = self.statuses, ports = self.ports, ids = self.ids)
        except Exception as e:
            print("Error sending status:", e)
            return provisioner_pb2.WorkerStatus(IPs = [], statuses = [], ports = [], ids = [])

    # DefineNWorkers(NumOfWorkers) returns () {}
    def DefineNWorkers(self, request, context):
        try:
            self.num_workers = request.NumOfWorkers
            print("Number of workers is:", self.num_workers)
            return provisioner_pb2.response(message = "Success receiving the number of workers")
        except Exception as e:
            print("Error receiving the number of workers: ", e)
            return provisioner_pb2.response(message = "Error receiving the number of workers")
    
    def create_workers(self):
        pass
    def delete_workers(self):
        pass
    def get_num_workers(self):
        return self.num_workers
    def start_coordinator(self):
        pass
    
    def stop_serving(self):
        if self.server:
            self.server.stop(0)

    def serve(self):
        try:
            # create a gRPC server
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
            # add the provisioner to the server
            provisioner_pb2_grpc.add_provisionerServicer_to_server(self, self.server)
            # listen on port 50054
            self.server.add_insecure_port('[::]:50054')
            # start the server
            self.server.start()
            print("provisioner is serving")
            
            self.start_coordinator()

            while self.num_workers == 0:
                continue
            # create the workers
            self.workers  = self.create_workers()
            return

        except Exception as e:
            print("Error in the provisioner server: ", e)
            return

        
