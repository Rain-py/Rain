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
    worker_pb2,
    worker_pb2_grpc,
    provisioner_pb2,
    provisioner_pb2_grpc,
    divider_pb2_grpc,
)

def read_file(filepath: str, logger: LogService, chunk_size: int = 1024) -> Iterator[coord_pb2.File]:
    
    """
    A generator function that reads a file in chunks and send it as stream of small chunks by yields the data as protobuf messages.

    Args:
        filepath (str): The path to the file to be read.
        chunk_size (int): The size of each chunk to be read, in bytes.

    Yields:
        An instance of `coord_pb2.File` containing either the metadata of the file or a chunk of file data.
    """
    # split filepath on '/' to get the filename and extension
    split_data = filepath.split("/")
    filename, extension = split_data[-1].split(".")[0], "." + split_data[-1].split(".")[1]
    try:
        metadata = coord_pb2.MetaData(filename=filename, extension=extension)
        yield coord_pb2.File(metadata=metadata)
        with open(filepath, mode="rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if chunk:
                    entry_request = coord_pb2.File(chunk_data=chunk)
                    yield entry_request
                else:  # The chunk was empty, which means we're at the end of the file
                    return
    except Exception as e:
        logger = logger
        logger.log("error", f"Error reading the file: {e}")
        return coord_pb2.File(chunk_data=b'')

## Coordinator class
class Coordinator(coord_pb2_grpc.coordinatorServicer):
    def __init__(self, divider_IP: str, provisioner_IP: str) -> None:
        """
        Initializes the Coordinator object.

        Args:
            divider_IP (str): The IP address of the Divider.
            provisioner_IP (str): The IP address of the Provisioner.

        Returns:
            None
        """
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('coord/')
        self.server  = None
        self.logger = LogService("Coordinator")
        self.logger.log('debug', f"Coordinator is initialized")
        self.divider_IP = divider_IP  
        self.provisioner_IP = provisioner_IP
        
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
            with grpc.insecure_channel(self.provisioner_IP + ":50054") as channel:
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
            with grpc.insecure_channel(self.provisioner_IP +':50054') as channel:
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

    def get_workers_info(self, request: coord_pb2.WorkersInfoRequest, context: grpc.ServicerContext) -> coord_pb2.WorkersInfoResponse:
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

    def upload(self, request: coord_pb2.MetaData, context: grpc.ServicerContext) -> coord_pb2.UploadFileResponse:
        """
        Divide the file into chunks and send them as a stream.

        Args:
            request (UploadFileRequest): A `UploadFileRequest` message containing the filename and extension of the file.
            context (grpc.ServicerContext): The context of the gRPC service.

        Yields:
            A `UploadFileResponse` message containing a chunk of the file data.
        """
        chunk_size = 1024
        filepath = self.date_base_path + request.filename + request.extension
        try:
            with open(filepath, mode="rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if chunk:
                        entry_response = worker_pb2.UploadFileResponse(chunk_data=chunk)
                        yield entry_response
                    else:  # The chunk was empty, which means we're at the end of the file
                        return
        except Exception as e:
            self.logger.log('error', f"Error uploading the file: {e}")
            return worker_pb2.UploadFileResponse(chunk_data=b'') # No file to upload, upload an empty chunk

    def download(self, request_iterator: coord_pb2.File, context: grpc.ServicerContext) -> coord_pb2.DownloadFileResponse:
        """
        Receives the data from workers as small chunks and appends them to a bytearray then writes the bytearray to a file.


        Args:
            request_iterator (Iterator[DownloadFileRequest]): An iterator of `DownloadFileRequest` messages containing file data.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `DownloadFileResponse` message containing a success or error message.
        """
        data = bytearray()
        try:
            # receive file name and its data
            for request in request_iterator:
                if request.metadata.filename and request.metadata.extension:
                    filepath = request.metadata.filename + request.metadata.extension
                else:
                    # the request is a file data, collect it
                    data.extend(request.chunk_data)
            # save file data
            with open(self.data_base_path + filepath, 'wb') as f:
                f.write(data)
            # return success message
            return worker_pb2.DownloadFileResponse(message='File received successfully')
        except Exception as e:
            self.logger.log('error', f"Error downloading the file: {e}")
            # return error message
            return worker_pb2.DownloadFileResponse(message='Error downloading the file')

    def execute(self, worker_id: int, ip: str, port: int, iteration_num: int = 0) -> worker_pb2.ExecuteData:
        """
        Executes a Python command on a worker.

        Args:
            worker_id (int): The ID of the worker.
            ip (str): The IP address of the worker.
            port (int): The port number of the worker.
            iteration_num (int): The iteration number (default 0).

        Returns:
            An `ExecuteData` message containing a success or error message.
        """
        try:
            with grpc.insecure_channel(f'{ip}:{port}') as channel:
                worker_stub = worker_pb2_grpc.workerStub(channel)   # interface for the grpc client(worker)

                filename, extension = 'Algo', '.py'  
                response =  worker_stub.Execute(worker_pb2.ExecuteData(filename=filename,extension=extension,worker_id=str(worker_id), iteration_num=str(iteration_num)))
                self.logger.log('debug', f"coordinator received: {response.message} from worker")
        except Exception as e:
            self.logger.log('error', f"Error executing the file: {e}")
            return worker_pb2.ExecuteData(message='Error executing the file')

    def send(self, target: str, worker_id: int, ip: str, port: int, iteration_num: int = 0) -> None:
        """
        Defines the interface for the workers and establishes a connection with the workers and sends them their tasks. 
        Defines the interface for the divider and establishes a connection with the divider and sends it the weights collected from the workers.

        Args:
            target (str): The target of the send operation (worker or divider).
            worker_id (int): The ID of the worker.
            ip (str): The IP address of the target (provisioner IP or worker IP).
            port (int): The port number of the worker.
            iteration_num (int): The iteration number (default 0).

        Returns:
            A `DownloadFileResponse` message containing a success or error message.
        """
        if target == "worker":
            # Establish a connection with the worker on port 50051
            with grpc.insecure_channel(f'{ip}:{port}') as channel:
                # create an interface for the grpc client (worker)
                worker_stub = worker_pb2_grpc.workerStub(channel) 
                # send files
                if not self.data_status[worker_id - 1]:
                    response = worker_stub.download(read_file(f'{self.data_base_path}X_train_{worker_id}.npy', self.logger))
                    self.logger.log('debug', f"coordinator received: {response.message} from worker")
                    response = worker_stub.download(read_file(f'{self.data_base_path}y_train_{worker_id}.npy', self.logger))
                    self.logger.log('debug', f"coordinator received: {response.message} from worker")
                    self.data_status[worker_id - 1] = 1

                response = worker_stub.download(read_file(f'{self.data_base_path}{iteration_num}.pkl', self.logger))
                self.logger.log('debug', f"coordinator received: {response.message} from worker")
        elif target == 'divider':
            # Establish a connection with the divider on port 50052
            with grpc.insecure_channel(ip + ":50053") as channel:
                # create an interface for the grpc client (divider)
                divider_stub = divider_pb2_grpc.dividerStub(channel)  
                response = divider_stub.download(read_file(f'{self.data_base_path}{worker_id}_{iteration_num}_trained.pkl', self.logger))
                self.logger.log('debug', f"coordinator received: {response.message} from divider")

    def receive(self, worker_id: int, ip: str, port: int, iteration_num: int) -> worker_pb2.UploadFileResponse:
        """
        Receives a trained model from a worker as a small chunks and appends them to a bytearray then writes the bytearray to a file.

        Args:
            worker_id (int): The ID of the worker.
            ip (str): The IP address of the worker.
            port (int): The port number of the worker.
            iteration_num (int): The iteration number.

        Returns:
            An `UploadFileResponse` message containing a success or error message.
        """
        try:
            
            with grpc.insecure_channel(f'{ip}:{port}') as channel:
                worker_stub = worker_pb2_grpc.workerStub(channel)   # interface for the grpc client(worker)

                filename, extension = f'{worker_id}_{iteration_num}_trained', '.pkl'
                filepath = self.data_base_path + filename + extension
                data = bytearray()
                for request in worker_stub.upload(
                    worker_pb2.MetaData(filename=filename, extension=extension)
                ):
                    data.extend(request.chunk_data)

                with open(filepath, mode="wb") as f:
                    f.write(data)
                self.logger.log('debug', f"Downloaded {filepath} in coordinator")
        except Exception as e:
            self.logger.log('error', f"Error receiving the file: {e}")
            return worker_pb2.UploadFileResponse(chunk_data=b'')


    def serve(self) -> None:
        """
        Starts the gRPC server for the coordinator.

        Returns:
            None
        """
        try:
            self.server = grpc.server(futures.ThreadPoolExecutor(1))

            coord_pb2_grpc.add_coordinatorServicer_to_server(self, self.server)

            self.server.add_insecure_port('[::]:50052') # open port for communication with the coordinator

            self.server.start()
            self.logger.log('info', f"coordinator is serving")
            self.set_num_of_workers(3)
            
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




    