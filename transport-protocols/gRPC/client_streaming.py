import grpc
import service_pb2
import service_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = service_pb2_grpc.ChatServiceStub(channel)

# Server streaming
print("Server streaming example:")
for reply in stub.ServerStream(service_pb2.ChatRequest(message="Hello Server")):
    print(reply.message)

# Client streaming
print("\nClient streaming example:")
def generate_messages():
    for i in range(3):
        yield service_pb2.ChatRequest(message=f"Message {i}")
response = stub.ClientStream(generate_messages())
print(response.message)

# Bidirectional streaming
def bidirectional_messages():
    for i in range(3):
        yield service_pb2.ChatRequest(message=f"BiMessage {i}")
for reply in stub.BidirectionalStream(bidirectional_messages()):
    print(reply.message)
