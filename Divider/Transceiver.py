from __future__ import print_function
from concurrent import futures  # indicates the num of (threads)
import logging
import os
import grpc
from protos import (
    divider_pb2,
    divider_pb2_grpc,
    coord_pb2,
    coord_pb2_grpc,
    provisioner_pb2,
    provisioner_pb2_grpc,
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

class Transceiver(divider_pb2_grpc.dividerServicer):
    def __init__(self):
        self.base_path = "../../../Divider/divider/"
        self.data_base_path = self.base_path +'data/'
        self.server = None
    def __del__(self):
        self.stop_serving()
    
    def send_data(self, coordinator_IP, Provisioner_IP, Num_of_workers, path):
        """
        This function will send the data to the coordinator and the provisioner.
        send the num of workers to the provisioner to create the workers.
        send the data to coordinator to distribute it among workers.
        """ 
        # try:
        #     # instantiate a channel to the provisioner
        #     with grpc.insecure_channel(Provisioner_IP + ":50054") as channel:
        #         # create an interface for the grpc client (provisioner)
        #         provisioner_stub = provisioner_pb2_grpc.provisionerStub(channel)

        #         # send the num of workers to the provisioner to create the workers, so will call function create workers from provisioner stub.
        #         response = provisioner_stub.DefineNWorkers(
        #             provisioner_pb2.NumOfWorkers(NumOfWorkers=Num_of_workers)
        #         )
        #         print("divider received: " + response.message + " from provisioner")
        # except Exception as e:
        #     print("Error sending the num of workers to the provisioner: ", e)
        #     return

        try:
            # instantiate a channel to the coord
            with grpc.insecure_channel(coordinator_IP + ":50052") as channel:
                print("divider is sending data to the coordinator")
                # create an interface for the grpc client (coord)
                coord_stub = coord_pb2_grpc.coordinatorStub(channel)

                for i in range(Num_of_workers):
                    response = coord_stub.download(
                        read_file(path + f"X_train_{i+1}.npy")
                    )
                    print(" divider received: " + response.message + " from coordinator")
                    response = coord_stub.download(
                        read_file(path + f"y_train_{i+1}.npy")
                    )
                    print(" divider received: " + response.message + " from coordinator")
        except Exception as e:
            print("Error sending the data to the coordinator: ", e)
            return

    def send_file(self, coordinator_IP, file_path):
        with grpc.insecure_channel(coordinator_IP + ":50052") as channel:
            print("divider is sending information file to the coordinator")
            # create an interface for the grpc client (coord)
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            # divider will send (upload) the data to the coordinator, so it will call function recieve_from_divider from coord_stub

            response = coord_stub.download(read_file(file_path))
            print("divider received: " + response.message  + " from coordinator")

    def iteration(self, coordinator_IP, iteration_num):
        with grpc.insecure_channel(coordinator_IP + ":50052") as channel:
            print("divider begins the iteration")
            # create an interface for the grpc client (coord)
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)
            response = coord_stub.start_loop(
                coord_pb2.StartLoopMessage(message="start the loop", iteration_num=iteration_num)
            )
            print("divider received: " + response.message + " from coordinator")
            return response.message

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
        # print current path
        with open(self.data_base_path + filepath, "wb") as f:
            f.write(data)
        return divider_pb2.DownloadFileResponse(message="Success!")

    def serve(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(1))
        divider_pb2_grpc.add_dividerServicer_to_server(self, self.server)
        self.server.add_insecure_port(
            "[::]:50053"
        )  # for other nodes to connect with divider
        self.server.start()
        print("Transceiver is serving")

    def stop_serving(self):
        if self.server:
            self.server.stop(0)
            print("Transceiver stopped")

