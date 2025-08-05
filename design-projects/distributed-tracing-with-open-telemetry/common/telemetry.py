import os
from functools import wraps
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

def init_tracer(service_name: str, collector_url: str):
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=f"{collector_url}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter)) # Batch processing will flush logs to collector (by default every 5 seconds)
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(service_name)
    return tracer, provider

def init_metrics(service_name: str, collector_url: str):
    exporter = OTLPMetricExporter(endpoint=f"{collector_url}/v1/metrics")
    reader = PeriodicExportingMetricReader(exporter) # We export (not scrape) metrics periodically (by default every 60 seconds)
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    return metrics.get_meter(service_name)

def traced(span_name: str):
    """
    Decorator to wrap a function call in a span named `span_name`.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(fn.__module__)
            with tracer.start_as_current_span(span_name):
                return fn(*args, **kwargs)
        return wrapper
    return decorator
