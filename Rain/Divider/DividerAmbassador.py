from __future__ import print_function
from concurrent import futures  # indicates the num of (threads)
import grpc
import numpy as np
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

def read_file(filepath, chunk_size=1024):
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
def read_partitioned_data(data, filename, extension, chunk_size = 1024):
    # The data is a list of numpy arrays
    metadata = divider_pb2.MetaData(
        filename= filename, extension=extension
    )
    yield divider_pb2.File(metadata=metadata)
    # We need to yield the data in chunks
    # convert data to byte array
    dataBytes = data.tobytes()
    # split the data into chunks
    data = [dataBytes[i:i+chunk_size] for i in range(0, len(dataBytes), chunk_size)]
    for i in range(len(data)):
        yield divider_pb2.File(chunk_data=data[i])
    return
    


class DividerAmbassador(divider_pb2_grpc.dividerServicer):
    def __init__(self):
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider/data/')
        self.server = None
        self.logger = LogService("DividerAmbassador")
    def __del__(self):
        self.stop_serving()
    
    def send_data(self, coordinator_IP, num_workers, X_train_partitions, y_train_partitions):
        """
        This function will send the data to the coordinator and the provisioner.
        send the num of workers to the provisioner to create the workers.
        send the data to coordinator to distribute it among workers.
        """ 
        # TODO: Remove writing and reading the file
        try:
            # instantiate a channel to the coord
            with grpc.insecure_channel(coordinator_IP + ":50052") as channel:
                self.logger.log('debug', "divider is sending data to the coordinator")
                # create an interface for the grpc client (coord)
                coord_stub = coord_pb2_grpc.coordinatorStub(channel)

                for i in range(num_workers):
                    np.save(f"{self.data_base_path}X_train_{i + 1}.npy", X_train_partitions[i])
                    response = coord_stub.download(
                        read_file(self.data_base_path + f"X_train_{i+1}.npy")
                        # read_partitioned_data(X_train_partitions[i], f"X_train_{i+1}", ".npy")
                    )
                    self.logger.log('debug', "divider is sending data to the provisioner")
                    np.save(f"{self.data_base_path}y_train_{i + 1}.npy", y_train_partitions[i])
                    response = coord_stub.download(
                        read_file(self.data_base_path + f"y_train_{i+1}.npy")
                        # read_partitioned_data(y_train_partitions[i], f"X_train_{i+1}", ".npy")
                    )
                    self.logger.log('debug', "divider received: " + response.message + " from coordinator")
        except Exception as e:
            self.logger.log('debug', "Error sending the data to the coordinator: " + str(e))
            return

    def send_file(self, coordinator_IP, file_path):
        with grpc.insecure_channel(coordinator_IP + ":50052") as channel:
            self.logger.log('debug', "divider is sending information file to the coordinator")
            # create an interface for the grpc client (coord)
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            # divider will send (upload) the data to the coordinator, so it will call function recieve_from_divider from coord_stub

            response = coord_stub.download(read_file(file_path))
            self.logger.log('debug', "divider received: " + response.message  + " from coordinator")

   
    def iteration(self, worker_id , worker_ip, worker_port, data_status, iteration_num, model_name):
        self.logger.log('debug', f'{worker_ip}:{worker_port}')
        with grpc.insecure_channel(f'{worker_ip}:{worker_port}') as channel:
            worker_stub = worker_pb2_grpc.workerStub(channel) 
            try:
                # send data to the worker
                if not data_status:
                    path = self.data_base_path
                    response = worker_stub.download(read_file(f'{path}X_train_{worker_id}.npy'))
                    self.logger.log('debug', "divider received: " + response.message + " after sending the data to worker " + str(worker_id))

                    response = worker_stub.download(read_file(f'{path}y_train_{worker_id}.npy'))
                    self.logger.log('debug', "divider received: " + response.message + " after sending the data to worker " + str(worker_id))
            except Exception as e:
                self.logger.log('error', "Error sending the data to the worker: " + str(e))
                return
            try:
                # send the model to the worker
                self.logger.log('debug', f"Sending {self.data_base_path}{worker_id}.pkl to worker{worker_id}")
                response = worker_stub.download(read_file(f'{self.data_base_path}{model_name}.pkl'))
                self.logger.log('debug',"divider received: " + response.message +  " after sending the model to worker " + str(worker_id))
            except Exception as e:
                self.logger.log('error', "Error sending the model to the worker: " + str(e))
                return
            try:
                # execute the model
                self.logger.log('debug', f"divider begins executing iteration{iteration_num} for worker{worker_id}")
                filename, extension = 'Algo', '.py' 
                response =  worker_stub.Execute(worker_pb2.executeData(filename=filename,extension=extension,worker_id=str(worker_id), iteration_num=str(model_name)))
                self.logger.log('debug',"divider received: " + response.message + " after executing the model on worker " + str(worker_id))
            except Exception as e:
                self.logger.log('error', "Error executing the model: " + str(e))
                return
            try:
                # receive the model from the worker
                filename, extension = f'{worker_id}_{model_name}_trained', '.pkl'
                filepath = self.data_base_path + filename + extension
                self.logger.log('debug', f"divider begins downloading {filepath} from worker{worker_id}")
                data = bytearray()
                for request in worker_stub.upload(
                    worker_pb2.MetaData(filename=filename, extension=extension)
                ):
                    data.extend(request.chunk_data)

                with open(filepath, mode="wb") as f:
                    f.write(data)
                self.logger.log('debug', f"Downloaded {filepath} from worker{worker_id} successfully")
            except Exception as e:
                self.logger.log('error', "Error downloading the model: " + str(e))
                return
    

    def download(self, request_iterator, context):
        """
        This function will receive the data from and the coordinator.
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

    def get_workers_info(self, coordinator_IP):
        with grpc.insecure_channel(coordinator_IP + ":50052") as channel:
            # create an interface for the grpc client (coord)
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            response = coord_stub.get_workers_info(
                coord_pb2.WorkersInfoRequest(message="get workers info")
            )
            self.logger.log('debug', "divider received: information from coordinator")
            return response.workers_ips, response.workers_ports, response.workers_ids
    def serve(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(1))
        divider_pb2_grpc.add_dividerServicer_to_server(self, self.server)
        self.server.add_insecure_port(
            "[::]:50053"
        )  # for other nodes to connect with divider
        self.server.start()
        self.logger.log('debug', "divider ambassador is serving")

    def get_worker_IPs(self, coordinator_IP, num_of_workers):
        with grpc.insecure_channel(coordinator_IP + ":50052") as channel:
            # create an interface for the grpc client (coord)
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            response = coord_stub.get_worker_IPs(
                coord_pb2.NumOfWorkers(num_of_workers=num_of_workers)
            )
            self.logger.log('debug', "divider received: " + response.message + " from coordinator")
            return response.worker_IPs
        
    def stop_serving(self):
        if self.server:
            self.server.stop(0)
            self.logger.log('debug', "divider ambassador stopped serving")

