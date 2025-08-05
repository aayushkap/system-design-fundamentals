import os
import requests
from fastapi import FastAPI
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
import random

# Setup OpenTelemetry Tracing
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_COLLECTOR_URL") + "/v1/traces"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Setup OpenTelemetry Metrics
exporter = OTLPMetricExporter(endpoint=os.getenv("OTEL_COLLECTOR_URL") + "/v1/metrics")
reader = PeriodicExportingMetricReader(exporter)
meter_provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)
request_counter = meter.create_counter("request_count", description="Number of requests")

app = FastAPI()
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
RequestsInstrumentor().instrument() # For context propagation (TraceID, SpanID) in outgoing requests

@app.get("/")
def root():
    with tracer.start_as_current_span("gateway.root"):
        request_counter.add(1)
        return {"message": "Welcome to the Gateway"}

@app.get("/proxy")
def proxy():
    with tracer.start_as_current_span("gateway.proxy"):
        request_counter.add(1)
        URL_1 = os.getenv("PROCESSOR_1_URL")
        URL_2 = os.getenv("PROCESSOR_2_URL")
        resp = requests.get(random.choice([URL_1, URL_2]))
        return {"processor_response": resp.json(), "url": resp.url}