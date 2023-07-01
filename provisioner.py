from concurrent import futures # indicates the num of workers (threads)
import grpc
from protos import provisioner_pb2, provisioner_pb2_grpc
import multiprocessing as mp

from Worker.worker import worker

class provisioner(provisioner_pb2_grpc.provisionerServicer):
    def __init__(self, IPs, statuses, ports, ids):
        self.IPs = IPs
        self.statuses = statuses
        self.ids = ids
        self.ports = ports
        self.NumOfWorkers = 0

    # sendStatus() returns (WorkerStatus) {}
    def SendStatus(self, request, context):
        try:
            print("Received request from coordinator to send status", request)
            # print IPs and statuses
            print("IPs:", self.IPs)
            print("statuses:", self.statuses)
            return provisioner_pb2.WorkerStatus(IPs = self.IPs, statuses = self.statuses, ports = self.ports, ids = self.ids)
        except Exception as e:
            print("Error sending status: ", e)
            return provisioner_pb2.WorkerStatus(IPs = [], statuses = [], ports = [], ids = [])

    # DefineNWorkers(NumOfWorkers) returns () {}
    def DefineNWorkers(self, request, context):
        try:
            print("Number of workers is:", request.NumOfWorkers)
            self.NumOfWorkers = request.NumOfWorkers
            return provisioner_pb2.response(message = "Success receiving the number of workers")
        except Exception as e:
            print("Error receiving the number of workers: ", e)
            return provisioner_pb2.response(message = "Error receiving the number of workers")

    def create_workers(self, num_workers, IPs, ports):
        self.workers = []
        for i in range(num_workers):
            worker_instance = worker(ports[i])
            self.workers.append(worker_instance)

        print(len(self.workers))
        processes = []
        for worker_instance in self.workers:
            print("creating worker")
            process = mp.Process(target=worker_instance.serve)
            process.start()
            print(process.pid)
            processes.append(process)

        for process in processes:
            process.join()
def serve():
    try:
        # create instance of provisioner class
        IPs = []
        statuses = []
        ids = []
        ports = []
        _provisioner = provisioner(IPs , statuses, ids, ports)

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
        _provisioner.IPs = ['127.0.0.1', '127.0.0.1'] # '197.56.23.126', 
        _provisioner.statuses =[provisioner_pb2.Status.UP, provisioner_pb2.Status.UP]
        _provisioner.ports = [50151, 50152]
        _provisioner.ids = [1, 2]

        # while _provisioner.NumOfWorkers == 0:
        #     continue

        # create the workers
        # _provisioner.create_workers(_provisioner.NumOfWorkers, _provisioner.IPs, _provisioner.ports)
        # since server.start() will not block, a sleep-loop is added to keep alive
        server.wait_for_termination()
    except Exception as e:
        print("Error in the provisioner server: ", e)
        return


if __name__ == '__main__':
    serve()