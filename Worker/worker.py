from concurrent import futures  # indicates the num of workers (threads)
import logging
import os
import grpc
import sys

sys.path.append("../")
from protos import worker_pb2, worker_pb2_grpc

sys.path.pop()

class worker(worker_pb2_grpc.workerServicer):
    def __init__(self, port):
        self.base_path = './worker/'
        self.data_base_path = self.base_path + 'data/'
        self.port = port
        if not os.path.exists(self.data_base_path):
            os.makedirs(self.data_base_path) 

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
            return worker_pb2.DownloadFileResponse(message='File downloaded successfully')
        except Exception as e:
            print("Error downloading the file: ", e)
            # return error message
            return worker_pb2.DownloadFileResponse(message='Error downloading the file')

    def upload(self, request, context):
        chunk_size = 1024 # size of chunks used for uploading files
        
        filepath = self.data_base_path + request.filename + request.extension
        try:
            with open(filepath, mode="rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if chunk:  # or len(chunk) > 0
                        entry_response = worker_pb2.UploadFileResponse(chunk_data=chunk)
                        yield entry_response
                    else:  # The chunk was empty, which means we're at the end of the file
                        return
        except Exception as e:
            print("Error uploading the file: ", e)
            return worker_pb2.UploadFileResponse(chunk_data=b'') # No file to upload, upload an empty chunk

    def Execute(self, request, context):
        try:
            filepath = self.data_base_path + request.filename +  request.extension
            command = 'python3 '  + filepath +  " " + request.worker_id + " " + self.data_base_path
            print("executing command: ", command)
            os.system(command)
            return worker_pb2.ExecuteFileResponse(message='Executed!')
        except Exception as e:
            print("Error executing the file: ", e)
            return worker_pb2.ExecuteFileResponse(message='Error executing the file')
        
    def serve(self):
        try:
            # create a gRPC server
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
            # add the worker to the server
            worker_pb2_grpc.add_workerServicer_to_server(self, server)
            # listen on port 50051 as a server based
            server.add_insecure_port(f'[::]:{self.port}')
            # start the server
            server.start()
            print("worker is running on port: ", self.port)
            # since server.start() will not block, a sleep-loop is added to keep alive
            server.wait_for_termination()
        except Exception as e:
            print("Error in the worker server: ", e)
            return
    


if __name__ == '__main__':
    # create a directory for the worker data if does not exist
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    _worker = worker(port)
    _worker.serve()
