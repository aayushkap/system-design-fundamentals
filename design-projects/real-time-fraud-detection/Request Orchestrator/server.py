import grpc
from concurrent import futures
import time
import service_pb2
import service_pb2_grpc
import random

class GeneratorServicer(service_pb2_grpc.GeneratorServicer):
    def Generate(self, request, context):
        return service_pb2.GenerateResponse(
            message="Hello from Python",
            value=random.randint(1, 100)
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    service_pb2_grpc.add_GeneratorServicer_to_server(GeneratorServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Python gRPC server running on 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
