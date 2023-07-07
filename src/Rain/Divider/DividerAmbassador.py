from __future__ import print_function
from concurrent import futures  # indicates the num of (threads)
import grpc
import numpy as np
from typing import List, Tuple, Any, Iterator
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService
from Rain.Protos import (
    divider_pb2,
    divider_pb2_grpc,
    coord_pb2,
    coord_pb2_grpc,
    worker_pb2_grpc,
    worker_pb2
)

def read_file(filepath: str, chunk_size: int = 1024) -> Iterator[divider_pb2.File]:
    """
    A generator function that reads a file in chunks and yields the data as protobuf messages.

    Args:
        filepath (str): The path to the file to be read.
        chunk_size (int): The size of each chunk to be read, in bytes.

    Yields:
        An instance of `divider_pb2.File` containing either the metadata of the file or a chunk of file data.
    """
    split_data = filepath.split("/")
    filename, extension = split_data[-1].split(".")[0], "." + split_data[-1].split(".")[1]
    metadata = divider_pb2.MetaData(
        filename= filename, extension=extension
    )
    yield divider_pb2.File(metadata=metadata)

    with open(filepath, mode="rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                entry_request = divider_pb2.File(chunk_data=chunk)
                yield entry_request
            else:  # The chunk was empty, which means we're at the end of the file
                return

def read_data(filepath: str, data_partition, filename: str, extension: str, chunk_size: int = 1024) -> Iterator[divider_pb2.File]:
    """
    A generator function that reads a file in chunks and yields the data as protobuf messages.

    Args:
        filepath (str): The path to the file to be read.
        chunk_size (int): The size of each chunk to be read, in bytes.

    Yields:
        An instance of `divider_pb2.File` containing either the metadata of the file or a chunk of file data.
    """
    metadata = divider_pb2.MetaData(
        filename=filename,
        extension=extension
    )
    yield divider_pb2.File(metadata=metadata)

    np.save(filepath, data_partition)
    with open(filepath, mode="rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                entry_request = divider_pb2.File(chunk_data=chunk)
                yield entry_request
            else:  # The chunk was empty, which means we're at the end of the file
                return
    max_message_size = 1*1024*1024  # Update the maximum allowed message size
    data_size = data_partition[0].nbytes * len(data_partition)
    chunk_size = min(chunk_size, max_message_size)  # Set the chunk size to be within the maximum allowed size
    offset = 0
    while offset < data_size:
        remaining_bytes = data_size - offset
        chunk = data_partition[offset: offset + min(chunk_size, remaining_bytes)]
        offset += min(chunk_size, remaining_bytes)
        entry_request = divider_pb2.File(chunk_data=chunk.tobytes())
        yield entry_request
    return

def read_partitioned_data(data: List[Any], filename: str, extension: str, chunk_size: int = 1024) -> Iterator[divider_pb2.File]:
    """
    A generator function that reads partitioned data in chunks and yields the data as protobuf messages.

    Args:
        data (List[Any]): The partitioned data to be read.
        filename (str): The name of the file containing the partitioned data.
        extension (str): The file extension of the file containing the partitioned data.
        chunk_size (int): The size of each chunk to be read, in bytes.

    Yields:
        An instance of `divider_pb2.File` containing either the metadata of the file or a chunk of file data.
    """
    metadata = divider_pb2.MetaData(
        filename=filename,
        extension=extension
    )
    # We need to yield the data in chunks
    yield divider_pb2.File(metadata=metadata)
    # convert data to byte array
    dataBytes = bytearray(data)
    # split the data into chunks
    data = [dataBytes[i:i+chunk_size] for i in range(0, len(dataBytes), chunk_size)]
    for i in range(len(data)):
        yield divider_pb2.File(chunk_data=data[i])
    return



class DividerAmbassador(divider_pb2_grpc.dividerServicer):
    def __init__(self, chunk_size: int = 1024):
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider/')
        self.server = None
        self.logger = LogService("DividerAmbassador")
        self.coordinator_IP = '127.0.0.1'
        self.chunk_size = chunk_size
        self.options = [('grpc.max_send_message_length', 10 * 1024 * 1024),
               ('grpc.max_receive_message_length', 10 * 1024 * 1024)]
        
    def __del__(self):
        try:
            self.stop_serving()
        except Exception as e:
            self.logger.log('error', f"Error deleting: {e}")
            return

    def send_data(self, worker_id: int, X_train_partition: List[Any], y_train_partition: List[Any], worker_stub: worker_pb2_grpc.workerStub) -> None:
        """
        Sends the data to the workers and coordinates the distribution of the data.

        Args:
            worker_id (int): The ID of the worker being sent data.
            X_train_partition (List[Any]): The partitioned training data to be sent to the worker.
            y_train_partition (List[Any]): The partitioned training labels to be sent to the worker.
            worker_stub (worker_pb2_grpc.workerStub): The gRPC stub of the worker being sent data.

        Returns:
            None
        """
        # TODO: Remove writing and reading the file
        try:
            # X train data
            response = worker_stub.download(
                read_data(f"{self.data_base_path}X_train_{worker_id}.npy", X_train_partition, f"X_train_{worker_id}", ".npy", chunk_size=self.chunk_size)
                )
            self.logger.log('debug', "divider receive: " + response.message + " from  worker after sending X_train")
            # y train data
            response = worker_stub.download(
                read_data(f"{self.data_base_path}y_train_{worker_id}.npy", y_train_partition, f"y_train_{worker_id}", ".npy", chunk_size=self.chunk_size)
            )
            self.logger.log('debug', f"divider receive: {response.message} from worker {worker_id} after sending y_train")
        except Exception as e:
            self.logger.log('debug', "Error sending the data to the worker: " + str(e))
            return

    def inform_coord(self, worker_ip : str, worker_port : int, worker_id: int) -> Tuple[str, int]:
        """
        Informs the coordinator that the worker has received the data.

        Args:
            worker_id (int): The ID of the worker being informed.

        Returns:
            Tuple[str, int] containing the IP address and port number of the coordinator.
        """
        with grpc.insecure_channel(self.coordinator_IP + ":50052") as channel:
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            try:
                response = coord_stub.WorkerNotRespond(coord_pb2.WorkerNotRespondRequest(worker_ip=worker_ip, worker_port=worker_port, worker_id=worker_id))
                self.logger.log('debug', "divider receive: " +response.worker_ip+ " from coordinator after informing coordinator")
                return response.worker_ip, response.worker_port
            except Exception as e:
                self.logger.log('error', "Error informing the coordinator: " + str(e))
                return "", 0

    def iteration(self, worker_id: int, worker_ip: str, worker_port: str, data_status: int, iteration_num: int, model_name: str, X_train_partition: List[Any], y_train_partition: List[Any]) -> None:
        """
        Executes one iteration of federated learning on a single worker.

        Args:
            worker_id (int): The ID of the worker being executed.
            worker_ip (str): The IP address of the worker being executed.
            worker_port (str): The port number of the worker being executed.
            data_status (int): A flag indicating whether the worker has already received the training data.
            iteration_num (int): The current iteration number.
            model_name (str): The name of the model being used for federated learning.
            X_train_partition (List[Any]): The partitioned training data being sent to the worker.
            y_train_partition (List[Any]): The partitioned training labels being sent to the worker.

        Returns:
            None
        """
        self.logger.log('debug', f'{worker_ip}:{worker_port}')
        with grpc.insecure_channel(target=f'{worker_ip}:{worker_port}', compression=grpc.Compression.Gzip, options=self.options) as channel:
            worker_stub = worker_pb2_grpc.workerStub(channel)
            try:
                # send data to the worker
                if not data_status:
                    self.send_data(worker_id, X_train_partition, y_train_partition, worker_stub)
                else:
                    self.logger.log('debug', f"divider begins will not send data in iteration {iteration_num} to worker {worker_id}")
           
            except Exception as e:
                self.logger.log('error', "Error sending the data to the worker: " + str(e))
                raise Exception("Error sending the data to the worker")
            
            try:
                # send the model to the worker
                self.logger.log('debug', f"Sending {self.data_base_path}{worker_id}.pkl to worker{worker_id}")
                response = worker_stub.Download(read_file(f'{self.data_base_path}{model_name}.pkl', chunk_size=self.chunk_size))
                self.logger.log('debug', "divider received: " + response.message +  " after sending the model to worker " + str(worker_id))
            except Exception as e:
                self.logger.log('error', "Error sending the model to the worker: " + str(e))
                raise Exception("Error sending the model to the worker")
  
            try:
                # execute the model
                self.logger.log('debug', f"divider begins executing iteration{iteration_num} for worker{worker_id}")
                filename, extension = 'Algo', '.py'
                response = worker_stub.Execute(worker_pb2.ExecuteData(filename=filename,extension=extension,worker_id=str(worker_id), iteration_num=str(model_name)))
                self.logger.log('debug', "divider received: " + response.message + f" after executing the model on worker{worker_id}")
            except Exception as e:
                self.logger.log('error', "Error executing the model on the worker: " + str(e))
                raise Exception("Error executing the model on the worker")


            try:
                    # receive the model from the worker
                    filename, extension = f'{worker_id}_{model_name}_trained', '.pkl'
                    filepath = self.data_base_path + filename + extension
                    self.logger.log('debug', f"divider begins downloading {filepath} from worker{worker_id}")
                    data = bytearray()
                    for request in worker_stub.Upload(
                        worker_pb2.MetaData(filename=filename, extension=extension)
                    ):
                        data.extend(request.chunk_data)

                    with open(filepath, mode="wb") as f:
                        f.write(data)
                    self.logger.log('debug', f"Downloaded {filepath} from worker{worker_id} successfully")
            except Exception as e:
                self.logger.log('error', "Error downloading the model: " + str(e))
                raise Exception("Error downloading the model from the worker")


    def Download(self, request_iterator: divider_pb2.File, context: grpc.ServicerContext) -> divider_pb2.DownloadFileResponse:
        """
        Receives data from the coordinator and saves it to disk.

        Args:
            request_iterator (Iterator[divider_pb2.DownloadFileRequest]): An iterator over `DownloadFileRequest` messages.
            context (grpc.ServicerContext): The context of the gRPC service.

        Returns:
            A `DownloadFileResponse` message indicating the success or failure of the data transfer.
        """
        data = bytearray()
        for request in request_iterator:
            if request.metadata.filename and request.metadata.extension:
                filepath = request.metadata.filename + request.metadata.extension
            else:
                data.extend(request.chunk_data)
        with open(self.data_base_path + filepath, "wb") as f:
            f.write(data)
        return divider_pb2.DownloadFileResponse(message="Success!")

    def GetWorkersInfo(self, coordinator_IP: str) -> Tuple[str, int, int]:
        """
        Retrieves information about the workers from the coordinator.

        Args:
            coordinator_IP (str): The IP address of the coordinator.

        Returns:
            A tuple containing the IP addresses, port numbers, and IDs of the workers.
        """
        with grpc.insecure_channel(target=coordinator_IP + ":50052", compression=grpc.Compression.Gzip, options=self.options) as channel:
            # create an interface for the grpc client (coord)
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            response = coord_stub.GetWorkersInfo(
                coord_pb2.WorkersInfoRequest(message="get workers info")
            )
            self.logger.log('debug', "divider received: information from coordinator")
            return response.workers_ips, response.workers_ports, response.workers_ids

    def serve(self) -> None:
        """
        Starts the gRPC server for the divider.

        Returns:
            None
        """
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=2), compression=grpc.Compression.Gzip, options=self.options)
        divider_pb2_grpc.add_dividerServicer_to_server(self, self.server)
        self.server.add_insecure_port(
            "[::]:50053"
        )  # for other nodes to connect with divider
        self.server.start()
        self.logger.log('debug', "divider ambassador is serving")

    def get_worker_IPs(self, coordinator_IP: str, num_of_workers: int) -> List[str]:
        """
        Retrieves the IP addresses of the workers from the coordinator.

        Args:
            coordinator_IP (str): The IP address of the coordinator.
            num_of_workers (int): The number of workers participating in the federated learning process.

        Returns:
            A list of IP addresses of the workers.
        """
        with grpc.insecure_channel(target=coordinator_IP + ":50052", compression=grpc.Compression.Gzip, options=self.options) as channel:
            # create an interface for the grpc client (coord)
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            response = coord_stub.get_worker_IPs(
                coord_pb2.NumOfWorkers(num_of_workers=num_of_workers)
        )
            self.logger.log('debug', "divider received: " + response.message + " from coordinator")
            return response.worker_IPs

    def stop_serving(self) -> None:
        """
        Stops the gRPC server for the divider.

        Returns:
            None
        """
        try:
            if self.server:
                self.server.stop(0)
                self.logger.log('debug', "divider ambassador stopped serving")
        except Exception as e:
            self.logger.log('error', "Error stopping serving: " + str(e))
            return

