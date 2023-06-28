from concurrent import futures # indicates the num of workers (threads)
import logging
import os
import grpc
import sys
sys.path.append('../')
from protos import worker_pb2, worker_pb2_grpc
sys.path.pop()

def get_filepath(filename, extension):
    return f'{filename}{extension}'

class worker(worker_pb2_grpc.workerServicer):
    
    def download(self, request_iterator, context):
        """
        function to recieve data files from the coordinator.
        """
        data = bytearray()
        for request in request_iterator:
            if request.metadata.filename and request.metadata.extension:
                filepath = get_filepath(request.metadata.filename, request.metadata.extension)
                continue
            data.extend(request.chunk_data)
        with open('worker/' + filepath, 'wb') as f:
            f.write(data)
        return worker_pb2.DownloadFileResponse(message='Success!')

    def upload(self, request, context):
        chunk_size = 1024

        filepath = f'{request.filename}{request.extension}'
        if os.path.exists('worker/'+filepath):
            with open('worker/'+filepath, mode="rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if chunk:
                        entry_response = worker_pb2.UploadFileResponse(chunk_data=chunk)
                        yield entry_response
                    else:  # The chunk was empty, which means we're at the end of the file
                        return

    def Execute(self, request, context):
        code_filepath = get_filepath(request.filename, request.extension)
        print(code_filepath)
        # print current directory
        # print(os.getcwd())
        # print('python ' + './worker/data/' + code_filepath+ " " + request.worker_id)
        # os.system('python ' + 'worker/data/' + code_filepath +  " " +request.worker_id)
        
        return worker_pb2.ExecuteFileResponse(message='Executed yaay!')
        
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    worker_pb2_grpc.add_workerServicer_to_server(worker(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()