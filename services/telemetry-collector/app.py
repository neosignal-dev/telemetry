import asyncio, os, json, time
from fastapi import FastAPI, Request
import aio_pika
from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

RABBITMQ_URL = os.getenv("RABBITMQ_URL","amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME   = os.getenv("QUEUE_NAME","telemetry.raw")
EXCHANGE     = "telemetry"

# --- Prometheus ---
ingest_total = Counter("telemetry_http_ingest_total", "Total HTTP ingests")
ingest_bytes = Counter("telemetry_http_ingest_bytes", "Total payload bytes")
last_ingest_ts = Gauge("telemetry_http_last_ingest_unixtime", "Last ingest unixtime")
collected_total = Counter(
    "telemetry_collected_total",
    "Accepted telemetry events",
    ["sat_id", "region"],
)

app = FastAPI()

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers={"/metrics"},
)
instrumentator.instrument(app).expose(app, endpoint="/metrics")

app.state.conn = None
app.state.ch = None
app.state.ex = None

async def connect_rmq_with_retry(url, attempts=60, delay=1):
    last=None
    for _ in range(attempts):
        try:
            return await aio_pika.connect_robust(url)
        except Exception as e:
            last=e
            await asyncio.sleep(delay)
    raise last

@app.on_event("startup")
async def startup():
    app.state.conn = await connect_rmq_with_retry(RABBITMQ_URL)
    app.state.ch   = await app.state.conn.channel()
    app.state.ex   = await app.state.ch.declare_exchange(EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)
    q = await app.state.ch.declare_queue(QUEUE_NAME, durable=True)
    await q.bind(app.state.ex, routing_key="raw")

@app.on_event("shutdown")
async def shutdown():
    if app.state.conn:
        await app.state.conn.close()

@app.post("/ingest")
async def ingest(payload: dict, request: Request):
    body = json.dumps(payload).encode()
    ingest_total.inc()
    ingest_bytes.inc(len(body))
    last_ingest_ts.set(time.time())
    # label-aware domain counter
    sat_id = str(payload.get("sat_id", "unknown"))
    region = str(payload.get("region", "unknown"))
    collected_total.labels(sat_id=sat_id, region=region).inc()
    await app.state.ex.publish(
        aio_pika.Message(body=body),
        routing_key="raw"
    )
    return {"queued": True}
