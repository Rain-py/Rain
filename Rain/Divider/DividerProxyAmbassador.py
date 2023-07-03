from __future__ import print_function
from concurrent import futures  # indicates the num of (threads)
import grpc
import numpy as np
import dill
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService
from Rain.Protos import (
    divider_pb2,
    divider_pb2_grpc,
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
    


class DividerProxyAmbassador(divider_pb2_grpc.dividerServicer):
    def __init__(self):
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider_proxy/')
        self.server = None
        self.logger = LogService("DividerProxyAmbassador")
        self.divider_IP = '127.0.0.1'

    def __del__(self):
        self.stop_serving()
    
    
    def send_data(self,X_train, y_train, model, config):
        """
        This function will send the data to the divider.
        """ 
        # TODO: Remove writing and reading the file
        try:
            # instantiate a channel to the coord
            with grpc.insecure_channel(self.divider_IP + ":50053") as channel:
                self.logger.log('debug', "divider proxy is sending data to the divider")
                # create an interface for the grpc client (coord)
                divider_stub = divider_pb2_grpc.dividerStub(channel)

                self.logger.log('debug', "divider proxy is sending data to the divider")
                np.save(f"{self.data_base_path}X_train.npy", X_train)
                response = divider_stub.download(
                    read_file(self.data_base_path + f"X_train.npy")
                )

                self.logger.log('debug', "divider proxy is sending data to the divider")
                np.save(f"{self.data_base_path}y_train.npy", y_train)
                response = divider_stub.download(
                    read_file(self.data_base_path + f"y_train.npy")
                )

                self.logger.log('debug', "divider proxy is sending model to the divider")
                dill.dump(model, open(f"{self.data_base_path}initial_model.pkl", "wb"))
                response = divider_stub.download(
                    read_file(self.data_base_path + f"initial_model.pkl")
                )
                
                self.logger.log('debug', "divider proxy is sending config to the divider")
                dill.dump(config, open(f"{self.data_base_path}config.pkl", "wb"))
                response = divider_stub.download(
                    read_file(self.data_base_path + f"config.pkl")
                )
                self.logger.log('debug', "divider proxy received: " + response.message + " from divider")
        except Exception as e:
            self.logger.log('debug', "Error sending the data to the divider: " + str(e))
            return

    def download(self, request_iterator, context):
        """
        This function will receive the data from and the coordinator or workers.
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

    def serve(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(1))
        divider_pb2_grpc.add_dividerServicer_to_server(self, self.server)
        self.server.add_insecure_port(
            "[::]:50050"
        )  # for other nodes to connect with divider proxy
        self.server.start()
        self.logger.log('debug', "divider proxy ambassador is serving")

    def stop_serving(self):
        if self.server:
            self.server.stop(0)
            self.logger.log('debug', "divider proxy ambassador stopped serving")

