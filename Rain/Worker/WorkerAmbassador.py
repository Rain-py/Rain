from concurrent import futures  # indicates the num of workers (threads)
import os
import grpc
from Rain.Protos import worker_pb2, worker_pb2_grpc
from Rain.LogService.LogService import LogService
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.Worker.Worker import Worker

class WorkerAmbassador(worker_pb2_grpc.workerServicer):
    def __init__(self, port):
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('worker/') 
        self.port = port
        self.server = None
        self.logger = LogService(f"Worker_{self.port}")
        if not os.path.exists(self.data_base_path):
            os.makedirs(self.data_base_path) 

    def __del__(self):
        self.stop_serving()

    def stop_serving(self):
        if self.server:
            self.server.stop(0)
            self.logger.log('info', f"Worker stopped serving on port: {self.port}")
    
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
            if './' in filepath:
                filepath = filepath[2:]
            with open(self.data_base_path + filepath, 'wb') as f:
                f.write(data)
            # return success message
            return worker_pb2.DownloadFileResponse(message='File downloaded successfully')
        except Exception as e:
            self.logger.log('error', f"Error downloading the file: {e}")
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
            self.logger.log('error', f"Error uploading the file: {e}")
            return worker_pb2.UploadFileResponse(chunk_data=b'') # No file to upload, upload an empty chunk

    def Execute(self, request, context):
        try:
            self.logger.log('info', f"Running the worker with id: {request.worker_id} on iteration: {request.iteration_num}")
            worker = Worker(request.worker_id, self.data_base_path, request.iteration_num)
            worker.run()
            return worker_pb2.ExecuteFileResponse(message='Executed!')
        except Exception as e:
            self.logger.log('error', f"Error executing the file: {e}")
            return worker_pb2.ExecuteFileResponse(message='Error executing the file')
        
    def serve(self):
        try:
            # create a gRPC server
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
            # add the worker to the server
            worker_pb2_grpc.add_workerServicer_to_server(self, self.server)
            # listen on port 50051 as a server based
            self.server.add_insecure_port(f'[::]:{self.port}')
            # start the server
            self.server.start()
            self.logger.log('info', f"Worker is running on port: {self.port}")
        except Exception as e:
            self.logger.log('error', f"Error in the worker server: {e}")
            return
    
