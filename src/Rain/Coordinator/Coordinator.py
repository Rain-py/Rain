from __future__ import print_function
from concurrent import futures  # indicates the num of (threads)
import os
import grpc
import threading
from typing import List, Tuple, Any, Iterator
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService
from Rain.Protos import (
    coord_pb2,
    coord_pb2_grpc,
    provisioner_pb2,
    provisioner_pb2_grpc,
)

## Coordinator class
class Coordinator(coord_pb2_grpc.coordinatorServicer):
    def __init__(self, divider_IP: str, provisioner_IP: str, num_of_workers : int, num_partitions :int) -> None:
        """
        Initializes the Coordinator object.

        Args:
            divider_IP (str): The IP address of the Divider.
            provisioner_IP (str): The IP address of the Provisioner.
            num_of_workers (int): The number of workers to create.
            num_partitions (int): The number of partitions to create.

        Returns:
            None
        """
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('coord/')
        self.server  = None
        self.logger = LogService("Coordinator")
        self.logger.log('debug', f"Coordinator is initialized")
        self.divider_IP = divider_IP  
        self.provisioner_IP = provisioner_IP
        self.num_of_workers = num_of_workers
        self.num_partitions = num_partitions

        self.options = [('grpc.max_send_message_length', 10 * 1024 * 1024),
               ('grpc.max_receive_message_length', 10 * 1024 * 1024)]
        
    def __del__(self):
        try:
            self.stop_serving()
        except Exception as e:
            self.logger.log('error', f"Error deleting: {e}")
            return

    def set_num_of_workers(self, num_of_workers: int) -> None:
        """
        Sends the number of workers to the Provisioner.

        Args:
            num_of_workers (int): The number of workers to create.

        Returns:
            None
        """
        try:
            self.logger.log('debug', f"sending the num of workers to the provisioner")
            # instantiate a channel to the provisioner
            with grpc.insecure_channel(target=self.provisioner_IP + ":50054", compression=grpc.Compression.Gzip, options=self.options) as channel:
                # create an interface for the grpc client (provisioner)
                provisioner_stub = provisioner_pb2_grpc.provisionerStub(channel)

                # send the num of workers to the provisioner to create the workers, so will call function create workers from provisioner stub.
                response = provisioner_stub.DefineNWorkers(
                    provisioner_pb2.NumOfWorkers(NumOfWorkers=num_of_workers)
                )
                self.logger.log('debug', f"sent {response.message} to the provisioner")
        except Exception as e:
            self.logger.log('error', f"Error sending the num of workers to the provisioner: {e}")
            return

    def get_IPs_from_provisioner(self) -> Tuple[List[str], List[Any], List[int], List[int]]:
        """
        Defines the interface for the Provisioner, establishes a connection with the Provisioner, 
        and gets the IPs of the workers and their status (Up or Down).

        Args:
            None

        Returns:
            A tuple containing a list of IPs, a list of statuses, a list of port numbers, and a list of IDs of the workers.
        """
        try:
            with grpc.insecure_channel(target=self.provisioner_IP +':50054', compression=grpc.Compression.Gzip, options=self.options) as channel:
                # create an interface for the grpc client (provisioner)
                provisioner_stub = provisioner_pb2_grpc.provisionerStub(channel) 
                # call function send Status from provisioner stub 
                response = provisioner_stub.SendStatus(provisioner_pb2.emptyMessage())
                # response is a list of IPs and their status
                self.workers_IPs = response.IPs
                self.statuses = response.statuses
                self.ports = response.ports
                self.ids = response.ids
                self.data_status = [0] * len(self.workers_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers
                return response.IPs, response.statuses, response.ports, response.ids
        except Exception as e:
            self.logger.log('error', f"Error getting IPs from provisioner: {e}")
            return [], [], [], []

    def GetWorkersInfo(self, request: coord_pb2.WorkersInfoRequest, context: grpc.ServicerContext) -> coord_pb2.WorkersInfoResponse:
        """
        Defines the interface to return the information about the working (Up) workers.

        Args:
            request (WorkersInfoRequest): A `WorkersInfoRequest` message sent by the Divider.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `WorkersInfoResponse` message containing the IPs, port numbers, and IDs of the working workers.
        """
        self.logger.log('debug', f"coordinator is sending workers info to divider")
        # get IPs and statuses from provisioner
        self.get_IPs_from_provisioner()
        # send working IPs to the divider
        working_IPs = []
        working_ports = []
        working_ids = []
        for i in range(len(self.workers_IPs)):
            if self.statuses[i] == 1:
                working_IPs.append(self.workers_IPs[i])
                working_ports.append(self.ports[i])
                working_ids.append(self.ids[i])
        return coord_pb2.WorkersInfoResponse(workers_ips=working_IPs, workers_ports=working_ports, workers_ids=working_ids)

    def GetNWorkers(self, request: coord_pb2.Request, context: grpc.ServicerContext) -> coord_pb2.NumOfWorkers:
        """
        Defines the interface to return the number of workers.

        Args:
            request (NWorkersRequest): A `NWorkersRequest` message sent by the Divider.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `NWorkersResponse` message containing the number of workers.
        """
        self.logger.log('debug', f"coordinator is sending the number of workers to provisioner")
        return coord_pb2.NumOfWorkers(NumOfWorkers=self.num_of_workers)

    def WorkerNotRespond (self, request: coord_pb2.WorkerNotRespondRequest, context: grpc.ServicerContext) -> coord_pb2.WorkerNotRespondResponse:
        """
        Defines the interface to handle the case when a worker does not respond.

        Args:
            request (WorkerNotRespondRequest): A `WorkerNotRespondRequest` message sent by the Divider.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `WorkerNotRespondResponse` message containing the new worker ip and port to connect with.
        """
        self.logger.log('debug', f"coordinator is handling the case of a worker not responding")
        # connect to the provisioner to solve the problem
        with grpc.insecure_channel(self.provisioner_IP +':50054') as channel:
            # create an interface for the grpc client (provisioner)
            provisioner_stub = provisioner_pb2_grpc.provisionerStub(channel) 
            # call function send Status from provisioner stub 
            response = provisioner_stub.SolveFailureWorker(provisioner_pb2.FailureWorker(worker_ip=request.worker_ip, worker_port=request.worker_port, worker_id=request.worker_id))
            # response is a list of IPs and their status
            self.workers_IPs[request.worker_id] = response.new_worker_ip
            self.statuses[request.worker_id]  = response.new_worker_port
            self.ports[request.worker_id]  = response.new_worker_status
        # send the ID of the worker that did not respond to the divider
        return coord_pb2.WorkerNotRespondResponse(worker_ip=response.new_worker_ip, worker_port=response.new_worker_port)

    def serve(self) -> None:
        """
        Starts the gRPC server for the coordinator.

        Returns:
            None
        """
        try:
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=2), compression=grpc.Compression.Gzip, options=self.options)

            coord_pb2_grpc.add_coordinatorServicer_to_server(self, self.server)

            self.server.add_insecure_port('[::]:50052') # open port for communication with the coordinator

            self.server.start()
            self.logger.log('info', f"coordinator is serving")
            # TODO: Critical, should be solved!!!
            self.set_num_of_workers(self.num_of_workers)
            
        except Exception as e:
            self.logger.log('error', f"Error in the coordinator server: {e}")
            return coord_pb2.LoopResponse(message = 'Error in the coordinator server')

    def stop_serving(self) -> None:
        """
        Stops the gRPC server for the coordinator.

        Returns:
            None
        """
        try:
            if self.server:
                self.server.stop(0)
                self.logger.log('info', f"coordinator stopped serving")
        except Exception as e:
            self.logger.log('error', "Error stopping serving: " + str(e))
            return




    