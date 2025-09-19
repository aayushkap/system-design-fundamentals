To generate python code from Proto file:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. service.proto
```

Run server with:
```bash
python server.py
```

Run client with:
```bash
python client.py
```

