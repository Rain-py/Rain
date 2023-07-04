from concurrent import futures  # indicates the num of workers (threads)
import os
import grpc
from Rain.Protos import worker_pb2, worker_pb2_grpc
from Rain.LogService.LogService import LogService
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.Worker.Worker import Worker

class WorkerAmbassador(worker_pb2_grpc.workerServicer):
    def __init__(self, port : int) -> None:
        """
        function to initialize the worker ambassador.
        Args:
            port (int): the port number to serve the worker on.
        """
        self.port = port
        self.server = None

        # create a temporary directory for the worker to store its data
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('worker/')
        # create a logger for the worker 
        self.logger = LogService(f"Worker_{self.port}")
        
        # create the directory if it does not exist
        if not os.path.exists(self.data_base_path):
            os.makedirs(self.data_base_path) 

    def __del__(self) -> None:
        """
        function to delete the worker ambassador.
        """
        try:
            self.stop_serving()
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return

    def stop_serving(self) -> None:
        """
        function to stop the worker ambassador.
        """
        try:
            if self.server:
                # stop the server
                self.server.stop(0)
                self.logger.log('info', f"Worker stopped serving on port: {self.port}")
        except Exception as e:
            self.logger.log('error', "Error stopping serving: " + str(e))
            return
    
    def download(self, request_iterator : worker_pb2.File, context : grpc.ServicerContext) -> worker_pb2.DownloadFileResponse:
        """
        function to receive data files from any service and save this data as file.
        Args:
            request_iterator (worker_pb2.File): the file to be received as stream of chunks.
            context (grpc.ServicerContext): the context of the request.
        Returns:
            worker_pb2.DownloadFileResponse: the response message.
        """
        data = bytearray()
        try:
            # receive file name and its data
            for request in request_iterator:
                if request.metadata.filename and request.metadata.extension:
                    # the request is a file metadata, save the file name and extension
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

    def upload(self, request : worker_pb2.MetaData, context : grpc.ServicerContext)-> worker_pb2.UploadFileResponse:
        """
        function to read and send data files to any service.
        Args:
            request (worker_pb2.MetaData): the file name and extention to be sent.
            context (grpc.ServicerContext): the context of the request.

        Returns:
            worker_pb2.UploadFileResponse: the chunck that will be send as response.

        Yields:
            Iterator[worker_pb2.UploadFileResponse]: the file data as stream of chunks.
        """
        chunk_size = 1024 # size of chunks used for uploading files
        
        filepath = self.data_base_path + request.filename + request.extension
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

    def Execute(self, request : worker_pb2.ExecuteData, context : grpc.ServicerContext)-> worker_pb2.ExecuteFileResponse:
        """
        function to execute worker.

        Args:
            request (worker_pb2.ExecuteData): the worker id and iteration number.
            context (grpc.ServicerContext): the context of the request.

        Returns:
            worker_pb2.ExecuteFileResponse: the response message.
        """
        try:
            self.logger.log('info', f"Running the worker with id: {request.worker_id} on iteration: {request.iteration_num}")
            # create a worker and run it
            worker = Worker(request.worker_id, self.data_base_path, request.iteration_num)
            worker.run()
            # return success message
            return worker_pb2.ExecuteFileResponse(message='Executed!')
        except Exception as e:
            self.logger.log('error', f"Error executing the file: {e}")
            # return error message
            return worker_pb2.ExecuteFileResponse(message='Error executing the file')

    def StopWorker(self, request, context):
        response = worker_pb2.StopSignal(message='Worker stopped!')
        return response
         
    def serve(self) -> None:
        """
        function to start the worker ambassador as a server to listen on the given port.
        """
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
    
