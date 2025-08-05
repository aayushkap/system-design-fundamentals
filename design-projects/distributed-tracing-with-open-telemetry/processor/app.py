import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
import random

# OpenTelemetry Tracing setup
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_COLLECTOR_URL") + "/v1/traces")) # Flush traces to the collector (default every 5 seconds)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# OpenTelemetry Metrics setup
exporter = OTLPMetricExporter(endpoint=os.getenv("OTEL_COLLECTOR_URL") + "/v1/metrics")
reader = PeriodicExportingMetricReader(exporter)
meter_provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

request_counter = meter.create_counter("request_count", description="Number of requests")
error_counter = meter.create_counter("error_count", description="Number of errors")

# Database
engine = create_engine(os.getenv("DATABASE_URL"))
SQLAlchemyInstrumentor().instrument(
    engine=engine,
    enable_commenter=True,
    commenter_options={"db_statement": True}
)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

@app.get("/process")
def process():
    with tracer.start_as_current_span("processor.process"):
        try:
            request_counter.add(1)
            if random.choice([True, False]):
                raise HTTPException(status_code=500, detail="Random error occurred")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT now()"))
                ts = result.scalar()
                return {"timestamp": str(ts)}
        except Exception as e:
            print(f"Database error: {e}")
            error_counter.add(1)
            raise HTTPException(status_code=500, detail=str(e))