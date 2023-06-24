from __future__ import print_function
from concurrent import futures # indicates the num of (threads)
import logging
import os
import grpc
from protos import divider_pb2, divider_pb2_grpc, coord_pb2 , coord_pb2_grpc, provisioner_pb2, provisioner_pb2_grpc
import time
import sys


def get_filepath(filename, extension):
    return f'{filename}{extension}'


def read_iterfile(filepath, chunk_size=1024):
    split_data = os.path.splitext(filepath)
    filename = split_data[0]
    extension = split_data[1]
    send_filename = filename.split('/')[-1]
    metadata = divider_pb2.MetaData(filename="./data/" + send_filename, extension=extension)
    yield divider_pb2.File(metadata=metadata)
    filepath = get_filepath(filename, extension)
    #print current path
    print(filepath)
    with open(filepath, mode="rb") as f:
        print("filepath is opened")
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                entry_request = divider_pb2.File(chunk_data=chunk)
                yield entry_request
            else:  # The chunk was empty, which means we're at the end of the file
                return

class div_transmitter(divider_pb2_grpc.dividerServicer):

    def send_data(self, coordinator_IP, Provisioner_IP, Num_of_workers, path):
        """
        This function will send the data to the coordinator and the provisioner.
        send the num of workers to the provisioner to create the workers.
        send the data to coordinator to distribute it among workers.
        """
        # instantiate a channel to the provisioner
        with grpc.insecure_channel(Provisioner_IP +':50054') as channel:

            # create an interface for the grpc client (provisionar)
            provisioner_stub = provisioner_pb2_grpc.provisionerStub(channel)

            # send the num of workers to the provisionar to create the workers, so will call function create workers from provisionar stub.
            response = provisioner_stub.DefineNWorkers(provisioner_pb2.NumOfWorkers(NumOfWorkers=Num_of_workers))
            print(" divider received: " + response.message)

        time.sleep(5)
        # instantiate a channel to the coord 
        with grpc.insecure_channel(coordinator_IP +':50052') as channel:
            
            print("divider is sending data to the coordinator")
            # create an interface for the grpc client (coord) 
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)   
            # divider will send (upload) the data to the coordinator, so it will call function recieve_from_divider from coord_stub
            
            # response = coord_stub.download(read_iterfile('install_locally.py'))
            # print(" divider received: " + response.message)
            
            response = coord_stub.download(read_iterfile("../../Divider/" + 'Algo.py'))
            print(" divider received: " + response.message)

            for i in range(Num_of_workers):
                response = coord_stub.download(read_iterfile(path + f'X_train_{i+1}.npy'))
                print(" divider received: " + response.message)
                response = coord_stub.download(read_iterfile(path + f'y_train_{i+1}.npy'))
                print(" divider received: " + response.message)
            response = coord_stub.start_loop(coord_pb2.StartLoopMessage(message='start the loop'))
            print(" divider received: " + response.message)
        # self.server.wait_for_termination()

    def iteration(self, coordinator_IP):
        
        with grpc.insecure_channel(coordinator_IP +':50052') as channel:
            
            print("divider is beginning the iteration")
            # create an interface for the grpc client (coord) 
            coord_stub = coord_pb2_grpc.coordinatorStub(channel)  
            response = coord_stub.start_loop(coord_pb2.StartLoopMessage(message='start the loop'))
            print(" divider received: " + response.message)
    
    def download(self, request_iterator, context):
        """
        This function will recieve the data from and the coordinator.
        """
        data = bytearray()
        for request in request_iterator:
            if request.metadata.filename and request.metadata.extension:
                filepath = get_filepath(request.metadata.filename, request.metadata.extension)
                continue
            data.extend(request.chunk_data)
        with open('divider/' + filepath, 'wb') as f:
            f.write(data)
        return divider_pb2.DownloadFileResponse(message='Success!')
    
    def create_server(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(1))
        divider_pb2_grpc.add_dividerServicer_to_server(self, self.server)
        self.server.add_insecure_port('[::]:50053') # for other nodes to connect with divider
        self.server.start()
        print("divider is running")
    
    def stop_server(self):
        self.server.stop(0)
        print("divider is stopped")

# def serve(divider, coordinator_IP, provisioner_IP, Num_of_workers):
#     server = grpc.server(futures.ThreadPoolExecutor(1))
#     divider_pb2_grpc.add_dividerServicer_to_server(divider, server)
#     server.add_insecure_port('[::]:50053') # for other nodes to connect with divider
#     server.start()
#     print("divider is running")
#     divider.send(coordinator_IP, provisioner_IP, Num_of_workers)
#     server.wait_for_termination()

# if __name__ == '__main__':
#     # Configures the root logger. This function does nothing if the root logger already has handlers configured for it. 
#     logging.basicConfig()

#     # define the coord ip
#     coordinator_IP = '127.0.0.1'

#     # define the provisioner ip
#     provisioner_IP = '127.0.0.1' 

#     # define the number of workers
#     Num_of_workers = 1

#     divider_ = div_transmitter()
#     serve(divider_, coordinator_IP, provisioner_IP, Num_of_workers)
