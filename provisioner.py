from concurrent import futures # indicates the num of workers (threads)
import logging
import os
import grpc
from protos import provisioner_pb2, provisioner_pb2_grpc
import time
def get_filepath(filename, extension):
    return f'{filename}{extension}'

class provisioner(provisioner_pb2_grpc.provisionerServicer):
    def __init__(self, IPs, statuses):
        self.IPs = IPs
        self.statuses = statuses

    # sendStatus() returns (WorkerStatus) {}
    def SendStatus(self, request, context):
        print("Received request from coordinator to send status", request)
        print(" self.IPs is: ", self.IPs)
        print(" self.statuses is: ", self.statuses)
        return provisioner_pb2.WorkerStatus(IPs = self.IPs, statuses = self.statuses)

    # DefineNWorkers(NumOfWorkers) returns () {}
    def DefineNWorkers(self, request, context):
        print("Number of workers is: ", request.NumOfWorkers)
        self.n = request.NumOfWorkers
        return provisioner_pb2.response(message = "Success receiving the number of workers.")

def serve():
    # create instance of provisioner class
    IPs = []
    statuses = []
    provisioner_ = provisioner(IPs , statuses)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    provisioner_pb2_grpc.add_provisionerServicer_to_server(provisioner_, server)
    server.add_insecure_port('[::]:50054')

    server.start()
    print("provisioner is running")

    # sleep for 5 seconds to make sure that the divider is running and has sent the # of workers needed.
    
    # send the IPs and statuses to the coordinator
    provisioner_.IPs = ['127.0.0.1']
    provisioner_.statuses =[provisioner_pb2.Status.UP]


    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()