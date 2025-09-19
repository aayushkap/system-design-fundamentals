import grpc
from concurrent import futures
import time

import service_pb2
import service_pb2_grpc

class ChatService(service_pb2_grpc.ChatServiceServicer):
    
    # Server streaming
    def ServerStream(self, request, context):
        for i in range(5):
            yield service_pb2.ChatReply(message=f"Server says {i} to '{request.message}'")
            time.sleep(1)
    
    # Client streaming
    def ClientStream(self, request_iterator, context):
        messages = []
        for req in request_iterator:
            messages.append(req.message)
        return service_pb2.ChatReply(message=f"Received {len(messages)} messages: {messages}")
    
    # Bidirectional streaming
    def BidirectionalStream(self, request_iterator, context):
        for req in request_iterator:
            yield service_pb2.ChatReply(message=f"Echo: {req.message}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
