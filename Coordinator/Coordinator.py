from __future__ import print_function
from concurrent import futures  # indicates the num of (threads)
import os
import grpc
import re
import sys
import threading

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
class Coordinator(coord_pb2_grpc.coordinatorServicer):
    def __init__(self, divider_IP, provisioner_IP):
        print("Coordinator initialized successfully") 
        self.divider_IP = divider_IP  
        self.provisioner_IP = provisioner_IP
        self.server  = None
        self.base_path = '../../../Coordinator/coord/'
        self.data_base_path = self.base_path + 'data/'
    def __del__(self):
        self.stop_serving()

    def set_num_of_workers(self, num_of_workers):
        try:
            print("Coordinator: sending the num of workers to the provisioner")
            # instantiate a channel to the provisioner
            with grpc.insecure_channel(self.provisioner_IP + ":50054") as channel:
                # create an interface for the grpc client (provisioner)
                provisioner_stub = provisioner_pb2_grpc.provisionerStub(channel)

                # send the num of workers to the provisioner to create the workers, so will call function create workers from provisioner stub.
                response = provisioner_stub.DefineNWorkers(
                    provisioner_pb2.NumOfWorkers(NumOfWorkers=num_of_workers)
                )
                print("divider received: " + response.message + " from provisioner")
        except Exception as e:
            print("Error sending the num of workers to the provisioner: ", e)
            return
    def get_IPs_from_provisioner(self):
        """
        function :
            Defines the interface for the provisioner and establishes a connection with the provisioner 
            and gets the IPs of the workers and their status (Up or Down).
        input : Provisioner IP
        output: list of IPs and their status
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
            print("Error getting IPs from provisioner: ", e)
            return [], []

    def upload(self, request, context):
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
            with open(self.data_base_path + filepath, 'wb') as f:
                f.write(data)
            # return success message
            return worker_pb2.DownloadFileResponse(message='File received successfully')
        except Exception as e:
            print("Error downloading the file: ", e)
            # return error message
            return worker_pb2.DownloadFileResponse(message='Error downloading the file')

    def execute(self, worker_id, ip, port, iteration_num = 0):
        try:
            with grpc.insecure_channel(f'{ip}:{port}') as channel:
                worker_stub = worker_pb2_grpc.workerStub(channel)   # interface for the grpc client(worker)

                filename, extension = 'Algo', '.py'  
                response =  worker_stub.Execute(worker_pb2.executeData(filename=filename,extension=extension,worker_id=str(worker_id), iteration_num=str(iteration_num)))
                print("coordinator received: " + response.message  + " from worker ")
        except Exception as e:
            print("Error executing the file: ", e)
            return worker_pb2.executeData(message='Error executing the file')

    def send(self, target, worker_id, ip, port, iteration_num = 0):
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
            with grpc.insecure_channel(f'{ip}:{port}') as channel:
                # create an interface for the grpc client (worker)
                worker_stub = worker_pb2_grpc.workerStub(channel) 
                # send files
                if not self.data_status[worker_id - 1]:
                    response = worker_stub.download(read_file(f'{self.data_base_path}X_train_{worker_id}.npy'))
                    print("coordinator received: " + response.message + " from worker ")
                    response = worker_stub.download(read_file(f'{self.data_base_path}y_train_{worker_id}.npy'))
                    print("coordinator received: " + response.message + " from worker ")
                    self.data_status[worker_id - 1] = 1

                response = worker_stub.download(read_file(f'{self.data_base_path}{iteration_num}.pkl'))
                print("coordinator received: " + response.message + " from worker ")
        elif target == 'divider':
            # Establish a connection with the divider on port 50052
            with grpc.insecure_channel(ip + ":50053") as channel:
                # create an interface for the grpc client (divider)
                divider_stub = divider_pb2_grpc.dividerStub(channel)  
                response = divider_stub.download(read_file(f'{self.data_base_path}{worker_id}_{iteration_num}_trained.pkl'))
                print("coordinator received: " + response.message + " from divider ")

    def receive(self, worker_id, ip, port, iteration_num):
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
                print(f"Downloaded {filepath} in coordinator")
        except Exception as e:
            print("Error receiving the file: ", e)
            return worker_pb2.UploadFileResponse(chunk_data=b'')

    # synchronous function
    def start_loop(self, request, context):
        """
        function: to start sending data to workers and receive models.
        return: it return model to divider.
        """
        print("start loop")
        self.get_IPs_from_provisioner()
        # then send the data to the workers
        for i in range(len(self.workers_IPs)):
            self.send("worker", self.ids[i], self.workers_IPs[self.ids[i] - 1], self.ports[self.ids[i] - 1], request.iteration_num)

        threads = list()
        # execute the data from the workers
        for i in range(len(self.workers_IPs)):
            new_thread = threading.Thread(target=self.execute, args=(self.ids[i],self.workers_IPs[self.ids[i] - 1], self.ports[self.ids[i] - 1], request.iteration_num))
            threads.append(new_thread)
            new_thread.start()
            # self.execute(id+1,self.workers_IPs[id])
        
        # receive the data from the workers
        for i in range(len(self.workers_IPs)):
            threads[self.ids[i] - 1].join()
            print("thread " + str(self.ids[i]) + " is done")
            self.receive(self.ids[i],self.workers_IPs[self.ids[i] - 1], self.ports[self.ids[i] - 1], request.iteration_num)

        # send the data to the divider
        for i in range(len(self.workers_IPs)):
            self.send("divider", self.ids[i], self.divider_IP, self.ports[self.ids[i] - 1], request.iteration_num)

        return coord_pb2.LoopResponse(message="one loop is done")

    # asynchronous function
    def start_loop_async(self, request, context):
        """
        function: to start sending data to workers and receive models.
        return: it return model to divider.
        """
        print("start loop")

        # then send the data to the workers
        self.send("worker", request.worker_id , self.workers_IPs[request.worker_id - 1], self.ports[request.worker_id - 1], request.iteration_num)

        # execute the data from the workers
        self.execute(request.worker_id, self.workers_IPs[request.worker_id - 1], self.ports[request.worker_id - 1], request.iteration_num)

        print("worker  " + str(request.worker_id ) + " is done")
        self.receive(request.worker_id,self.workers_IPs[request.worker_id - 1], self.ports[request.worker_id - 1], request.iteration_num)


        self.send("divider", request.worker_id , self.divider_IP, self.ports[request.worker_id - 1], request.iteration_num)

        return coord_pb2.LoopResponse(message="one loop is done")
    
    def serve(self):
        try:
            self.server = grpc.server(futures.ThreadPoolExecutor(1))

            coord_pb2_grpc.add_coordinatorServicer_to_server(self, self.server)

            self.server.add_insecure_port('[::]:50052') # open port for communication with the coordinator

            self.server.start()
            print("coordinator is serving")
            self.set_num_of_workers(3)
            
        except Exception as e:
            print("Error in the coordinator server: ", e)
            return coord_pb2.LoopResponse(message = 'Error in the coordinator server')

    def stop_serving(self):
        if self.server:
            self.server.stop(0)
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
        print("Error reading the file: ", e)
        return coord_pb2.File(chunk_data=b'')


    

            
# main function 
if __name__ == '__main__':
    divider_IP = '127.0.0.1'
    provisioner_IP = '127.0.0.1'
    coordinator = Coordinator(divider_IP, provisioner_IP)
    coordinator.serve()


