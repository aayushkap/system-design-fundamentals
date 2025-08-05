import os, random
from fastapi import FastAPI
from requests import get
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from common.telemetry import init_tracer, init_metrics, traced

# env vars
collector_url = os.getenv("OTEL_COLLECTOR_URL", "http://collector:4318")
service_name = os.getenv("OTEL_SERVICE_NAME", "gateway")
url1 = os.getenv("PROCESSOR_1_URL")
url2 = os.getenv("PROCESSOR_2_URL")

# init telemetry
tracer, provider = init_tracer(service_name, collector_url)
meter = init_metrics(service_name, collector_url)
request_counter = meter.create_counter(
    "request_count", description="Total GET requests"
)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
RequestsInstrumentor().instrument()  # instrument outgoing HTTP


# @traced("gateway.root")
@app.get("/")
def root():
    request_counter.add(1)
    return {"message": "Welcome to the Gateway"}


@traced("gateway.proxy")
@app.get("/proxy")
def proxy():
    request_counter.add(1)
    target = random.choice([url1, url2])
    resp = get(target)
    return {"processor_response": resp.json(), "url": resp.url}
