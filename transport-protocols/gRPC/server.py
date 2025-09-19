import grpc
from concurrent import futures
import time

import service_pb2
import service_pb2_grpc

class Greeter(service_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        name = request.name or None
        eid = request.employee_id or None
        return service_pb2.HelloReply(message=f"Hello, {name} ({eid})!")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('[::]:50051')  # listen on port 50051
    
    server.start() # Starts gRPC server in background thread
    
    print("Server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
