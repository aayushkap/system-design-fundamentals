import grpc
import service_pb2
import service_pb2_grpc

def run():
    # Connect to server
    channel = grpc.insecure_channel('localhost:50051')
    stub = service_pb2_grpc.GreeterStub(channel)

    # Make a request
    response = stub.SayHello(service_pb2.HelloRequest(name="Aayush", employee_id=2))
    print("Server response:", response.message)

if __name__ == '__main__':
    run()
