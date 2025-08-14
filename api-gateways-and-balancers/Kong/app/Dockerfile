# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV WORKERS=3


COPY main.py .

# Default server; override via SERVER env var
ENV SERVER=gunicorn

CMD ["/bin/sh", "-c", "if [ \"$SERVER\" = \"uvicorn\" ]; then \
       uvicorn main:app --host 0.0.0.0 --port 8000; \
     else \
       gunicorn -k uvicorn.workers.UvicornWorker main:app \
         --bind 0.0.0.0:8000 \
         --workers $WORKERS; \
     fi"]
