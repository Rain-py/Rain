from concurrent import futures # indicates the num of workers (threads)
import grpc
from protos import provisioner_pb2, provisioner_pb2_grpc

class provisioner(provisioner_pb2_grpc.provisionerServicer):
    def __init__(self, IPs, statuses):
        self.IPs = IPs
        self.statuses = statuses
        self.NumOfWorkers = 0

    # sendStatus() returns (WorkerStatus) {}
    def SendStatus(self, request, context):
        try:
            print("Received request from coordinator to send status", request)
            # print IPs and statuses
            print("IPs: ", self.IPs)
            print("statuses: ", self.statuses)
            return provisioner_pb2.WorkerStatus(IPs = self.IPs, statuses = self.statuses)
        except Exception as e:
            print("Error sending status: ", e)
            return provisioner_pb2.WorkerStatus(IPs = [], statuses = [])

    # DefineNWorkers(NumOfWorkers) returns () {}
    def DefineNWorkers(self, request, context):
        try:
            print("Number of workers is: ", request.NumOfWorkers)
            self.NumOfWorkers = request.NumOfWorkers
            return provisioner_pb2.response(message = "Success receiving the number of workers")
        except Exception as e:
            print("Error receiving the number of workers: ", e)
            return provisioner_pb2.response(message = "Error receiving the number of workers")

def serve():
    try:
        # create instance of provisioner class
        IPs = []
        statuses = []
        _provisioner = provisioner(IPs , statuses)

        # create a gRPC server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        # add the provisioner to the server
        provisioner_pb2_grpc.add_provisionerServicer_to_server(_provisioner, server)
        # listen on port 50054
        server.add_insecure_port('[::]:50054')
        # start the server
        server.start()
        print("provisioner is running")
        
        # send the IPs and statuses to the coordinator
        _provisioner.IPs = ['127.0.0.1']
        _provisioner.statuses =[provisioner_pb2.Status.UP]

        # since server.start() will not block, a sleep-loop is added to keep alive
        server.wait_for_termination()
    except Exception as e:
        print("Error in the provisioner server: ", e)
        return


if __name__ == '__main__':
    serve()