from __future__ import print_function
from concurrent import futures  # indicates the num of (threads)
import os
import grpc
import re
import sys

sys.path.append("../")
from protos import (
    coord_pb2,
    coord_pb2_grpc,
    worker_pb2,
    worker_pb2_grpc,
    provisioner_pb2,
    provisioner_pb2_grpc,
    divider_pb2,
    divider_pb2_grpc,
)

sys.path.pop()


## Coordinator class
class coordinator(coord_pb2_grpc.coordinatorServicer):
    def __init__(self, divider_IP):
        print("Coordinator initialized successfully") 
        self.divider_IP = divider_IP  
        self.base_path = 'coord/'
        self.data_base_path = self.base_path + 'data/'

    def get_IPs_from_provisioner(self, provisioner_IP):
        """
        function :
            Defines the interface for the provisioner and establishes a connection with the provisioner 
            and gets the IPs of the workers and their status (Up or Down).
        input : Provisioner IP
        output: list of IPs and their status
        """
        try:
            with grpc.insecure_channel(provisioner_IP +':50054') as channel:
                # create an interface for the grpc client (provisioner)
                provisioner_stub = provisioner_pb2_grpc.provisionerStub(channel) 
                # call function send Status from provisioner stub 
                response = provisioner_stub.SendStatus(provisioner_pb2.emptyMessage())
                # response is a list of IPs and their status
                self.workers_IPs = response.IPs
                self.statuses = response.statuses
                return response.IPs, response.statuses
        except Exception as e:
            print("Error getting IPs from provisioner: ", e)
            return [], []

    def upload(self, request, context):
        chunk_size = 1024

        filepath = self.base_path + request.filename + request.extension
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
            print("Error uploading the file: ", e)
            return worker_pb2.UploadFileResponse(chunk_data=b'') # No file to upload, upload an empty chunk

    def download(self, request_iterator, context):
        """
        function to receive data files from the coordinator.
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
            with open(self.base_path + filepath, 'wb') as f:
                f.write(data)
            # return success message
            return worker_pb2.DownloadFileResponse(message='File received successfully')
        except Exception as e:
            print("Error downloading the file: ", e)
            # return error message
            return worker_pb2.DownloadFileResponse(message='Error downloading the file')

    def execute(self, worker_id,ip):
        try:
            with grpc.insecure_channel(ip +':50051') as channel:
                worker_stub = worker_pb2_grpc.workerStub(channel)   # interface for the grpc client(worker)

                filename, extension = 'Algo', '.py'
                
                print(f'Executing {filename}{extension}, worker_id: {worker_id}')
                response =  worker_stub.Execute(worker_pb2.executeData(filename=filename,extension=extension,worker_id=str(worker_id)))
                print("coordinator received: " + response.message)
        except Exception as e:
            print("Error executing the file: ", e)
            return worker_pb2.executeData(message='Error executing the file')

    def send(self, target, worker_id, ip):
        """
        function :
            Defines the interface for the workers and establishes a connection with the workers
            and send them their tasks.
            Defines the interface for the divider and establishes a connection with the divider
            and send it the weights collected from the workers.
        input : target (worker or divider), worker_id, IP (provisioner IP or worker IP)
        output: response from the worker or divider
        """
        if target == "worker":
            # Establish a connection with the worker on port 50051
            with grpc.insecure_channel(ip + ":50051") as channel:
                # create an interface for the grpc client (worker)
                worker_stub = worker_pb2_grpc.workerStub(channel) 
                # send files
                response = worker_stub.download(read_file(f'{self.data_base_path}Algo.py'))
                print("coordinator received: " + response.message)
                response = worker_stub.download(read_file(f'{self.data_base_path}X_train_{worker_id}.npy'))
                print("coordinator received: " + response.message)
                response = worker_stub.download(read_file(f'{self.data_base_path}y_train_{worker_id}.npy'))
                print("coordinator received: " + response.message)
                response = worker_stub.download(read_file(f'{self.data_base_path}{worker_id}.pkl'))
                print("coordinator received: " + response.message)
        elif target == 'divider':
            # Establish a connection with the divider on port 50052
            with grpc.insecure_channel(ip + ":50053") as channel:
                # create an interface for the grpc client (divider)
                divider_stub = divider_pb2_grpc.dividerStub(channel)  
                response = divider_stub.download(read_file(f'{self.data_base_path}{worker_id}_trained.pkl'))
                print("coordinator received: " + response.message)

    def receive(self, worker_id,ip):
        try:
            with grpc.insecure_channel(ip +':50051') as channel:
                worker_stub = worker_pb2_grpc.workerStub(channel)   # interface for the grpc client(worker)

                filename, extension = f'{worker_id}_trained', '.pkl'
                filepath = self.data_base_path + filename + extension
                data = bytearray()
                for request in worker_stub.upload(
                    worker_pb2.MetaData(filename=filename, extension=extension)
                ):
                    data.extend(request.chunk_data)

                with open(filepath, mode="wb") as f:
                    f.write(data)
                print(f"Downloaded {filepath} in coordinator")
        except Exception as e:
            print("Error receiving the file: ", e)
            return worker_pb2.UploadFileResponse(chunk_data=b'')

    def start_loop(self, request, context):
        """
        function: to start sending data to workers and receive models.
        return: it return model to divider.
        """
        print("start loop")
        # then send the data to the workers
        for id in range(len(self.workers_IPs)):
            self.send("worker", id + 1, self.workers_IPs[id])

        # execute the data from the workers
        for id in range(len(self.workers_IPs)):
            # channel = grpc.insecure_channel(self.workers_IPs[id] +':50051')
            # # new_thread = threading.Thread(target=self.execute, args=(channel,id+1,self.workers_IPs[id]))
            # # new_thread.start()
            self.execute(id + 1, self.workers_IPs[id])

        # receive the data from the workers
        for id in range(len(self.workers_IPs)):
            self.receive(id + 1, self.workers_IPs[id])

        # send the data to the divider
        for id in range(len(self.workers_IPs)):
            self.send("divider", id + 1, self.divider_IP)

        return coord_pb2.LoopResponse(message="one loop is done")


## Helper functions
def get_filepath(filename, extension):
    """
    function to get the filepath of the file to be sent.
    """
    return f"{filename}{extension}"


def read_file(filepath, chunk_size=1024):
    """
    function :
        divide the file into chunks and send it as stream of small chunks using yield.
    input : filepath
    output: stream of small chunks of the file
    """
    if "coord/" in filepath:
        split_data = os.path.splitext(re.sub("coord/", "", filepath))
    else:
        split_data = os.path.splitext(filepath)
    filename, extension = split_data[0], split_data[1]
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
        print("Error reading the file: ", e)
        return coord_pb2.File(chunk_data=b'')


def serve(provisioner_IP, coordinator_stub):
    try:

        server = grpc.server(futures.ThreadPoolExecutor(1))

        coord_pb2_grpc.add_coordinatorServicer_to_server(coordinator_stub, server)

        server.add_insecure_port('[::]:50052') # open port for communication with the coordinator

        server.start()
        print("coordinator is running")

        # first get the IPs and the status of the workers from the provisioner
        workers_IPs, statuses = coordinator_stub.get_IPs_from_provisioner(provisioner_IP)
        print(IP + " , " for IP in workers_IPs)
        
        # since server.start() will not block, a sleep-loop is added to keep alive
        server.wait_for_termination()
    except Exception as e:
        print("Error in the coordinator server: ", e)
        return coord_pb2.LoopResponse(message = 'Error in the coordinator server')


            
# main function 
if __name__ == '__main__':
    provisioner_IP = '127.0.0.1'
    divider_IP = '127.0.0.1'
    coordinator = coordinator(divider_IP)
    serve(provisioner_IP, coordinator)


