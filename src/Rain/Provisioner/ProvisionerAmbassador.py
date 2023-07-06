from concurrent import futures # indicates the num of workers (threads)
import grpc
from Rain.Protos import provisioner_pb2, provisioner_pb2_grpc, worker_pb2, worker_pb2_grpc
from Rain.LogService.LogService import LogService


class ProvisionerAmbassador(provisioner_pb2_grpc.provisionerServicer):
    def __init__(self):
        self.ips = [] 
        self.statuses = []
        self.ports = []
        self.ids = []
        self.workers = []
        self.num_workers = 0
        self.server = None
        self.logger = LogService("ProvisionerAmbassador")

    def __del__(self):
        try:
            self.stop_serving()
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return

    # sendStatus() returns (WorkerStatus) {}
    def SendStatus(self, request: provisioner_pb2.emptyMessage, context: grpc.ServicerContext) -> provisioner_pb2.WorkerStatus:
        """
        This function will be called from the coordinator side to get the status of the workers.

        Args:
            request (provisioner_pb2.StatusRequest): A `StatusRequest` message sent by the coordinator.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `WorkerStatus` message containing the IP addresses, port numbers, statuses, and IDs of the workers.
        """
        try:
            self.logger.log('debug', f"Received '{request}' from the coordinator to send status")
            self.logger.log('debug', f"Workers\nIPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")
            return provisioner_pb2.WorkerStatus(IPs = self.ips, statuses = self.statuses, ports = self.ports, ids = self.ids)
        except Exception as e:
            self.logger.log('error', f"Error sending status: {e}")
            return provisioner_pb2.WorkerStatus(IPs = [], statuses = [], ports = [], ids = [])

    # DefineNWorkers(NumOfWorkers) returns () {}
    def DefineNWorkers(self, request: provisioner_pb2.NumOfWorkers, context: grpc.ServicerContext) -> provisioner_pb2.response:
        """
        This function will be called from the coordinator side define the number of workers to be created.

        Args:
            request (provisioner_pb2.NumOfWorkersRequest): A `NumOfWorkersRequest` message sent by the coordinator.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `response` message indicating whether the request was successful or not.
        """
        try:
            self.num_workers = request.NumOfWorkers
            self.logger.log('debug', f"Received '{request}' from the coordinator to define the number of workers")
            return provisioner_pb2.response(message = "Success receiving the number of workers")
        except Exception as e:
            self.logger.log('error', f"Error receiving the number of workers: {e}")
            return provisioner_pb2.response(message = "Error receiving the number of workers")

    def SolveFailureWorker(self, request: provisioner_pb2.FailureWorker, context: grpc.ServicerContext) -> provisioner_pb2.NewWorker:
        """
        This function will be called from the coordinator side to solve the failure of a worker.

        Args:
            request (provisioner_pb2.FailureWorker): A `FailureWorker` message sent by the coordinator.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `NewWorker` message containing the IP address, port number, and ID of the new worker.
        """
        try:
            self.logger.log('debug', f"Received request from the coordinator to solve the failure of a worker {request.worker_id + 1}")
            self.create_worker(request.worker_id)
            return provisioner_pb2.NewWorker(new_worker_ip=self.ips[request.worker_id], new_worker_port=self.ports[request.worker_id], new_worker_status=self.statuses[request.worker_id])
        except Exception as e:
            self.logger.log('error', f"Error solving the failure of a worker: {e}")
            return provisioner_pb2.NewWorker(new_worker_ip = "", new_worker_port = 0, new_worker_status = 0)

    def start_coordinator(self)         -> None:
        pass
    def create_workers(self)            -> None:
        pass
    def create_worker(self, worker_id)  -> None:
        pass
    def get_num_workers(self)           -> int:
        return self.num_workers
    def delete_workers(self)            -> None:
        pass
    def stop_worker(self,worker_ip, worker_port):
        try:
            with grpc.insecure_channel(worker_ip + f":{str(worker_port)}") as channel:
                worker_stub = worker_pb2_grpc.workerStub(channel)
                worker_stub.StopWorker(worker_pb2.StopSignal(message = "Stop the worker"))
                return 
        except Exception as e:
            self.logger.log('error', f"Error stopping worker {worker_ip}:{worker_port}: {e}")
            return 
    
    def stop_serving(self) -> None:
        """
        Stops the gRPC server for the provisioner.

        Returns:
            None
        """
        try:
            self.delete_workers()
        except Exception as e:
            self.logger.log('error', f"Error deleting workers: {e}")
            
        try:
            if self.server:
                self.server.stop(0)
                self.logger.log('info', "provisioner stopped serving")
        except Exception as e:
            self.logger.log('error', f"Error stopping serving: {e}")
            return

    def serve(self) -> None:
        """
        Starts the gRPC server for the provisioner.

        Returns:
            None
        """
        try:
            # create a gRPC server
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
            # add the provisioner to the server
            provisioner_pb2_grpc.add_provisionerServicer_to_server(self, self.server)
            # listen on port 50054
            self.server.add_insecure_port('[::]:50054')
            # start the server
            self.server.start()
            self.logger.log('info', "provisioner is serving")
            
            self.start_coordinator()

            # busy wait until receiving the number of workers
            while self.num_workers == 0:
                continue
            # create the workers
            self.workers  = self.create_workers()
            return

        except Exception as e:
            self.logger.log('error', f"Error in the provisioner server: {e}")
            return

        
