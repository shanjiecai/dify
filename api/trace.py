import os

from flask import Flask
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_trace(app: Flask):
    trace.set_tracer_provider(TracerProvider(resource=Resource.create({SERVICE_NAME: "role"})))

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=os.environ.get("JAEGER_AGENT_HOST", "127.0.0.1"),
                agent_port=6831,
            ),
            max_queue_size=5120,
        )
    )

    FlaskInstrumentor().instrument_app(app, excluded_urls="client/.*/healthcheck")
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    # PymongoInstrumentor().instrument(capture_statement=True)
