import os, random
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from common.telemetry import init_tracer, init_metrics, traced

# env
collector_url = os.getenv("OTEL_COLLECTOR_URL", "http://collector:4318")
service_name = os.getenv("OTEL_SERVICE_NAME", "processor")
db_url = os.getenv("DATABASE_URL")

# init telemetry
tracer, provider = init_tracer(service_name, collector_url)
meter = init_metrics(service_name, collector_url)
request_counter = meter.create_counter(
    "request_count", description="Total /process calls"
)
error_counter = meter.create_counter("error_count", description="Errors in /process")

# init database
engine = create_engine(db_url)
SQLAlchemyInstrumentor().instrument(
    engine=engine, enable_commenter=True, commenter_options={"db_statement": True}
)

# init FastAPI
app = FastAPI()
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)


@traced("processor.process")
@app.get("/process")
def process():
    request_counter.add(1)
    if random.choice([True, False]):
        error_counter.add(1)
        raise HTTPException(status_code=500, detail="Random error occurred")
    with engine.connect() as conn:
        ts = conn.execute(text("SELECT now()")).scalar()
    return {"timestamp": str(ts)}
