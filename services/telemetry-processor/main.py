import asyncio, os, json, time
import aio_pika, asyncpg
from prometheus_client import start_http_server, Counter, Histogram, Gauge

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME   = os.getenv("QUEUE_NAME", "telemetry.raw")
PG_DSN       = os.getenv("PG_DSN", "postgresql://telemetry:example@postgres:5432/telemetry")

ingested_total = Counter("telemetry_ingested_total", "Total msgs")
ingested_by_sat_total = Counter(
    "telemetry_ingested_by_sat_total",
    "Total msgs by satellite",
    ["sat_id", "region"],
)
processing_latency_s = Histogram(
    "telemetry_processing_latency_seconds",
    "End-to-end processing latency seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]
)
db_errors_total = Counter("telemetry_db_errors_total", "DB errors total")
ingest_lag_s   = Histogram("telemetry_ingest_lag_seconds", "Ingest lag seconds")
db_write_s     = Histogram("telemetry_db_write_seconds", "DB write seconds")

sat_battery     = Gauge("sat_battery_percent", "Battery %", ["sat_id","orbit","region"])
sat_uplink_mbps = Gauge("sat_link_uplink_mbps", "Uplink Mbps", ["sat_id","orbit","region"])
sat_down_mbps   = Gauge("sat_link_downlink_mbps", "Downlink Mbps", ["sat_id","orbit","region"])
sat_latency_ms  = Gauge("sat_link_latency_ms", "RTT latency ms", ["sat_id","orbit","region"])
sat_loss_pct    = Gauge("sat_link_packet_loss_pct", "Packet loss %", ["sat_id","orbit","region"])

async def main():
    pool = await asyncpg.create_pool(PG_DSN)
    async with pool.acquire() as c:
        await c.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
          id SERIAL PRIMARY KEY,
          ts timestamptz NOT NULL DEFAULT now(),
          data jsonb NOT NULL
        );
        CREATE INDEX IF NOT EXISTS telemetry_gin ON telemetry USING GIN (data);
        """)

    conn = await aio_pika.connect_robust(RABBITMQ_URL)
    ch = await conn.channel()
    q = await ch.declare_queue(QUEUE_NAME, durable=True)

    start_http_server(8000)

    async with q.iterator() as it:
        async for msg in it:
            loop_start = time.perf_counter()
            payload = json.loads(msg.body)
            # compute ingest lag from ISO timestamp if present
            try:
                from datetime import datetime
                ts = payload.get("ts")
                if isinstance(ts, str):
                    ts_clean = ts.replace("Z", "")
                    lag = max(0.0, time.time() - datetime.fromisoformat(ts_clean).timestamp())
                else:
                    lag = 0.0
            except Exception:
                lag = 0.0
            ingest_lag_s.observe(lag)

            try:
                async with pool.acquire() as c:
                    await c.execute("INSERT INTO telemetry(data) VALUES($1::jsonb)", json.dumps(payload))
            except Exception:
                db_errors_total.inc()
                raise
            finally:
                db_write_s.observe(time.perf_counter() - loop_start)

            labels = dict(
                sat_id=payload.get("sat_id","unknown"),
                orbit=payload.get("orbit","unknown"),
                region=payload.get("region","unknown"),
            )
            sat_battery.labels(**labels).set(float(payload.get("battery", 0)))
            link = payload.get("link", {})
            if isinstance(link, dict):
                if "uplink_mbps" in link:  sat_uplink_mbps.labels(**labels).set(float(link["uplink_mbps"]))
                if "downlink_mbps" in link: sat_down_mbps.labels(**labels).set(float(link["downlink_mbps"]))
                if "latency_ms" in link:   sat_latency_ms.labels(**labels).set(float(link["latency_ms"]))
                if "packet_loss_pct" in link: sat_loss_pct.labels(**labels).set(float(link["packet_loss_pct"]))

            ingested_total.inc()
            ingested_by_sat_total.labels(sat_id=labels["sat_id"], region=labels["region"]).inc()
            processing_latency_s.observe(time.perf_counter() - loop_start)
            await msg.ack()

if __name__ == "__main__":
    asyncio.run(main())
