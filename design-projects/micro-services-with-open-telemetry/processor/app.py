# ./processor/app.py

import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import random
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


# OpenTelemetry setup
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_COLLECTOR_URL") + "/v1/traces"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Database
engine = create_engine(os.getenv("DATABASE_URL"))
SQLAlchemyInstrumentor().instrument(
    engine=engine,
    enable_commenter=True,   # Optional: adds trace context as SQL comment
    commenter_options={      # Optional
        "db_statement": True
    }
)


app = FastAPI()
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

@app.get("/process")
def process():
	with tracer.start_as_current_span("processor.process"):
		# Randomly throw an error to demonstrate error handling	
		if random.choice([True, False]):
			raise HTTPException(status_code=500, detail="Random error occurred")
		try:
			with engine.connect() as conn:
				result = conn.execute(text("SELECT now()"))
				ts = result.scalar()
				return {"timestamp": str(ts)}
		except Exception as e:
			# will automatically create a span for the error
			raise HTTPException(status_code=500, detail=str(e))