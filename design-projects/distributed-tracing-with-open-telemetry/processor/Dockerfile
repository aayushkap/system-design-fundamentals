FROM python:3.11-slim
WORKDIR /app

COPY common ./common

COPY processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processor/app.py .

ENV PYTHONPATH=/app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
