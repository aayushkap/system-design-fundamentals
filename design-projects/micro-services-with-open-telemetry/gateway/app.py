# gateway/app.py

import os
import requests
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import random

# Setup OpenTelemetry
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_COLLECTOR_URL") + "/v1/traces"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
RequestsInstrumentor().instrument()    # For context propagation	


@app.get("/")
def root():
	with tracer.start_as_current_span("gateway.root"):
		return {"message": "Welcome to the Gateway"}
	
@app.get("/proxy")
def proxy():
	with tracer.start_as_current_span("gateway.proxy"):
		URL_1 = os.getenv("PROCESSOR_1_URL")
		URL_2 = os.getenv("PROCESSOR_2_URL")
		resp = requests.get(random.choice([URL_1, URL_2]))
		return {"processor_response": resp.json(), "url": resp.url}