from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(title="FastAPI Terraform Demo")

@app.get("/")
def read_root():
    return {
        "message": "Hello from FastAPI!",
        "provisioned_by": "Terraform in Docker Compose",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "fastapi-demo"}

@app.get("/info")
def info():
    return {
        "app": "FastAPI Demo",
        "version": "1.0.0",
        "description": "Provisioned with Terraform running in Docker Compose"
    }
