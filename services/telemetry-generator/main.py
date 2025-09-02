import asyncio, os, json, random
from datetime import datetime, timezone
import aio_pika
from prometheus_client import start_http_server, Counter, Gauge, Histogram

RABBITMQ_URL=os.getenv("RABBITMQ_URL","amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME=os.getenv("QUEUE_NAME","telemetry.raw")
RATE=float(os.getenv("RATE_HZ","1"))
SAT_COUNT=int(os.getenv("SAT_COUNT","8"))
ORBIT=os.getenv("ORBIT","LEO")
REGIONS=os.getenv("REGIONS","RU").split(",")

# --- Prometheus metrics ---
GEN_TOTAL_BY_SAT = Counter(
    "telemetry_generated_total",
    "Messages generated per satellite",
    ["sat_id", "orbit", "region"]
)

BATTERY_HIST = Histogram(
    "telemetry_sat_battery",
    "Battery level distribution per satellite",
    ["sat_id"],
    buckets=[0,10,20,30,40,50,60,70,80,90,100]
)

LATENCY_HIST = Histogram(
    "telemetry_link_latency_ms",
    "Link latency distribution (ms) per satellite",
    ["sat_id"],
    buckets=[10,20,30,40,50,60,70,80,100,150,200]
)

PKTLOSS_HIST = Histogram(
    "telemetry_link_packet_loss_pct",
    "Packet loss distribution (%) per satellite",
    ["sat_id"],
    buckets=[0,0.1,0.5,1,2,5,10]
)

UPLINK_HIST = Histogram(
    "telemetry_link_uplink_mbps",
    "Uplink throughput distribution per satellite",
    ["sat_id"],
    buckets=[1,5,10,20,50,100]
)

DOWNLINK_HIST = Histogram(
    "telemetry_link_downlink_mbps",
    "Downlink throughput distribution per satellite",
    ["sat_id"],
    buckets=[10,50,100,150,200,300]
)

CONFIG_RATE  = Gauge("telemetry_generator_rate_hz", "Configured generation rate (Hz)")
CONFIG_SATS  = Gauge("telemetry_generator_sat_count", "Configured satellites count")

# Optional: publish loop duration
PUBLISH_DURATION = Histogram(
    "telemetry_generator_publish_seconds",
    "Time to publish a single message",
)

CONFIG_RATE.set(RATE)
CONFIG_SATS.set(SAT_COUNT)
# -----------------------------------

def generate_payload(sat_id: str, region: str) -> dict:
    base_latency = random.uniform(25, 55)  # ms
    jitter       = random.uniform(0, 15)
    pkt_loss     = max(0.0, random.gauss(0.2, 0.15))  # %
    up_mbps      = max(5, random.gauss(30, 10))
    down_mbps    = max(20, random.gauss(120, 30))
    battery      = max(5.0, min(100.0, random.gauss(75, 7)))

    latency = round(base_latency + random.uniform(-jitter, jitter), 2)

    return {
      "sat_id": sat_id,
      "orbit": ORBIT,
      "region": region,
      "ts": datetime.now(timezone.utc).isoformat(),
      "battery": round(battery, 2),
      "link": {
          "uplink_mbps": round(up_mbps, 2),
          "downlink_mbps": round(down_mbps, 2),
          "latency_ms": latency,
          "packet_loss_pct": round(pkt_loss, 2)
      }
    }

async def main():
    # Prometheus metrics endpoint on 9100
    start_http_server(9100)

    conn=await aio_pika.connect_robust(RABBITMQ_URL)
    async with conn:
        ch=await conn.channel()
        await ch.declare_queue(QUEUE_NAME,durable=True)
        while True:
            for i in range(SAT_COUNT):
                sat_id = f"SAT-{i:03d}"
                region = random.choice(REGIONS)
                msg = generate_payload(sat_id, region)

                with PUBLISH_DURATION.time():
                    await ch.default_exchange.publish(
                        aio_pika.Message(body=json.dumps(msg).encode()),
                        routing_key=QUEUE_NAME
                    )

                # --- Prometheus updates ---
                GEN_TOTAL_BY_SAT.labels(sat_id=sat_id, orbit=ORBIT, region=region).inc()
                BATTERY_HIST.labels(sat_id=sat_id).observe(msg["battery"])
                LATENCY_HIST.labels(sat_id=sat_id).observe(msg["link"]["latency_ms"])
                PKTLOSS_HIST.labels(sat_id=sat_id).observe(msg["link"]["packet_loss_pct"])
                UPLINK_HIST.labels(sat_id=sat_id).observe(msg["link"]["uplink_mbps"])
                DOWNLINK_HIST.labels(sat_id=sat_id).observe(msg["link"]["downlink_mbps"])

            await asyncio.sleep(1.0/max(RATE,0.1))

if __name__=="__main__":
    asyncio.run(main())
